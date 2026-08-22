---
description: JavaScript/TypeScript のドキュメントを日本語で監査・改善する。JSDoc コメント（@param, @returns, @template, @example）、コメントマーカー（TODO, FIXME, HACK）、コードコメント品質を扱う。「JSDoc 追加」「ドキュメント監査」「コメント修正」「add JSDoc」「document this function」「audit documentation」「fix comments」「add TODO/FIXME markers」「improve code documentation」などの依頼で使用する。
name: ts-documentation
---
# コードドキュメントスキル

JavaScript/TypeScript のドキュメントを日本語で改善するためのスキル。JSDoc、TODO/FIXME などのコメントマーカー、コードコメントの品質を扱う。

## 使う場面

このスキルは次の作業で使用する。

### JSDoc ドキュメント
- エクスポートされた関数、型、interface、class に JSDoc を追加する
- `@param`, `@returns`, `@template` などの不足を確認する
- `@example` が言語指定付きコードフェンスを使っているか確認する
- 分割代入されたオブジェクトパラメータを dot notation で文書化する

### コメント品質
- `TODO`, `FIXME`, `HACK`, `NOTE`, `PERF`, `REVIEW`, `DEBUG`, `REMARK` を適切に使う
- コメントアウトされたコード、編集履歴、明白な処理の説明を削除する
- マーカー、linter directive、業務ルールの説明など保持すべきコメントを守る
- 行末コメントを対象コードの直前へ移動して読みやすくする

### ドキュメント監査
- コードのドキュメント充足度を確認する
- public API に十分な説明があるか確認する
- 内部コードに必要最小限の説明があるか確認する

## 使わない場面

次の作業では別のスキルを優先する。

- 一般的なコード品質改善: `accelint-ts-best-practices`
- パフォーマンス最適化: `accelint-ts-performance`
- 型安全性の改善: `accelint-ts-best-practices`
- React PropTypes や Vue props など、フレームワーク固有の文書化

## 手順

### 1. タスクに応じて参照資料を読む

**JSDoc の追加・検証を行う場合**

**必須**: 実装前に [`jsdoc.md`](references/jsdoc.md) を全文読む。
特に `@example` のコードフェンス、オブジェクトパラメータの dot notation、`@template`、特殊ケースを確認する。

タスクが `TODO`, `FIXME` などのコメントマーカーやコメント品質に明示的に触れていない限り、`comments.md` は読まない。

**コメント品質を監査する場合**

**必須**: 実装前に [`comments.md`](references/comments.md) を全文読む。
特にマーカーの形式、削除するコメント、保持するコメント、配置ルールを確認する。

タスクが `@param`, `@returns` などの JSDoc タグや関数・型の文書化に明示的に触れていない限り、`jsdoc.md` は読まない。

質問への回答だけで、コード変更や監査レポートを作らない場合は、参照資料を読まなくてよい。

### 2. 読み手を決める

監査や修正の前に、次を判断する。

**誰が読むか**
- API 利用者: 実装文脈を持たないため、包括的に説明する
- チームメンバー: コードベースの文脈を持つため、自明でない振る舞いだけ説明する
- 将来の保守者: 判断理由を忘れるため、設計意図や例外条件を説明する

**不透明さと複雑さを分ける**
- 不透明さ: 意図がコードから読めない。必ず説明する
- 複雑さ: 実装が込み入っている。JSDoc ではなく必要箇所の実装コメントで補う

**保守コストを考える**
- 変更が多い内部コード: 説明は最小限にする
- 安定した public API: 説明を充実させる
- 利用頻度の低い内部ユーティリティ: 読む価値のある内容だけを書く

### 3. 二段階ルールで判断する

**エクスポートされた public API か**

YES の場合は包括的なドキュメントを必須にする。
- `@param`, `@returns`, `@template`, `@throws`, `@example` を必要に応じて記述する
- 自明に見える内容でも、利用者は実装文脈を持たない前提で説明する

