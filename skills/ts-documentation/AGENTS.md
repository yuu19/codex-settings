# コードドキュメント監査

## 概要

JavaScript/TypeScript のドキュメントを日本語で監査・改善するためのガイド。JSDoc 標準、コメントマーカー、コードコメント品質を扱う。詳細な例は `references/` 配下を参照する。

---

## 使い方

1. **まずここを読む**: ルール概要から、対象コードの問題種別を判断する。
2. **必要な参照だけ読む**: 実装時に必要な詳細例だけ `references/` から読み込む。
3. **段階的に読む**: 各参照ファイルは自己完結しており、誤り/正しい例を含む。

この構成はコンテキスト使用量を抑えつつ、必要なときに十分な実装指針を提供する。

---

## 早見表

### いつ文書化するか

**エクスポートされたコード (Public API):**
- 常に包括的なドキュメントを書く。
- 必要項目: 概要, `@param`, `@returns`, `@template`, `@throws`, `@example`

**内部コード:**
- 自明でないことを書く。
- 目的、制約、特殊ケース、判断理由を優先する。
- `@example` と `@throws` は複雑な場合だけ使う。

---

## JSDoc 標準

### 関数
関数には概要、必要な `@param`、ジェネリックの `@template`、`void` 以外の `@returns` を確認する。エクスポートされた関数には `@throws` と `@example` も確認する。
[詳細例を見る](references/jsdoc.md#functions)

### 型と interface
型と interface には概要、ジェネリックの `@template`、公開プロパティの説明を確認する。
[詳細例を見る](references/jsdoc.md#types-and-interfaces)

### クラス
class には責務、ジェネリックの `@template`、エクスポートされた class の生成例、公開メソッドの説明を確認する。
[詳細例を見る](references/jsdoc.md#classes)

### 定数
定数には用途を説明する。単位、制約、デフォルト値として使われる文脈があれば明記する。
[詳細例を見る](references/jsdoc.md#constants)

### オブジェクトパラメータ
分割代入されたオブジェクトパラメータは `props.children` や `config.timeout` のように dot notation で説明する。
[詳細例を見る](references/jsdoc.md#object-parameter-と分割代入)

### コードフェンス要件
すべての `@example` は `typescript`, `javascript`, `tsx`, `jsx` などの言語指定付きコードフェンスを使う。
[詳細例を見る](references/jsdoc.md#example-の-code-fence)

---

## コメント品質

### コメントマーカー
`TODO`, `FIXME`, `HACK`, `NOTE`, `PERF`, `REVIEW`, `DEBUG`, `REMARK` を文脈と所有者付きで使う。
[詳細例を見る](references/comments.md#コメントマーカー)

### 削除するコメント
コメントアウトされたコード、編集履歴、コードを言い換えただけのコメントは削除する。
[詳細例を見る](references/comments.md#削除するコメント)

### 保持するコメント
マーカーコメント、ツールディレクティブ、業務ルールの説明、docblock は保持する。
[詳細例を見る](references/comments.md#保持するコメント)

### コメント配置
行末コメントは原則として対象コードの直前行へ移動する。
[詳細例を見る](references/comments.md#コメント配置)

---

## よくあるアンチパターン

避けること:
- コードフェンスのない `@example` を承認する
- 内部ユーティリティを過剰に文書化する
- public API の説明を不足させる
- コメントアウトされたコードを残す
- WHAT/WHY ではなく HOW を JSDoc に書く
- `void` 関数に `@returns` を付ける
- 文脈のない `TODO` を残す

修正例は `SKILL.md` と `references/` を参照する。
