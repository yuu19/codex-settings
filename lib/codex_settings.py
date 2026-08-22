from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tarfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

if sys.version_info < (3, 11):
    raise SystemExit("codex-settings requires Python 3.11 or newer")

import tomllib


SCHEMA_VERSION = 1
STATE_FILE_NAME = "state.json"
SIMPLE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")
TABLE_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
ARRAY_TABLE_RE = re.compile(r"^\s*\[\[")
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=.*$")
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class SettingsError(RuntimeError):
    """An expected validation or synchronization error."""


@dataclass(frozen=True)
class TemplateAssignment:
    path: tuple[str, ...]
    line: str
    value: Any


@dataclass(frozen=True)
class SkillSpec:
    name: str
    relative_path: Path
    capability: str


@dataclass(frozen=True)
class PackageSpec:
    name: str
    version: str
    capability: str


@dataclass(frozen=True)
class ConfigMigration:
    path: tuple[str, ...]
    expected_value: Any


@dataclass(frozen=True)
class Manifest:
    minimum_codex_version: str
    capabilities: dict[str, dict[str, Any]]
    skills: tuple[SkillSpec, ...]
    packages: tuple[PackageSpec, ...]
    config_migrations: tuple[ConfigMigration, ...]

    @property
    def default_capabilities(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, definition in self.capabilities.items()
            if bool(definition.get("default"))
        )


@dataclass(frozen=True)
class TargetLayout:
    home: Path
    codex_home: Path
    state_dir: Path

    @property
    def config_path(self) -> Path:
        return self.codex_home / "config.toml"

    @property
    def skills_dir(self) -> Path:
        return self.home / ".agents" / "skills"

    @property
    def legacy_skills_dir(self) -> Path:
        return self.codex_home / "skills"

    @property
    def state_path(self) -> Path:
        return self.state_dir / STATE_FILE_NAME

    @property
    def backups_dir(self) -> Path:
        return self.state_dir / "backups"

    @classmethod
    def for_current_user(cls) -> "TargetLayout":
        home = Path.home()
        codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
        state_root = Path(
            os.environ.get("XDG_STATE_HOME", home / ".local" / "state")
        )
        return cls(
            home=home,
            codex_home=codex_home,
            state_dir=state_root / "codex-settings",
        )


@dataclass(frozen=True)
class ConfigChange:
    path: tuple[str, ...]
    before: Any
    after: Any

    @property
    def action(self) -> str:
        if self.before is _MISSING:
            return "add"
        if self.after is _MISSING:
            return "remove"
        return "update"


@dataclass(frozen=True)
class SkillAction:
    action: str
    name: str
    destination: Path
    source: Path | None = None
    source_hash: str | None = None


@dataclass(frozen=True)
class SyncPlan:
    candidate_config: str
    config_changes: tuple[ConfigChange, ...]
    skill_actions: tuple[SkillAction, ...]
    legacy_removals: tuple[SkillAction, ...]
    next_state: dict[str, Any]
    previous_state: dict[str, Any] | None
    state_changed: bool

    @property
    def has_changes(self) -> bool:
        return bool(
            self.config_changes
            or self.skill_actions
            or self.legacy_removals
            or self.state_changed
        )


_MISSING = object()


def _path_key(path: Sequence[str]) -> str:
    return ".".join(path)


def _split_path(value: str) -> tuple[str, ...]:
    parts = tuple(value.split("."))
    if not parts or any(not SIMPLE_COMPONENT_RE.fullmatch(part) for part in parts):
        raise SettingsError(f"invalid managed config path in state: {value!r}")
    return parts


def _ensure_within(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
        raise SettingsError(f"{label} escapes the repository: {path}")
    return resolved_path


def _flatten(value: Any, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], Any]:
    if isinstance(value, dict):
        result: dict[tuple[str, ...], Any] = {}
        for key, child in value.items():
            result.update(_flatten(child, prefix + (str(key),)))
        return result
    return {prefix: value}


def _parse_simple_section(raw: str) -> tuple[str, ...] | None:
    parts = tuple(part.strip() for part in raw.split("."))
    if not parts or any(not SIMPLE_COMPONENT_RE.fullmatch(part) for part in parts):
        return None
    return parts