**内部コードか**

次の情報から自明でないことだけを説明する。
1. 関数名と型シグネチャ
2. 引数名と型
3. コードベース内の標準的なパターン

目安: チームメンバーが「なぜ？」または「どの特殊ケース？」と聞きそうなら書く。読めば明らかな内容は書かない。

### 4. 充足度を確認する

**第 1 段階: エクスポートされたコード**
- 目的、利用場面、制約を説明する
- すべての `@param` を記述し、オブジェクトパラメータはプロパティも記述する
- `void` 以外は `@returns` を記述する
- ジェネリックは各型パラメータに `@template` を記述する
- throw されるエラーと条件を `@throws` で記述する
- 現実的な `@example` を少なくとも 1 つ入れる

**第 2 段階: 内部コード**
- 一行の概要で十分な場合がある
- 自明でないパラメータだけ `@param` を書く
- 自明でない戻り値だけ `@returns` を書く
- ジェネリックは `@template` を書く
- 複雑な振る舞いに限り `@example` を書く

**対象ごとの追加確認**
- クラス: エクスポートされたクラスではコンストラクタ、公開メソッド、生成例を確認する
- 型/interface: 公開プロパティには説明を付ける
- 定数/変数: 単位、制約、範囲がある場合は説明する

**チェックリスト**
- [ ] エクスポートされた項目に包括的な JSDoc がある
- [ ] `@param` は型の繰り返しではなく、パラメータの意味を説明している
- [ ] `@returns` はシナリオごとの戻り値を説明している
- [ ] `@example` は言語指定付きコードフェンスを使っている
- [ ] `void` 関数に `@returns` がない
- [ ] ジェネリックに `@template` がある
- [ ] オブジェクトパラメータは dot notation でプロパティを説明している
- [ ] WHAT/WHY を説明し、HOW の説明に寄りすぎていない

### 5. 参照資料だけで判断できない場合

1. エクスポート / 内部の二段階ルールを基準にする
2. 推測で構文を増やすより、自然言語で明確に説明する
3. TypeScript / JSDoc の標準的な慣習に従う
4. 不確かな箇所は `// NOTE: [具体的なケース] の JSDoc 構文は確認が必要` のように残す
5. 仕様判断が必要ならユーザーに確認する

よくある未網羅シナリオ:
- mapped type、conditional type、template literal type などの高度な TypeScript 型
- ジェネリック付き React hooks、Vue composables などのフレームワークパターン
- overload を持つコールバックシグネチャ

### 6. 明示的な監査依頼ではレポートテンプレートを使う

ユーザーがドキュメント監査を明示した場合、または `/ts-documentation <path>` としてスキルを直接呼び出した場合は、標準レポート形式を使う。

**テンプレート:** [`assets/output-report-template.md`](assets/output-report-template.md)

テンプレートを使う場面:
- `/ts-documentation <path>` で直接呼び出された
- 「documentation audit」「ドキュメント監査」「ドキュメントをレビュー」と依頼された
- 複数ファイルのドキュメント問題を一覧化する必要がある

テンプレートを使わない場面:
- 「この関数に JSDoc を追加して」のような直接実装
- 「このコメントの何が悪い？」のような質問回答
- 特定の修正を依頼され、正式な監査レポートが不要な場合

## 監査時のアンチパターン

### 誤り: 内部コードを過剰に文書化する

```typescript
/**
 * 入力値を検証する内部ヘルパー。
 * @internal
 * @param value - 検証対象の値。
 * @returns 有効な場合は true。
 * @example
 * ```typescript
 * if (isValid(data)) { ... }
 * ```
 */
function isValid(value: unknown): boolean {
  return value != null;
}
```

問題: 内部コードは変更頻度が高く、過剰な説明は実装から乖離しやすい。public API ではなく内部実装なら、読み手がコードを読んで理解できる内容は省く。

### 正しい: 内部は最小限、public API は包括的

