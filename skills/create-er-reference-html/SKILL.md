---
name: create-er-reference-html
description: Create standalone ER diagram reference HTML files from schema notes, table docs, Mermaid ER definitions, or migration design docs. Use when Codex needs to produce or update an offline ER reference page like packages/barem/docs/barem_schema_reference.html with table cards, relation lists, embedded static SVG, and Mermaid source. Do not include Prisma schema proposal panes, Prisma drafts, or .prisma file generation unless the user explicitly asks outside this skill.
---

# ER参照HTML作成

## 概要

データベース設計をレビューする人間向けに、単一ファイルで開けるオフラインER参照HTMLを作成する。既存の参照ページがある場合はローカルの見た目に合わせ、出力内容はテーブル、リレーション、埋め込みER図、元ソース表記に集中させる。

## ワークフロー

1. 依頼された出力先、近くのドキュメント、既存のER HTMLを確認する。このリポジトリでは、該当する場合は `packages/barem/docs/barem_schema_reference.html` を最も近い見た目の参照として使う。
2. HTMLを新規作成または大きく更新する前に `references/html-contract.md` を読む。
3. HTMLを書く前に、内部的なスキーマモデルを整理する:
   - ドメインごとにグルーピングしたテーブル
   - 型、説明、PK/FK/UKタグを持つカラム
   - 現行フィールドと分離した legacy または互換用フィールド
   - Mermaidのカーディナリティ、ラベル、legacyフラグを持つリレーション
   - 推測で埋めず、見える形で残すべき警告や不明点
4. 新規ファイルでは `assets/er-reference-template.html` から開始する。既存ファイルの更新では、そのファイルのローカル構造をできるだけ保つ。
5. インラインCSS、インラインSVG、インラインMermaidソースを含むスタンドアロンHTMLを出力する。ネットワークアセット、CDNスクリプト、Mermaid.js、Google Fonts、外部スタイルシートには依存しない。
6. 生成したHTMLに対して `scripts/check_er_reference_html.py` を実行し、失敗をすべて修正する。

## 出力要件

- テーブル定義、リレーション、ER図、Mermaidソースのペインまたはセクションを含める。
- Prismaスキーマ案、Prismaタブ、Prismaコードブロック、生成 `.prisma` ファイルは含めない。
- ER図は埋め込み静的SVGにする。Mermaidソースはコピー・参照用として含めるだけで、外部JavaScriptでレンダリングしない。
- サイドバーからテーブルカードへリンクできるよう、テーブル名から導出した安定したアンカーを使う。
- ソース由来のテキストは、HTMLへ挿入する前に必ずエスケープする。
- 印刷スタイル、レスポンシブ表示、外部fetchなしを満たし、オフラインで使えるページにする。
- 元資料が日本語の場合は、日本語のラベルと説明を保持する。

## 図の方針

- テーブルはアルファベット順ではなく、業務ドメインまたはデータフローの向きで配置する。
- SVGノードはコンパクトにし、テーブル名、カラム数、PK概要、FK数を表示する。
- エッジの経路は見やすく、控えめにする。強調は最重要または誤読されやすいリレーションに限る。
- legacyリレーションはリレーション一覧とMermaidソースで明示する。SVG上で別スタイルにするのは、可読性が上がる場合だけにする。
- 大きいスキーマでは、文字が読めなくなるまで縮小するより、横幅のあるスクロール可能なSVGを優先する。

## 検証

実行する:

```bash
python3 .agents/skills/create-er-reference-html/scripts/check_er_reference_html.py path/to/output.html
```

この検証スクリプトは、HTMLがスタンドアロンであること、期待されるER参照セクションを持つこと、インラインSVGとMermaidソースを含むこと、Prismaドラフト内容を含まないことを確認する。

## リソース

- `references/html-contract.md`: 受け付けるスキーマ情報と必須HTML構造の簡潔な契約。
- `assets/er-reference-template.html`: 新しいスタンドアロンER参照ページの開始点。
- `scripts/check_er_reference_html.py`: 生成したER参照HTMLの決定的な検証。
