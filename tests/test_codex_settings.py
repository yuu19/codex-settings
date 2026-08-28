from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "lib"))

import codex_settings
from codex_settings import (
    SettingsError,
    SettingsManager,
    TargetLayout,
    TemplateAssignment,
    directory_hash,
    load_manifest,
    merge_config,
)


def write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def create_skill(root: Path, name: str, marker: str = "v1") -> None:
    write(
        root / "skills" / name / "SKILL.md",
        f"""
        ---
        name: {name}
        description: Test skill {name}.
        ---

        # {name}

        {marker}
        """,
    )


def create_agent(root: Path, name: str, marker: str = "v1") -> None:
    write(
        root / ".codex" / "agents" / f"{name}.toml",
        f'''\
        name = "{name}"
        description = "Test custom agent {name}."
        model = "gpt-test"
        model_reasoning_effort = "high"
        sandbox_mode = "read-only"
        developer_instructions = """
        Review only.
        {marker}
        """
        ''',
    )


def create_fake_codex(path: Path) -> None:
    write(
        path,
        """
        #!/usr/bin/env python3
        import json
        import sys

        if "--version" in sys.argv:
            print("codex-cli 0.148.0")
        elif "doctor" in sys.argv:
            print(json.dumps({"checks": {"config.load": {"status": "ok"}}}))
        else:
            print("feature stable true")
        """,
        mode=0o755,
    )


def create_repository(root: Path) -> None:
    create_skill(root, "core-skill")
    create_skill(root, "browser-skill")
    create_agent(root, "core_agent")
    create_agent(root, "browser_agent")
    write(
        root / "config.toml",
        """
        model = "gpt-test"
        personality = "pragmatic"

        [features]
        memories = true
        """,
    )
    write(
        root / "config" / "browser.toml",
        """
        [mcp_servers.playwright]
        command = "npx"
        args = ["--yes", "@playwright/mcp@1.2.3"]
        """,
    )
    write(
        root / "manifest.toml",
        """
        schema_version = 1
        minimum_codex_version = "0.148.0"

        [capabilities.core]
        default = true
        config_files = ["config.toml"]

        [capabilities.browser]
        default = false
        config_files = ["config/browser.toml"]

        [[skills]]
        name = "core-skill"
        path = "skills/core-skill"
        capability = "core"

        [[skills]]
        name = "browser-skill"
        path = "skills/browser-skill"
        capability = "browser"

        [[agents]]
        name = "core_agent"
        path = ".codex/agents/core_agent.toml"
        capability = "core"

        [[agents]]
        name = "browser_agent"
        path = ".codex/agents/browser_agent.toml"
        capability = "browser"

        [[packages]]
        name = "@playwright/mcp"
        version = "1.2.3"
        capability = "browser"
        """,
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "codex-settings tests"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "test fixture"], cwd=root, check=True)