```typescript
/** null/undefined ではないことを確認する。 */
function isValid(value: unknown): boolean {
  return value != null;
}

/**
 * ユーザー入力データを検証する。
 *
 * @param data - 検証対象のユーザー入力。
 * @returns 入力が定義済みで null ではない場合は true。
 *
 * @example
 * ```typescript
 * if (validateInput(userData)) {
 *   processData(userData);
 * }
 * ```
 */
export function validateInput(data: unknown): boolean {
  return data != null;
}
```

### 誤り: WHAT/WHY ではなく HOW を説明する

```typescript
/**
 * reduce を使って配列を走査し、値を合計する。
 */
function sum(numbers: number[]): number {
  return numbers.reduce((a, b) => a + b, 0);
}
```

問題: JSDoc は IDE 補完にも表示される。実装手順を書くと利用者に不要な情報が増え、実装変更のたびにドキュメント更新が必要になる。

### 正しい: 目的と振る舞いを説明する

```typescript
/**
 * 配列内の数値を合計する。
 *
 * @param numbers - 合計する数値の配列。
 * @returns 合計値。空配列の場合は 0。
 */
function sum(numbers: number[]): number {
  return numbers.reduce((a, b) => a + b, 0);
}
```

### 誤り: 曖昧なコメントマーカーを残す

```typescript
// TODO: fix this
// TODO: improve performance
```

問題: 誰が、何を、なぜ直すのか分からないマーカーは蓄積して無視される。

### 正しい: 所有者と文脈を入れる

```typescript
// TODO(username): O(log n) lookup にするため binary search へ置き換える。
// FIXME(username): 空配列で例外になるため guard clause を追加する。
```

## 品質例

```typescript
/**
 * 認証サービスからユーザープロフィールを取得する。
 *
 * ネットワーク失敗時は指数バックオフで最大 3 回再試行する。
 * セッションが無効な場合、またはプロフィールが存在しない場合は例外を投げる。
 *
 * @param userId - 取得対象ユーザーの一意な ID。
 * @param options - 取得動作の設定。
 * @param options.includeMetadata - 作成日時や最終ログインなどの metadata を含めるか。
 * @param options.timeout - request timeout milliseconds。未指定時は 5000。
 * @returns email、name、任意の metadata を含むユーザープロフィール。
 * @throws {AuthenticationError} セッションが期限切れまたは無効な場合。
 * @throws {NotFoundError} プロフィールが存在しない場合。
 * @throws {NetworkError} すべての retry が失敗した場合。
 *
 * @example
 * ```typescript
 * const profile = await fetchUserProfile('user-123', {
 *   includeMetadata: true,
 *   timeout: 10000,
 * });
 * ```
 */
export async function fetchUserProfile(
  userId: string,
  options?: { includeMetadata?: boolean; timeout?: number }
): Promise<UserProfile> {
  // implementation
}
```

良い理由:
- リトライやエラー条件など、シグネチャから分からない振る舞いを説明している
- オブジェクトパラメータを dot notation で説明している
- `@throws` が条件付きで書かれている
- `@example` が現実的で、言語指定付きコードフェンスを使っている
- WHAT/WHY を中心に書き、実装手順に寄りすぎていない

## 判断が衝突したときの優先順位

1. 一貫性 > 完璧さ: 既存コードベースのパターンに合わせる
2. 利用者 > 実装者: public API は文脈を持たない利用者に向けて書く
3. 意図 > 実装: WHAT/WHY を書き、HOW は必要な場合に限る
4. 安定 > 変更中: 安定した API は詳しく、頻繁に変わる内部実装は薄く書く
5. 未来の明瞭さ: 6 か月後の自分に役立たない説明は削る

## edge case

deprecated API、overload、generic utility type、callback parameter、builder pattern、event emitter などは [`jsdoc.md`](references/jsdoc.md) を読む。edge case でも export / internal の二段階ルールを守り、syntax は推測しない。
