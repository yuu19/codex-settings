#!/usr/bin/env python3
"""Create a new article markdown file with frontmatter."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true/false")


def parse_topics(raw: str) -> list[str]:
    return [topic.strip() for topic in raw.split(",") if topic.strip()]


def to_topics_literal(topics: list[str]) -> str:
    quoted = [f'"{topic}"' for topic in topics]
    return "[" + ", ".join(quoted) + "]"


def build_frontmatter(args: argparse.Namespace) -> str:
    today = dt.date.today().isoformat()
    date_value = args.date or today
    topics_literal = to_topics_literal(parse_topics(args.topics))

    blog_published = "True" if args.blog_published else "False"
    published = "True" if args.published else "False"

    return "\n".join(
        [
            "---",
            f"title: '{args.title}'",
            f"description: '{args.description}'",
            f"emoji: '{args.emoji}'",
            f"date: {date_value}",
            f"topics: {topics_literal}",
            f"blog_published: {blog_published}",
            f"published: {published}",
            "---",
            "",
        ]
    )


def build_body() -> str:
    return "\n".join(
        [
            "## はじめに",
            "",
            "## 1. 問題設定",
            "",
            "## 2. モデルと前提",
            "",
            "## 3. 導出・理論",
            "",
            "## 4. 実務上の注意点",
            "",
            "## まとめ",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create article markdown with frontmatter")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--emoji", default="📝")
    parser.add_argument("--date", default="")
    parser.add_argument("--topics", default="")
    parser.add_argument("--blog-published", type=parse_bool, default=True)
    parser.add_argument("--published", type=parse_bool, default=False)
    parser.add_argument("--output-dir", default="articles")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.slug}.md"

    if output_path.exists() and not args.force:
        raise SystemExit(f"File already exists: {output_path} (use --force to overwrite)")

    content = build_frontmatter(args) + build_body()
    output_path.write_text(content, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