def parse_template_assignments(text: str, label: str) -> tuple[TemplateAssignment, ...]:
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"invalid TOML in {label}: {error}") from error

    assignments: list[TemplateAssignment] = []
    current_section: tuple[str, ...] | None = ()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ARRAY_TABLE_RE.match(line):
            raise SettingsError(
                f"{label}:{line_number}: array tables are not supported in managed config"
            )
        table_match = TABLE_RE.match(line)
        if table_match:
            current_section = _parse_simple_section(table_match.group(1))
            if current_section is None:
                raise SettingsError(
                    f"{label}:{line_number}: managed table names must use simple components"
                )
            continue
        assignment_match = ASSIGNMENT_RE.match(line)
        if not assignment_match:
            continue
        if current_section is None:
            raise SettingsError(f"{label}:{line_number}: unsupported managed section")
        key = assignment_match.group(1)
        path = current_section + (key,)
        value: Any = parsed
        try:
            for component in path:
                value = value[component]
        except (KeyError, TypeError) as error:
            raise SettingsError(
                f"{label}:{line_number}: could not resolve {_path_key(path)}"
            ) from error
        assignments.append(TemplateAssignment(path=path, line=line.strip(), value=value))

    parsed_paths = set(_flatten(parsed))
    assignment_paths = {assignment.path for assignment in assignments}
    if parsed_paths != assignment_paths:
        missing = sorted(_path_key(path) for path in parsed_paths - assignment_paths)
        raise SettingsError(
            f"{label}: every managed value must be a single-line assignment"
            + (f"; missing: {', '.join(missing)}" if missing else "")
        )
    if len(assignment_paths) != len(assignments):
        raise SettingsError(f"{label}: duplicate managed assignment")
    return tuple(assignments)


