#!/usr/bin/env python3
"""Validate standalone ER reference HTML output."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


REQUIRED_IDS = {
    "tab-tables",
    "tab-relations",
    "tab-diagram",
    "tab-source",
    "pane-tables",
    "pane-relations",
    "pane-diagram",
    "pane-source",
}

FORBIDDEN_TERMS = (
    "prisma",
    "schema.prisma",
    "tab-prisma",
    "pane-prisma",
    "prisma-code",
    "prismaスキーマ案",
)


class ReferenceHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.tags: list[str] = []
        self.class_counts: dict[str, int] = {}
        self.external_refs: list[str] = []
        self.script_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag.lower())
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for class_name in attr_map.get("class", "").split():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1

        for name, value in attr_map.items():
            if not value:
                continue
            if name.startswith("xmlns"):
                continue
            normalized = value.strip().lower()
            if normalized.startswith(("http://", "https://", "//")):
                self.external_refs.append(f"{tag}.{name}={value}")

        if tag.lower() == "script" and attr_map.get("src"):
            self.script_srcs.append(attr_map["src"])


def validate(path: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1
    if path.suffix.lower() != ".html":
        warnings.append("output file does not use .html extension")

    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    parser = ReferenceHtmlParser()
    parser.feed(text)

    missing_ids = sorted(REQUIRED_IDS - parser.ids)
    if missing_ids:
        errors.append("missing required tab/pane ids: " + ", ".join(missing_ids))

    forbidden_found = sorted({term for term in FORBIDDEN_TERMS if term in lowered})
    if forbidden_found:
        errors.append("contains forbidden Prisma draft content: " + ", ".join(forbidden_found))

    if parser.external_refs:
        errors.append("contains external references: " + "; ".join(parser.external_refs[:8]))
    if parser.script_srcs:
        errors.append("contains external script src tags: " + ", ".join(parser.script_srcs))
    if re.search(r"@import\s+url\s*\(", text, flags=re.IGNORECASE):
        errors.append("contains CSS @import url")
    if re.search(r"url\s*\(\s*['\"]?(?:https?:)?//", text, flags=re.IGNORECASE):
        errors.append("contains external CSS url")

    if "svg" not in parser.tags:
        errors.append("missing inline SVG diagram")
    if "erdiagram" not in lowered:
        errors.append("missing Mermaid erDiagram source")
    if "<title>" not in lowered:
        warnings.append("missing title element")

    table_cards = parser.class_counts.get("tcard", 0)
    relation_rows = parser.class_counts.get("rel-row", 0)
    if table_cards == 0:
        errors.append("no table cards with class tcard found")
    if relation_rows == 0:
        errors.append("no relation rows with class rel-row found")

    placeholders = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text)))
    if placeholders:
        errors.append("template placeholders remain: " + ", ".join(placeholders))

    print(f"Checked: {path}")
    print(f"Table cards: {table_cards}")
    print(f"Relation rows: {relation_rows}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1

    print("OK: ER reference HTML contract passed")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: check_er_reference_html.py path/to/er_reference.html")
        return 2
    return validate(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
