#!/usr/bin/env python3
"""frontmatter 付きの新規記事 Markdown ファイルを作成する。"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


class JapaneseArgumentParser(argparse.ArgumentParser):
    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "使い方:", 1)

    def format_help(self) -> str:
        return (
            super()
            .format_help()
            .replace("usage:", "使い方:", 1)
            .replace("options:", "オプション:", 1)
        )

    def error(self, message: str) -> None:
        translated = (
            message.replace("the following arguments are required:", "次の引数が必須です:")
            .replace("unrecognized arguments:", "不明な引数です:")
            .replace("argument ", "引数 ", 1)
        )
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: エラー: {translated}\n")


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("true/false を指定してください")


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
    parser = JapaneseArgumentParser(
        description="frontmatter 付きの記事 Markdown を作成します",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="ヘルプを表示して終了")
    parser.add_argument("--title", required=True, metavar="タイトル", help="記事タイトル")
    parser.add_argument("--slug", required=True, metavar="SLUG", help="記事ファイル名に使う slug")
    parser.add_argument("--description", default="", metavar="説明文", help="記事の説明文")
    parser.add_argument("--emoji", default="📝", metavar="絵文字", help="frontmatter に入れる絵文字")
    parser.add_argument("--date", default="", metavar="日付", help="公開日。未指定なら今日の日付")
    parser.add_argument("--topics", default="", metavar="トピック", help="カンマ区切りのトピック一覧")
    parser.add_argument(
        "--blog-published",
        type=parse_bool,
        default=True,
        metavar="公開フラグ",
        help="ブログの記事一覧に表示するか (true/false)",
    )
    parser.add_argument(
        "--published",
        type=parse_bool,
        default=False,
        metavar="外部公開フラグ",
        help="外部公開済みとして扱うか (true/false)",
    )
    parser.add_argument("--output-dir", default="articles", metavar="ディレクトリ", help="記事の出力ディレクトリ")
    parser.add_argument("--force", action="store_true", help="既存ファイルを上書き")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.slug}.md"

    if output_path.exists() and not args.force:
        raise SystemExit(f"ファイルは既に存在します: {output_path}（上書きする場合は --force を指定）")

    content = build_frontmatter(args) + build_body()
    output_path.write_text(content, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