def _read_skill_name(skill_file: Path) -> str:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError as error:
        raise SettingsError(f"could not read {skill_file}: {error}") from error
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SettingsError(f"{skill_file}: missing YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as error:
        raise SettingsError(f"{skill_file}: unterminated YAML frontmatter") from error
    for line in lines[1:end]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    raise SettingsError(f"{skill_file}: frontmatter name is missing")


def directory_hash(path: Path) -> str:
    if path.is_symlink():
        raise SettingsError(f"skill directory may not be a symlink: {path}")
    if not path.is_dir():
        raise SettingsError(f"skill directory does not exist: {path}")
    digest = hashlib.sha256()
    files: list[Path] = []
    for candidate in path.rglob("*"):
        relative = candidate.relative_to(path)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        if candidate.is_symlink():
            raise SettingsError(f"skill directories may not contain symlinks: {candidate}")
        if candidate.is_file():
            files.append(candidate)
    for candidate in sorted(files, key=lambda item: item.relative_to(path).as_posix()):
        relative = candidate.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = candidate.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        executable = bool(candidate.stat().st_mode & stat.S_IXUSR)
        digest.update(b"x" if executable else b"-")
    return digest.hexdigest()


def git_archive_directory_hash(
    repo_root: Path, revision: str, relative_path: Path
) -> str | None:
    try:
        result = subprocess.run(
            ["git", "archive", "--format=tar", revision, relative_path.as_posix()],
            cwd=repo_root,
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SettingsError(f"failed to inspect Git history: {error}") from error
    if result.returncode != 0:
        return None

    prefix = relative_path.as_posix().rstrip("/") + "/"
    files: list[tuple[str, bytes, bool]] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            for member in archive.getmembers():
                if member.issym() or member.islnk():
                    return None
                if not member.isfile() or not member.name.startswith(prefix):
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    return None
                files.append(
                    (
                        member.name[len(prefix) :],
                        extracted.read(),
                        bool(member.mode & stat.S_IXUSR),
                    )
                )
    except tarfile.TarError as error:
        raise SettingsError(f"could not inspect archived skill: {error}") from error

    digest = hashlib.sha256()
    for relative, content, executable in sorted(files):
        encoded_relative = relative.encode("utf-8")
        digest.update(len(encoded_relative).to_bytes(4, "big"))
        digest.update(encoded_relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        digest.update(b"x" if executable else b"-")
    return digest.hexdigest()


def load_manifest(repo_root: Path) -> Manifest:
    manifest_path = repo_root / "manifest.toml"
    try:
        raw = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SettingsError(f"manifest not found: {manifest_path}") from error
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"invalid manifest TOML: {error}") from error

    if raw.get("schema_version") != SCHEMA_VERSION:
        raise SettingsError(
            f"unsupported manifest schema_version: {raw.get('schema_version')!r}"
        )
    minimum = raw.get("minimum_codex_version")
    if not isinstance(minimum, str) or VERSION_RE.fullmatch(minimum) is None:
        raise SettingsError("minimum_codex_version must be an x.y.z string")

    capabilities = raw.get("capabilities")
    if not isinstance(capabilities, dict) or "core" not in capabilities:
        raise SettingsError("manifest must define the core capability")
    if not bool(capabilities["core"].get("default")):
        raise SettingsError("the core capability must be enabled by default")
    for name, definition in capabilities.items():
        if not SIMPLE_COMPONENT_RE.fullmatch(name) or not isinstance(definition, dict):
            raise SettingsError(f"invalid capability: {name!r}")
        files = definition.get("config_files")
        if not isinstance(files, list) or not files or not all(
            isinstance(item, str) for item in files
        ):
            raise SettingsError(f"capability {name} must list config_files")
        for relative in files:
            config_path = _ensure_within(repo_root, repo_root / relative, "config file")
            if not config_path.is_file():
                raise SettingsError(f"managed config file is missing: {relative}")
            parse_template_assignments(
                config_path.read_text(encoding="utf-8"), relative
            )

    skills: list[SkillSpec] = []
    seen_names: set[str] = set()
    for item in raw.get("skills", []):
        if not isinstance(item, dict):
            raise SettingsError("each skill entry must be a table")
        name = item.get("name")
        relative = item.get("path")
        capability = item.get("capability")
        if not all(isinstance(value, str) for value in (name, relative, capability)):
            raise SettingsError("skill name, path, and capability must be strings")
        if name in seen_names:
            raise SettingsError(f"duplicate skill in manifest: {name}")
        if capability not in capabilities:
            raise SettingsError(f"skill {name} has unknown capability: {capability}")
        if not SIMPLE_COMPONENT_RE.fullmatch(name):
            raise SettingsError(f"invalid skill name: {name}")
        skill_path = _ensure_within(repo_root, repo_root / relative, "skill path")
        skill_file = skill_path / "SKILL.md"
        if _read_skill_name(skill_file) != name:
            raise SettingsError(f"skill name does not match directory for {name}")
        directory_hash(skill_path)
        seen_names.add(name)
        skills.append(
            SkillSpec(name=name, relative_path=Path(relative), capability=capability)
        )

    packages: list[PackageSpec] = []
    for item in raw.get("packages", []):
        if not isinstance(item, dict):
            raise SettingsError("each package entry must be a table")
        name = item.get("name")
        version = item.get("version")
        capability = item.get("capability")
        if not all(isinstance(value, str) for value in (name, version, capability)):
            raise SettingsError("package name, version, and capability must be strings")
        if capability not in capabilities:
            raise SettingsError(f"package {name} has unknown capability: {capability}")
        if VERSION_RE.fullmatch(version) is None:
            raise SettingsError(f"package {name} must use an exact x.y.z version")
        config_text = "\n".join(
            (repo_root / relative).read_text(encoding="utf-8")
            for relative in capabilities[capability]["config_files"]
        )
        if f"{name}@{version}" not in config_text:
            raise SettingsError(
                f"package pin {name}@{version} is not present in {capability} config"
            )
        packages.append(PackageSpec(name=name, version=version, capability=capability))

    config_migrations: list[ConfigMigration] = []
    migration_paths: set[tuple[str, ...]] = set()
    for item in raw.get("config_migrations", []):
        if not isinstance(item, dict):
            raise SettingsError("each config migration must be a table")
        path_value = item.get("path")
        if not isinstance(path_value, str) or "expected_value" not in item:
            raise SettingsError("config migration requires path and expected_value")
        path = _split_path(path_value)
        if path in migration_paths:
            raise SettingsError(f"duplicate config migration: {path_value}")
        migration_paths.add(path)
        config_migrations.append(
            ConfigMigration(path=path, expected_value=item["expected_value"])
        )

    if not skills:
        raise SettingsError("manifest must contain at least one skill")
    return Manifest(
        minimum_codex_version=minimum,
        capabilities=capabilities,
        skills=tuple(skills),
        packages=tuple(packages),
        config_migrations=tuple(config_migrations),
    )


def _scan_document(lines: Sequence[str]) -> tuple[dict[tuple[str, ...], int], dict[tuple[str, ...], int]]:
    assignments: dict[tuple[str, ...], int] = {}
    sections: dict[tuple[str, ...], int] = {}
    current_section: tuple[str, ...] | None = ()
    for index, line in enumerate(lines):
        if ARRAY_TABLE_RE.match(line):
            current_section = None
            continue
        table_match = TABLE_RE.match(line)
        if table_match:
            current_section = _parse_simple_section(table_match.group(1))
            if current_section is not None:
                sections[current_section] = index
            continue
        assignment_match = ASSIGNMENT_RE.match(line)
        if assignment_match and current_section is not None:
            assignments[current_section + (assignment_match.group(1),)] = index
    return assignments, sections


def _remove_empty_section(lines: list[str], section: tuple[str, ...]) -> list[str]:
    _, sections = _scan_document(lines)
    header_index = sections.get(section)
    if header_index is None:
        return lines
    end = len(lines)
    for index in range(header_index + 1, len(lines)):
        if TABLE_RE.match(lines[index]) or ARRAY_TABLE_RE.match(lines[index]):
            end = index
            break
    body = lines[header_index + 1 : end]
    if any(line.strip() and not line.lstrip().startswith("#") for line in body):
        return lines
    del lines[header_index:end]
    while header_index > 0 and header_index <= len(lines) and not lines[header_index - 1].strip():
        del lines[header_index - 1]
        header_index -= 1
    return lines


def merge_config(
    current_text: str,
    desired: Sequence[TemplateAssignment],
    previous_managed: dict[tuple[str, ...], Any],
    migrations: Sequence[ConfigMigration] = (),
) -> tuple[str, tuple[ConfigChange, ...]]:
    try:
        current_data = tomllib.loads(current_text) if current_text.strip() else {}
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"existing Codex config is invalid TOML: {error}") from error
    current_flat = _flatten(current_data)
    desired_by_path = {assignment.path: assignment for assignment in desired}
    desired_paths = set(desired_by_path)
    previous_paths = set(previous_managed)
    migration_paths: set[tuple[str, ...]] = set()
    for migration in migrations:
        current_value = current_flat.get(migration.path, _MISSING)
        if current_value is _MISSING:
            continue
        if current_value != migration.expected_value:
            raise SettingsError(
                f"config migration conflict at {_path_key(migration.path)}: "
                "the local value does not match the known legacy value"
            )
        migration_paths.add(migration.path)
    removed_paths = (previous_paths - desired_paths) | migration_paths

    obsolete_mcp_sections = {
        path[:2]
        for path in removed_paths
        if len(path) >= 3
        and path[0] == "mcp_servers"
        and not any(candidate[:2] == path[:2] for candidate in desired_paths)
    }
    for section in sorted(obsolete_mcp_sections):
        local_descendants = {
            path
            for path in current_flat
            if path[: len(section)] == section and path not in previous_paths
        }
        if local_descendants:
            rendered = ", ".join(sorted(_path_key(path) for path in local_descendants))
            raise SettingsError(
                f"cannot remove {_path_key(section)} because it contains local settings: {rendered}"
            )

    changes: list[ConfigChange] = []
    for path in sorted(desired_paths | removed_paths):
        before = current_flat.get(path, _MISSING)
        after = desired_by_path[path].value if path in desired_by_path else _MISSING
        if before != after:
            changes.append(ConfigChange(path=path, before=before, after=after))

    lines = current_text.splitlines()
    assignment_indices, _ = _scan_document(lines)
    for path in sorted(removed_paths, key=lambda value: assignment_indices.get(value, -1), reverse=True):
        index = assignment_indices.get(path)
        if index is not None:
            del lines[index]
            assignment_indices, _ = _scan_document(lines)

    for section in sorted(obsolete_mcp_sections, key=len, reverse=True):
        lines = _remove_empty_section(lines, section)

    assignment_indices, _ = _scan_document(lines)
    for assignment in desired:
        index = assignment_indices.get(assignment.path)
        if index is not None:
            lines[index] = assignment.line

    assignment_indices, sections = _scan_document(lines)
    missing_by_section: dict[tuple[str, ...], list[TemplateAssignment]] = {}
    for assignment in desired:
        if assignment.path not in assignment_indices:
            missing_by_section.setdefault(assignment.path[:-1], []).append(assignment)

    for section, missing in missing_by_section.items():
        assignment_indices, sections = _scan_document(lines)
        if section == ():
            insert_at = next(
                (
                    index
                    for index, line in enumerate(lines)
                    if TABLE_RE.match(line) or ARRAY_TABLE_RE.match(line)
                ),
                len(lines),
            )
            payload = [assignment.line for assignment in missing]
            if insert_at > 0 and lines[insert_at - 1].strip():
                payload.append("")
            lines[insert_at:insert_at] = payload
            continue

        header_index = sections.get(section)
        payload = [assignment.line for assignment in missing]
        if header_index is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(f"[{_path_key(section)}]")
            lines.extend(payload)
            continue

        insert_at = len(lines)
        for index in range(header_index + 1, len(lines)):
            if TABLE_RE.match(lines[index]) or ARRAY_TABLE_RE.match(lines[index]):
                insert_at = index
                break
        if insert_at > header_index + 1 and lines[insert_at - 1].strip():
            payload.append("")
        lines[insert_at:insert_at] = payload

    candidate = "\n".join(lines).rstrip() + "\n"
    try:
        candidate_data = tomllib.loads(candidate)
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"generated Codex config is invalid TOML: {error}") from error
    candidate_flat = _flatten(candidate_data)
    for path, assignment in desired_by_path.items():
        if candidate_flat.get(path, _MISSING) != assignment.value:
            raise SettingsError(f"generated config did not set {_path_key(path)}")
    for path in removed_paths:
        if path in candidate_flat:
            raise SettingsError(f"generated config did not remove {_path_key(path)}")
    return candidate, tuple(changes)


