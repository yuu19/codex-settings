# ER参照HTML契約

スキーマメモ、移行ドキュメント、テーブル一覧、Mermaid ER定義をスタンドアロンER参照HTMLへ変換するときは、この契約に従う。

## 入力

HTMLを書く前に、元資料を次のモデルへ正規化する:

```text
Document
  title
  version_or_context
  source_notes
  groups[]
  tables[]
  relations[]

Group
  name
  table_names[]

Table
  name
  group
  description
  columns[]
  legacy_columns[]

Column
  name
  type
  description
  tags: PK, FK, UK, nullable, derived, source-of-truth
  legacy: true または false

Relation
  from_table
  connector: ||--o{, ||--||, ||--o| などのMermaid ERコネクタ
  to_table
  label
  legacy: true または false
```

事実が不足している場合は、不明であることを見える形で残すか、短い注記を追加する。キー、制約、カーディナリティを捏造しない。

## 必須ページ構造

- ヘッダー: プロダクト/システム名、バージョンまたは文脈のバッジ、「外部リソースなし」相当のバッジ、テーブル数、リレーション数、必要に応じたlegacy概要。
- サイドバー: フラグメントアンカーを使った、グループ別のテーブルナビゲーション。
- テーブル定義: テーブルごとに1カード。現行カラムを先に表示し、legacyカラムは区切りの後に表示する。
- リレーション: リレーションごとに1行。コネクタとラベルを含める。
- ER図: スクロール可能なコンテナ内のインライン静的SVG。
- Mermaidソース: 対応する `erDiagram` ソースを含むコピー可能な `pre` ブロック。

Prismaスキーマ案セクションを追加しない。Prismaタブを追加しない。兄弟ファイルとして `.prisma` を生成しない。

## 見た目のパターン

- リポジトリにより強い既存規約がない限り、ドキュメント向けのダークUIを使う。
- コンパクトなカード、等幅のテーブル/カラム識別子、PK/FK/UK用バッジを使う。
- カードの角丸は10px以下にする。
- CSSのみのタブ、または単純な見出しを使う。参照ページにJavaScriptは不要。
- 印刷時にすべてのペインを表示し、ナビゲーションUIを隠すCSSを含める。

## Mermaidソース

Mermaidソースは、表示内容と一致させる:

```text
erDiagram
    table_name {
        varchar id PK "description"
        varchar parent_id FK "description"
    }

    parent ||--o{ table_name : "relation label"
```

legacyフィールドがテーブル定義に残る場合は、Mermaidソースにも表現する。ラベルや説明では、互換用または削除対象フィールドであることを示す。

## インラインSVGのルール

- 可搬性のため、textノード、rect、path、markerを中心に使い、foreignObjectは避ける。
- `viewBox` がすべてのノードとラベルを収めるようにする。
- 読みやすい10から14px程度のフォントサイズを使う。
- リレーションエッジには三次ベジェ曲線を優先する。
- リレーションラベルがノードと重ならないようにする。必要に応じて重要なエッジを外側へ迂回させる。

## 完了チェックリスト

- dev serverなしで、ファイルをブラウザで直接開ける。
- `http`、`https`、プロトコル相対URL、CDN、外部スタイルシート、外部スクリプト、Webフォント参照が残っていない。
- ページにテーブル定義、リレーション、埋め込みSVG図、Mermaidソースがある。
- HTMLにPrismaドラフトセクションやPrismaスキーマ案テキストが含まれていない。
- ヘッダーの件数が実際のテーブルカード数とリレーション行数に一致している。
- `scripts/check_er_reference_html.py` が成功する。