class RepositoryManifestTests(unittest.TestCase):
    def test_real_manifest_has_expected_capability_groups_and_pins(self) -> None:
        manifest = load_manifest(REPOSITORY_ROOT)
        groups = {
            capability: {skill.name for skill in manifest.skills if skill.capability == capability}
            for capability in manifest.capabilities
        }
        self.assertEqual(
            groups["core"],
            {
                "blog-article-creator",
                "create-er-reference-html",
                "japanese-conventional-commit",
                "natural-japanese",
                "playwright-e2e-test-writer",
                "ts-documentation",
            },
        )
        self.assertEqual(
            groups["browser"],
            {"chrome-web-store", "saas-user-manual-screenshot-writer"},
        )
        self.assertEqual(
            {(package.name, package.version) for package in manifest.packages},
            {("@playwright/mcp", "0.0.79"), ("chrome-devtools-mcp", "1.7.0")},
        )
        self.assertEqual(manifest.minimum_codex_version, "0.150.1")
        self.assertEqual(
            {agent.name for agent in manifest.agents},
            {
                "quick_proofreader",
                "structure_reviewer",
                "structure_reviewer_max",
                "readability_reviewer",
                "readability_reviewer_max",
                "blog_fit_reviewer",
                "blog_fit_reviewer_max",
            },
        )

    def test_real_custom_agents_use_pinned_read_only_profiles(self) -> None:
        manifest = load_manifest(REPOSITORY_ROOT)
        for agent in manifest.agents:
            definition = tomllib.loads(
                (REPOSITORY_ROOT / agent.relative_path).read_text(encoding="utf-8")
            )
            self.assertEqual(definition["name"], agent.name)
            self.assertEqual(definition["model"], "gpt-5.6-sol")
            self.assertEqual(definition["sandbox_mode"], "read-only")
            expected_effort = (
                "high"
                if agent.name == "quick_proofreader"
                else "max"
                if agent.name.endswith("_max")
                else "xhigh"
            )
            self.assertEqual(definition["model_reasoning_effort"], expected_effort)

    def test_readmes_list_every_managed_skill(self) -> None:
        manifest = load_manifest(REPOSITORY_ROOT)
        readmes = (
            (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPOSITORY_ROOT / "skills" / "README.md").read_text(encoding="utf-8"),
        )
        for skill in manifest.skills:
            for readme in readmes:
                self.assertIn(f"`{skill.name}`", readme)

    def test_natural_japanese_records_upstream_and_local_policy(self) -> None:
        skill = REPOSITORY_ROOT / "skills" / "natural-japanese"
        provenance = (skill / "UPSTREAM.md").read_text(encoding="utf-8")
        entrypoint = (skill / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("v1.3.0", provenance)
        self.assertIn("b54954f8deb4f110f0959f4e4fac295708900120", provenance)
        self.assertIn("MIT License", (skill / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("references/technical-document-policy.md", entrypoint)
        self.assertTrue((skill / "references" / "technical-document-policy.md").is_file())
        self.assertIn(
            "$natural-japanese",
            (skill / "agents" / "openai.yaml").read_text(encoding="utf-8"),
        )

    def test_blog_article_creator_routes_natural_japanese_proofreading(self) -> None:
        skill = REPOSITORY_ROOT / "skills" / "blog-article-creator"
        entrypoint = (skill / "SKILL.md").read_text(encoding="utf-8")
        proofreading_path = skill / "references" / "natural-japanese-proofreading.md"

        self.assertTrue(proofreading_path.is_file())
        self.assertIn("references/natural-japanese-proofreading.md", entrypoint)

        proofreading = proofreading_path.read_text(encoding="utf-8")
        for contract in (
            "natural-japanese",
            "--genre tech",
            "quick",
            "full",
            "max",
            "fork_turns",
            "ファイルを変更しない",
            "判断台帳",
            "手動チェックリスト",
        ):
            self.assertIn(contract, proofreading)

        for agent_name in (
            "quick_proofreader",
            "structure_reviewer",
            "readability_reviewer",
            "blog_fit_reviewer",
        ):
            self.assertIn(agent_name, proofreading)
        self.assertIn("_max", proofreading)

    def test_cli_entrypoint_is_executable(self) -> None:
        entrypoint = REPOSITORY_ROOT / "bin" / "codex-settings"
        self.assertTrue(os.access(entrypoint, os.X_OK))

    def test_real_core_config_excludes_local_security_and_unstable_keys(self) -> None:
        text = (REPOSITORY_ROOT / "config.toml").read_text(encoding="utf-8")
        for forbidden in (
            "network_access",
            "approval_policy",
            "approvals_reviewer",
            "sandbox_mode",
            "remote_connections",
            "rmcp_client",
            "streamable_shell",
            "js_repl",
            "prevent_idle_sleep",
            "ollama",
            "@latest",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn('url = "https://mcp.context7.com/mcp"', text)


class ConfigMergeTests(unittest.TestCase):
    def test_merge_updates_owned_values_and_preserves_local_tables(self) -> None:
        current = textwrap.dedent(
            """
            # local comment
            model = "old-model"
            approvals_reviewer = "auto_review"

            [features]
            memories = false
            hooks = true

            [projects."/srv/app"]
            trust_level = "trusted"
            """
        ).lstrip()
        desired = (
            TemplateAssignment(("model",), 'model = "new-model"', "new-model"),
            TemplateAssignment(("features", "memories"), "memories = true", True),
        )
        merged, changes = merge_config(
            current,
            desired,
            {("model",): "old-model", ("features", "memories"): False},
        )
        self.assertIn("# local comment", merged)
        self.assertIn('approvals_reviewer = "auto_review"', merged)
        self.assertIn('trust_level = "trusted"', merged)
        self.assertIn("hooks = true", merged)
        self.assertIn('model = "new-model"', merged)
        self.assertIn("memories = true", merged)
        self.assertEqual({change.action for change in changes}, {"update"})

    def test_removing_mcp_with_local_tool_rules_stops(self) -> None:
        current = textwrap.dedent(
            """
            [mcp_servers.playwright]
            command = "npx"
            args = ["@playwright/mcp@1.2.3"]

            [mcp_servers.playwright.tools.browser_click]
            approval_mode = "auto"
            """
        ).lstrip()
        previous = {
            ("mcp_servers", "playwright", "command"): "npx",
            ("mcp_servers", "playwright", "args"): ["@playwright/mcp@1.2.3"],
        }
        with self.assertRaisesRegex(SettingsError, "contains local settings"):
            merge_config(current, (), previous)

    def test_known_legacy_transport_is_removed_by_migration(self) -> None:
        current = textwrap.dedent(
            """
            [mcp_servers.context7]
            command = "npx"
            args = ["-y", "@upstash/context7-mcp@latest"]
            """
        ).lstrip()
        desired = (
            TemplateAssignment(
                ("mcp_servers", "context7", "url"),
                'url = "https://mcp.context7.com/mcp"',
                "https://mcp.context7.com/mcp",
            ),
        )
        migrations = (
            codex_settings.ConfigMigration(
                ("mcp_servers", "context7", "command"), "npx"
            ),
            codex_settings.ConfigMigration(
                ("mcp_servers", "context7", "args"),
                ["-y", "@upstash/context7-mcp@latest"],
            ),
        )
        merged, _ = merge_config(current, desired, {}, migrations)
        parsed = __import__("tomllib").loads(merged)
        self.assertEqual(
            parsed["mcp_servers"]["context7"],
            {"url": "https://mcp.context7.com/mcp"},
        )

    def test_changed_legacy_transport_stops_migration(self) -> None:
        current = textwrap.dedent(
            """
            [mcp_servers.context7]
            command = "custom-context7"
            """
        ).lstrip()
        migration = codex_settings.ConfigMigration(
            ("mcp_servers", "context7", "command"), "npx"
        )
        with self.assertRaisesRegex(SettingsError, "migration conflict"):
            merge_config(current, (), {}, (migration,))


class SynchronizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        create_repository(self.repo)
        self.fake_codex = self.base / "bin" / "codex"
        create_fake_codex(self.fake_codex)
        self.home = self.base / "home"
        self.layout = TargetLayout(
            home=self.home,
            codex_home=self.home / ".codex",
            state_dir=self.home / ".local" / "state" / "codex-settings",
        )
        self.manager = SettingsManager(
            self.repo,
            layout=self.layout,
            codex_bin=str(self.fake_codex),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_setup_is_idempotent_and_preserves_local_config(self) -> None:
        write(
            self.layout.config_path,
            """
            approvals_reviewer = "auto_review"

            [projects."/srv/app"]
            trust_level = "trusted"
            """,
        )
        first = self.manager.build_plan()
        self.assertTrue(first.has_changes)
        self.manager.apply_plan(first)

        installed_config = self.layout.config_path.read_text(encoding="utf-8")
        self.assertIn('approvals_reviewer = "auto_review"', installed_config)
        self.assertIn('trust_level = "trusted"', installed_config)
        self.assertIn('model = "gpt-test"', installed_config)
        self.assertTrue((self.layout.skills_dir / "core-skill" / "SKILL.md").is_file())
        self.assertFalse((self.layout.skills_dir / "browser-skill").exists())
        self.assertTrue((self.layout.agents_dir / "core_agent.toml").is_file())
        self.assertFalse((self.layout.agents_dir / "browser_agent.toml").exists())

        second = self.manager.build_plan(require_existing_state=True)
        self.assertFalse(second.has_changes)

    def test_doctor_reports_optional_uv_status(self) -> None:
        for executable, expected in (
            ("/usr/bin/uv", "uv (natural-japanese lint): available"),
            (None, "uv (natural-japanese lint): missing (manual checklist fallback)"),
        ):
            with self.subTest(executable=executable):
                with mock.patch("codex_settings.shutil.which", return_value=executable):
                    with mock.patch("builtins.print") as print_mock:
                        self.assertEqual(self.manager.run_doctor(), 0)
                print_mock.assert_any_call(expected)

    def test_browser_capability_can_be_enabled_then_pruned(self) -> None:
        initial = self.manager.build_plan(extra_capabilities=("browser",))
        self.manager.apply_plan(initial)
        self.assertTrue((self.layout.skills_dir / "browser-skill").is_dir())
        self.assertTrue((self.layout.agents_dir / "browser_agent.toml").is_file())
        self.assertIn(
            "[mcp_servers.playwright]",
            self.layout.config_path.read_text(encoding="utf-8"),
        )

        self.manager.set_capability("browser", False)
        prune = self.manager.build_plan(require_existing_state=True)
        self.assertIn("remove", {action.action for action in prune.skill_actions})
        self.assertIn("remove", {action.action for action in prune.agent_actions})
        self.manager.apply_plan(prune)
        self.assertFalse((self.layout.skills_dir / "browser-skill").exists())
        self.assertFalse((self.layout.agents_dir / "browser_agent.toml").exists())
        self.assertNotIn(
            "[mcp_servers.playwright]",
            self.layout.config_path.read_text(encoding="utf-8"),
        )

    def test_unmanaged_skill_conflict_stops_before_changes(self) -> None:
        create_skill(self.home / ".agents", "core-skill", marker="local")
        with self.assertRaisesRegex(SettingsError, "unmanaged skill conflicts"):
            self.manager.build_plan()
        self.assertFalse(self.layout.state_path.exists())

    def test_unmanaged_custom_agent_conflict_stops_before_changes(self) -> None:
        write(
            self.layout.agents_dir / "core_agent.toml",
            'name = "core_agent"\ndescription = "Local"\ndeveloper_instructions = "Local"\n',
        )
        with self.assertRaisesRegex(SettingsError, "unmanaged custom agent conflicts"):
            self.manager.build_plan()
        self.assertFalse(self.layout.state_path.exists())

    def test_unrelated_custom_agent_is_preserved(self) -> None:
        local_agent = self.layout.agents_dir / "personal.toml"
        write(
            local_agent,
            'name = "personal"\ndescription = "Local"\ndeveloper_instructions = "Local"\n',
        )
        plan = self.manager.build_plan()
        self.manager.apply_plan(plan)
        self.assertTrue(local_agent.is_file())

    def test_managed_custom_agent_updates_atomically(self) -> None:
        initial = self.manager.build_plan()
        self.manager.apply_plan(initial)

        create_agent(self.repo, "core_agent", marker="v2")
        update = self.manager.build_plan(
            allow_dirty=True,
            require_existing_state=True,
        )
        self.assertEqual(
            [(action.name, action.action) for action in update.agent_actions],
            [("core_agent", "update")],
        )
        self.manager.apply_plan(update)

        installed = self.layout.agents_dir / "core_agent.toml"
        self.assertIn("v2", installed.read_text(encoding="utf-8"))
        self.assertEqual(installed.stat().st_mode & 0o777, 0o600)

    def test_modified_managed_custom_agent_is_rejected(self) -> None:
        initial = self.manager.build_plan()
        self.manager.apply_plan(initial)
        write(self.layout.agents_dir / "core_agent.toml", "locally modified\n")

        with self.assertRaisesRegex(SettingsError, "modified locally"):
            self.manager.build_plan(require_existing_state=True)

    def test_symlinked_destination_is_not_overwritten(self) -> None:
        create_skill(self.base / "external", "core-skill")
        external = self.base / "external" / "skills" / "core-skill"
        destination = self.layout.skills_dir / "core-skill"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(SettingsError, "may not be a symlink"):
            self.manager.build_plan()

    def test_dirty_source_is_rejected(self) -> None:
        write(self.repo / "untracked.txt", "dirty\n")
        with self.assertRaisesRegex(SettingsError, "checkout is dirty"):
            self.manager.build_plan()
        dirty_plan = self.manager.build_plan(allow_dirty=True)
        self.assertTrue(dirty_plan.next_state["source_commit"].endswith("+dirty"))

    def test_apply_failure_restores_config_skills_and_state(self) -> None:
        write(self.layout.config_path, 'approvals_reviewer = "auto_review"\n')
        original_config = self.layout.config_path.read_bytes()
        plan = self.manager.build_plan()
        real_atomic_write = codex_settings.atomic_write_bytes

        def fail_on_state(path: Path, content: bytes, mode: int = 0o600) -> None:
            if path == self.layout.state_path:
                raise OSError("injected state failure")
            real_atomic_write(path, content, mode)

        with mock.patch("codex_settings.atomic_write_bytes", side_effect=fail_on_state):
            with self.assertRaisesRegex(SettingsError, "rolled back"):
                self.manager.apply_plan(plan)

        self.assertEqual(self.layout.config_path.read_bytes(), original_config)
        self.assertFalse((self.layout.skills_dir / "core-skill").exists())
        self.assertFalse((self.layout.agents_dir / "core_agent.toml").exists())
        self.assertFalse(self.layout.state_path.exists())

    def test_legacy_copy_is_removed_only_when_it_matches(self) -> None:
        source = self.repo / "skills" / "core-skill"
        legacy = self.layout.legacy_skills_dir / "core-skill"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copytree(source, legacy)
        plan = self.manager.build_plan()
        self.assertEqual([item.action for item in plan.legacy_removals], ["remove-legacy"])
        self.manager.apply_plan(plan)
        self.assertFalse(legacy.exists())

        # A local legacy variant must not be silently removed.
        self.layout.state_path.unlink()
        create_skill(self.layout.legacy_skills_dir.parent, "core-skill", marker="local")
        with self.assertRaisesRegex(SettingsError, "legacy skill differs"):
            self.manager.build_plan()

    def test_legacy_copy_matching_repository_history_is_migrated(self) -> None:
        source = self.repo / "skills" / "core-skill"
        legacy = self.layout.legacy_skills_dir / "core-skill"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copytree(source, legacy)
        write(source / "SKILL.md", source.joinpath("SKILL.md").read_text() + "\nv2\n")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "update core skill"],
            cwd=self.repo,
            check=True,
        )

        plan = self.manager.build_plan()
        self.assertEqual([item.action for item in plan.legacy_removals], ["remove-legacy"])
        self.manager.apply_plan(plan)
        self.assertFalse(legacy.exists())
        self.assertEqual(
            directory_hash(self.layout.skills_dir / "core-skill"),
            directory_hash(source),
        )


if __name__ == "__main__":
    unittest.main()