def _load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SettingsError(f"could not read state {path}: {error}") from error
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION:
        raise SettingsError(f"unsupported or invalid state file: {path}")
    if not isinstance(state.get("managed_config", {}), dict):
        raise SettingsError(f"invalid managed_config in state: {path}")
    if not isinstance(state.get("managed_skills", {}), dict):
        raise SettingsError(f"invalid managed_skills in state: {path}")
    return state


def _semantic_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    return {key: value for key, value in state.items() if key != "updated_at"}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def atomic_write_bytes(path: Path, content: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SettingsError(f"failed to run {' '.join(command)}: {error}") from error


def _parse_version(text: str, label: str) -> tuple[int, int, int]:
    match = VERSION_RE.search(text)
    if match is None:
        raise SettingsError(f"could not parse {label} version from: {text.strip()!r}")
    return tuple(int(part) for part in match.groups())


class SettingsManager:
    def __init__(
        self,
        repo_root: Path,
        *,
        layout: TargetLayout | None = None,
        codex_bin: str | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.layout = layout or TargetLayout.for_current_user()
        self.manifest = load_manifest(self.repo_root)
        self.codex_bin = codex_bin or shutil.which("codex") or ""

    def _codex_version(self) -> str:
        if not self.codex_bin:
            raise SettingsError("Codex CLI is required but was not found on PATH")
        result = _run([self.codex_bin, "--version"], timeout=15)
        output = (result.stdout or result.stderr).strip()
        if result.returncode != 0:
            raise SettingsError(f"could not determine Codex version: {output}")
        installed = _parse_version(output, "Codex")
        minimum = _parse_version(self.manifest.minimum_codex_version, "minimum Codex")
        if installed < minimum:
            raise SettingsError(
                f"Codex {self.manifest.minimum_codex_version} or newer is required; found {output}"
            )
        return ".".join(str(part) for part in installed)

    def _source_revision(self, allow_dirty: bool) -> str:
        revision = _run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, timeout=15)
        if revision.returncode != 0:
            raise SettingsError("codex-settings must be run from a Git checkout")
        status = _run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=self.repo_root,
            timeout=15,
        )
        if status.returncode != 0:
            raise SettingsError(f"could not inspect Git status: {status.stderr.strip()}")
        dirty = bool(status.stdout.strip())
        if dirty and not allow_dirty:
            raise SettingsError(
                "the codex-settings checkout is dirty; commit the source or use --allow-dirty for development only"
            )
        suffix = "+dirty" if dirty else ""
        return revision.stdout.strip() + suffix

    def _matches_skill_history(self, spec: SkillSpec, candidate_hash: str) -> bool:
        history = _run(
            [
                "git",
                "log",
                "--format=%H",
                "--all",
                "--",
                spec.relative_path.as_posix(),
            ],
            cwd=self.repo_root,
            timeout=30,
        )
        if history.returncode != 0:
            raise SettingsError(f"could not inspect skill history: {history.stderr.strip()}")
        for revision in dict.fromkeys(history.stdout.splitlines()):
            archived_hash = git_archive_directory_hash(
                self.repo_root, revision, spec.relative_path
            )
            if archived_hash == candidate_hash:
                return True
        return False

    def _selected_capabilities(
        self,
        state: dict[str, Any] | None,
        extra_capabilities: Iterable[str],
    ) -> tuple[str, ...]:
        selected = set(
            state.get("selected_capabilities", [])
            if state is not None
            else self.manifest.default_capabilities
        )
        selected.update(extra_capabilities)
        selected.add("core")
        unknown = selected - set(self.manifest.capabilities)
        if unknown:
            raise SettingsError(f"unknown capabilities: {', '.join(sorted(unknown))}")
        return tuple(name for name in self.manifest.capabilities if name in selected)

    def _desired_assignments(
        self, selected_capabilities: Sequence[str]
    ) -> tuple[TemplateAssignment, ...]:
        assignments: list[TemplateAssignment] = []
        seen: set[tuple[str, ...]] = set()
        for capability in selected_capabilities:
            definition = self.manifest.capabilities[capability]
            for relative in definition["config_files"]:
                path = self.repo_root / relative
                for assignment in parse_template_assignments(
                    path.read_text(encoding="utf-8"), relative
                ):
                    if assignment.path in seen:
                        raise SettingsError(
                            f"managed config path appears in multiple capabilities: {_path_key(assignment.path)}"
                        )
                    seen.add(assignment.path)
                    assignments.append(assignment)
        return tuple(assignments)

    def _validate_candidate_with_codex(self, candidate_config: str) -> None:
        if not self.codex_bin:
            raise SettingsError("Codex CLI is required but was not found on PATH")
        with tempfile.TemporaryDirectory(
            prefix=".codex-settings-validate-", dir=self.repo_root
        ) as temporary:
            candidate_codex_home = Path(temporary) / "codex-home"
            candidate_codex_home.mkdir(mode=0o700)
            config_path = candidate_codex_home / "config.toml"
            config_path.write_text(candidate_config, encoding="utf-8")
            config_path.chmod(0o600)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(candidate_codex_home)
            # `doctor` is the Codex 0.148 command that supports strict config
            # validation. Route its connectivity checks to a closed loopback
            # port so synchronization remains a local-only operation.
            for key in (
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
                "http_proxy",
                "https_proxy",
                "all_proxy",
            ):
                environment[key] = "http://127.0.0.1:9"
            environment["NO_PROXY"] = ""
            environment["no_proxy"] = ""
            result = _run(
                [self.codex_bin, "--strict-config", "doctor", "--json"],
                env=environment,
                timeout=30,
            )
            try:
                report = json.loads(result.stdout)
            except json.JSONDecodeError:
                detail = (result.stderr or result.stdout).strip()
                raise SettingsError(
                    f"Codex strict validation did not return JSON: {detail}"
                )
            config_check = report.get("checks", {}).get("config.load", {})
            if config_check.get("status") != "ok":
                summary = config_check.get("summary", "config could not be loaded")
                notes = config_check.get("notes", [])
                detail = "; ".join(str(note) for note in notes)
                raise SettingsError(
                    f"Codex rejected the generated config: {summary}"
                    + (f" ({detail})" if detail else "")
                )

    def build_plan(
        self,
        *,
        allow_dirty: bool = False,
        extra_capabilities: Iterable[str] = (),
        require_existing_state: bool = False,
        validate_with_codex: bool = True,
    ) -> SyncPlan:
        state = _load_state(self.layout.state_path)
        if require_existing_state and state is None:
            raise SettingsError("codex-settings is not set up; run setup first")
        selected = self._selected_capabilities(state, extra_capabilities)
        revision = self._source_revision(allow_dirty)
        codex_version = self._codex_version()

        previous_managed_raw = state.get("managed_config", {}) if state else {}
        previous_managed = {
            _split_path(path): value for path, value in previous_managed_raw.items()
        }
        desired_assignments = self._desired_assignments(selected)
        if self.layout.config_path.exists():
            try:
                current_config = self.layout.config_path.read_text(encoding="utf-8")
            except OSError as error:
                raise SettingsError(
                    f"could not read {self.layout.config_path}: {error}"
                ) from error
        else:
            current_config = ""
        candidate_config, config_changes = merge_config(
            current_config,
            desired_assignments,
            previous_managed,
            self.manifest.config_migrations,
        )
        if validate_with_codex:
            self._validate_candidate_with_codex(candidate_config)

        previous_skills = state.get("managed_skills", {}) if state else {}
        desired_specs = tuple(
            skill for skill in self.manifest.skills if skill.capability in selected
        )
        desired_names = {skill.name for skill in desired_specs}
        skill_actions: list[SkillAction] = []
        legacy_removals: list[SkillAction] = []
        next_managed_skills: dict[str, dict[str, str]] = {}

        for spec in desired_specs:
            source = self.repo_root / spec.relative_path
            source_hash = directory_hash(source)
            destination = self.layout.skills_dir / spec.name
            previous = previous_skills.get(spec.name)
            if destination.exists() or destination.is_symlink():
                destination_hash = directory_hash(destination)
                if previous is not None:
                    if destination_hash != previous.get("sha256"):
                        raise SettingsError(
                            f"managed skill was modified locally: {destination}"
                        )
                    if destination_hash != source_hash:
                        skill_actions.append(
                            SkillAction(
                                action="update",
                                name=spec.name,
                                destination=destination,
                                source=source,
                                source_hash=source_hash,
                            )
                        )
                elif destination_hash != source_hash:
                    raise SettingsError(
                        f"unmanaged skill conflicts with {spec.name}: {destination}"
                    )
            else:
                skill_actions.append(
                    SkillAction(
                        action="add",
                        name=spec.name,
                        destination=destination,
                        source=source,
                        source_hash=source_hash,
                    )
                )

            legacy = self.layout.legacy_skills_dir / spec.name
            if legacy != destination and (legacy.exists() or legacy.is_symlink()):
                legacy_hash = directory_hash(legacy)
                if legacy_hash != source_hash and not self._matches_skill_history(
                    spec, legacy_hash
                ):
                    raise SettingsError(
                        f"legacy skill differs from the repository and was not removed: {legacy}"
                    )
                legacy_removals.append(
                    SkillAction(
                        action="remove-legacy",
                        name=spec.name,
                        destination=legacy,
                        source_hash=legacy_hash,
                    )
                )

            next_managed_skills[spec.name] = {
                "capability": spec.capability,
                "path": str(destination),
                "sha256": source_hash,
            }

        for name, previous in sorted(previous_skills.items()):
            if name in desired_names:
                continue
            destination = Path(previous.get("path", self.layout.skills_dir / name))
            expected = (self.layout.skills_dir / name).resolve()
            if destination.resolve() != expected:
                raise SettingsError(f"refusing to remove unexpected skill path: {destination}")
            if destination.exists() or destination.is_symlink():
                current_hash = directory_hash(destination)
                if current_hash != previous.get("sha256"):
                    raise SettingsError(
                        f"managed skill was modified locally and cannot be removed: {destination}"
                    )
                skill_actions.append(
                    SkillAction(action="remove", name=name, destination=destination)
                )

        next_state: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "source_commit": revision,
            "codex_version": codex_version,
            "selected_capabilities": list(selected),
            "applied_capabilities": list(selected),
            "managed_config": {
                _path_key(assignment.path): assignment.value
                for assignment in desired_assignments
            },
            "managed_skills": next_managed_skills,
        }
        semantic_changed = _semantic_state(state) != next_state
        if semantic_changed:
            next_state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        elif state is not None and "updated_at" in state:
            next_state["updated_at"] = state["updated_at"]

        return SyncPlan(
            candidate_config=candidate_config,
            config_changes=config_changes,
            skill_actions=tuple(skill_actions),
            legacy_removals=tuple(legacy_removals),
            next_state=next_state,
            previous_state=state,
            state_changed=semantic_changed,
        )

    def apply_plan(self, plan: SyncPlan) -> None:
        if not plan.has_changes:
            return
        self.layout.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.layout.backups_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.layout.skills_dir.mkdir(parents=True, exist_ok=True)
        self.layout.codex_home.mkdir(parents=True, exist_ok=True, mode=0o700)

        original_config = (
            self.layout.config_path.read_bytes() if self.layout.config_path.exists() else None
        )
        original_state = (
            self.layout.state_path.read_bytes() if self.layout.state_path.exists() else None
        )
        moved_backups: list[tuple[Path, Path]] = []
        created_destinations: list[Path] = []
        temporary_paths: list[Path] = []
        backup_record_path: Path | None = None

        try:
            if plan.config_changes:
                atomic_write_bytes(
                    self.layout.config_path,
                    plan.candidate_config.encode("utf-8"),
                    mode=0o600,
                )

            for action in (*plan.skill_actions, *plan.legacy_removals):
                destination = action.destination
                if action.action in {"add", "update"}:
                    if action.source is None:
                        raise SettingsError(f"missing source for {action.name}")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary = destination.parent / (
                        f".{destination.name}.codex-settings-new-{uuid.uuid4().hex}"
                    )
                    shutil.copytree(action.source, temporary)
                    temporary_paths.append(temporary)
                    if destination.exists():
                        backup = destination.parent / (
                            f".{destination.name}.codex-settings-old-{uuid.uuid4().hex}"
                        )
                        os.replace(destination, backup)
                        moved_backups.append((destination, backup))
                    else:
                        created_destinations.append(destination)
                    os.replace(temporary, destination)
                    temporary_paths.remove(temporary)
                elif action.action in {"remove", "remove-legacy"} and destination.exists():
                    backup = destination.parent / (
                        f".{destination.name}.codex-settings-old-{uuid.uuid4().hex}"
                    )
                    os.replace(destination, backup)
                    moved_backups.append((destination, backup))

            timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            backup_record_path = self.layout.backups_dir / f"{timestamp}.json"
            backup_record = {
                "schema_version": SCHEMA_VERSION,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "previous_state": plan.previous_state,
                "config_changes": [
                    {
                        "path": _path_key(change.path),
                        "action": change.action,
                        "before": None if change.before is _MISSING else change.before,
                        "after": None if change.after is _MISSING else change.after,
                    }
                    for change in plan.config_changes
                ],
                "skill_actions": [
                    {"name": action.name, "action": action.action}
                    for action in (*plan.skill_actions, *plan.legacy_removals)
                ],
            }
            atomic_write_bytes(backup_record_path, _json_bytes(backup_record), mode=0o600)
            atomic_write_bytes(
                self.layout.state_path, _json_bytes(plan.next_state), mode=0o600
            )
        except Exception as error:
            if original_config is None:
                self.layout.config_path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(self.layout.config_path, original_config, mode=0o600)
            if original_state is None:
                self.layout.state_path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(self.layout.state_path, original_state, mode=0o600)
            for destination in reversed(created_destinations):
                if destination.exists():
                    shutil.rmtree(destination)
            for destination, backup in reversed(moved_backups):
                if destination.exists():
                    shutil.rmtree(destination)
                if backup.exists():
                    os.replace(backup, destination)
            if backup_record_path is not None:
                backup_record_path.unlink(missing_ok=True)
            for temporary in temporary_paths:
                if temporary.exists():
                    shutil.rmtree(temporary)
            raise SettingsError(f"synchronization failed and was rolled back: {error}") from error
        else:
            for _, backup in moved_backups:
                if backup.exists():
                    shutil.rmtree(backup)
            for temporary in temporary_paths:
                if temporary.exists():
                    shutil.rmtree(temporary)

    def set_capability(self, name: str, enabled: bool) -> None:
        state = _load_state(self.layout.state_path)
        if state is None:
            raise SettingsError("codex-settings is not set up; run setup first")
        if name not in self.manifest.capabilities:
            raise SettingsError(f"unknown capability: {name}")
        if name == "core" and not enabled:
            raise SettingsError("the core capability cannot be disabled")
        selected = set(state.get("selected_capabilities", []))
        if enabled:
            selected.add(name)
        else:
            selected.discard(name)
        selected.add("core")
        ordered = [item for item in self.manifest.capabilities if item in selected]
        if ordered == state.get("selected_capabilities", []):
            return
        state["selected_capabilities"] = ordered
        state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        atomic_write_bytes(self.layout.state_path, _json_bytes(state), mode=0o600)

    def run_doctor(self) -> int:
        version = self._codex_version()
        print("repository: valid")
        print(f"python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"codex: {version}")
        state = _load_state(self.layout.state_path)
        selected = (
            state.get("selected_capabilities", [])
            if state is not None
            else list(self.manifest.default_capabilities)
        )
        if "browser" in selected:
            print(f"npx: {'available' if shutil.which('npx') else 'missing'}")
            browser_available = any(
                shutil.which(command)
                for command in ("google-chrome", "chromium", "chromium-browser")
            )
            print(f"browser: {'available' if browser_available else 'missing'}")
        result = _run([self.codex_bin, "doctor", "--json"], timeout=120)
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            detail = (result.stderr or result.stdout).strip()
            print(f"codex doctor: invalid report ({detail})", file=sys.stderr)
            return result.returncode or 2
        print(f"codex doctor: {report.get('overallStatus', 'unknown')}")
        checks = report.get("checks", {})
        if not isinstance(checks, dict):
            print("codex doctor: report did not contain checks", file=sys.stderr)
            return result.returncode or 2
        for check_id in sorted(checks):
            check = checks[check_id]
            if not isinstance(check, dict):
                continue
            status = check.get("status", "unknown")
            summary = check.get("summary", "no summary")
            print(f"  [{status}] {check_id}: {summary}")
            remediation = check.get("remediation")
            if remediation and status not in {"ok", "idle"}:
                print(f"    action: {remediation}")
        return result.returncode


def _safe_display(value: Any) -> str:
    if value is _MISSING:
        return "<absent>"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def print_plan(plan: SyncPlan) -> None:
    if not plan.has_changes:
        print("No changes. The target already matches the selected capabilities.")
        return
    print("Planned changes:")
    for change in plan.config_changes:
        print(
            f"  config {change.action}: {_path_key(change.path)} "
            f"{_safe_display(change.before)} -> {_safe_display(change.after)}"
        )
    for action in plan.skill_actions:
        print(f"  skill {action.action}: {action.name} -> {action.destination}")
    for action in plan.legacy_removals:
        print(f"  skill remove legacy copy: {action.name} -> {action.destination}")
    if plan.state_changed:
        print("  state: update managed ownership and source revision")


def _confirm() -> bool:
    answer = input("Apply these changes? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-settings",
        description="Safely synchronize portable Codex settings and shared skills.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_repo_root_from_script(),
        help=argparse.SUPPRESS,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("setup", "sync"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--dry-run", action="store_true")
        subparser.add_argument("--yes", action="store_true")
        subparser.add_argument(
            "--allow-dirty",
            action="store_true",
            help="allow an uncommitted checkout for development only",
        )
        subparser.add_argument(
            "--with",
            dest="extra_capabilities",
            action="append",
            default=[],
            metavar="CAPABILITY",
        )

    status = subparsers.add_parser("status")
    status.add_argument("--allow-dirty", action="store_true")

    capability = subparsers.add_parser("capability")
    capability_subparsers = capability.add_subparsers(dest="capability_action", required=True)
    for action in ("enable", "disable"):
        action_parser = capability_subparsers.add_parser(action)
        action_parser.add_argument("name")

    subparsers.add_parser("doctor")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manager = SettingsManager(args.repo_root)
        if args.command in {"setup", "sync", "status"}:
            plan = manager.build_plan(
                allow_dirty=args.allow_dirty,
                extra_capabilities=(
                    args.extra_capabilities if args.command in {"setup", "sync"} else ()
                ),
                require_existing_state=args.command in {"sync", "status"},
            )
            print_plan(plan)
            if args.command == "status":
                return 1 if plan.has_changes else 0
            if args.dry_run or not plan.has_changes:
                return 0
            if not args.yes:
                if not sys.stdin.isatty():
                    raise SettingsError(
                        "refusing to modify files without a TTY; rerun with --yes or --dry-run"
                    )
                if not _confirm():
                    print("Cancelled. No files were changed.")
                    return 1
            manager.apply_plan(plan)
            print("Synchronization completed.")
            return 0
        if args.command == "capability":
            enabled = args.capability_action == "enable"
            manager.set_capability(args.name, enabled)
            state = "enabled" if enabled else "disabled"
            print(f"Capability {args.name} is {state}. Run sync to apply the change.")
            return 0
        if args.command == "doctor":
            return manager.run_doctor()
        parser.error(f"unsupported command: {args.command}")
    except SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
