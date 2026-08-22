# コメント品質標準

## コメントマーカー

docblock ではないコメントには、必要に応じて次の marker を使う。marker は翻訳しない。

- `TODO:` - 将来の変更、未実装機能
- `FIXME:` - 既知の bug、重大な欠陥
- `HACK:` - 回避策、望ましくないが必要な実装
- `NOTE:` - 重要な補足情報
- `REVIEW:` - review で確認してほしい箇所
- `PERF:` - performance bottleneck や最適化候補
- `DEBUG:` - 一時的な debug code。後で削除する
- `REMARK:` - 一般的な観察や補足

marker には所有者と文脈を含める。

**誤り: 文脈がない**

```typescript
// TODO: fix this
// TODO: improve performance
// TODO: handle edge cases
```

**正しい: 所有者と具体的な action がある**

```typescript
// TODO(username): O(log n) lookup にするため binary search へ置き換える。
// FIXME(username): 空配列で例外になるため guard clause を追加する。
// HACK(username): API bug #1234 の一時回避。修正後に削除する。
```

## 削除するコメント

監査では次のコメントを削除する。

### コメントアウトされたコード

dead code はコメントとして残さず削除する。履歴は version control が保持する。

**誤り: dead code が残っている**

```typescript
function process(data: Data): Result {
  // const oldWay = transform(data);
  // return oldWay.map((value) => value * 2);
  return newWay(data);
}
```

**正しい: dead code を削除する**

```typescript
function process(data: Data): Result {
  return newWay(data);
}
```

### 編集履歴コメント

「追加した」「変更した」「削除した」といった履歴は削除する。変更履歴は Git が持つ。

**誤り: 編集履歴が comment にある**

```typescript
// Added 2024-01-15: new API support
// Changed by John: Use async/await
// Removed error handling (not needed)
async function fetchData(): Promise<Data> {
  // ...
}
```

**正しい: 編集履歴を削除する**

```typescript
async function fetchData(): Promise<Data> {
  // ...
}
```

### コードを言い換えただけのコメント

処理をそのまま言い換える comment は価値が低い。

**誤り: obvious comment**

```typescript
// counter を 1 増やす。
counter++;

// すべての users を loop する。
for (const user of users) {
  // ...
}

// true を返す。
return true;
```

**正しい: 自明でない意図だけを書く**

```typescript
// 次の batch のために counter を初期化する。
counter = 0;

// 登録順で処理する必要があるため、database の stable order を維持する。
for (const user of users) {
  // ...
}
```

## 保持するコメント

監査では次のコメントを保持する。

### marker comment

`TODO`, `FIXME`, `HACK`, `NOTE`, `REVIEW`, `PERF`, `DEBUG`, `REMARK` を使ったコメントは、文脈がある限り保持する。不十分な場合は削除ではなく具体化する。

```typescript
// TODO(alice): repeated query のため cache を追加する。
// FIXME(bob): concurrent request 時の race condition を解消する。
// PERF(charlie): O(n^2) loop を O(n log n) に最適化する。
```

### linter / tool directive

tool directive は syntax が重要なので変更しない。

```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = parseUnknownFormat(input);

// biome-ignore lint/suspicious/noExplicitAny: External API requires any
function processExternal(input: any): void {
  // ...
}

// prettier-ignore
const matrix = [
  1, 0, 0,
  0, 1, 0,
  0, 0, 1
];

// @ts-expect-error - Testing error handling
const result = functionThatThrows();
```

### 業務ルールや設計意図の説明

WHAT の言い換えではなく WHY を説明するコメントは保持する。

```typescript
// marketing policy により、discount は weekday のみ適用する。
const discount = isWeekday ? 0.1 : 0;

// API rate limit 回避のため、cache は 5 分で失効させる。
const CACHE_TTL = 5 * 60 * 1000;

// database が target column で pre-sort しているため binary search を使う。
const index = binarySearch(sortedData, target);
```

### docblock comment

JSDoc は保持し、不足があれば改善する。

```typescript
/**
 * 税込み価格を計算する。
 *
 * @param basePrice - 税抜き価格。
 * @param taxRate - 税率。`0.08` は 8% を表す。
 * @returns 税込み価格。
 */
function calculateTotal(basePrice: number, taxRate: number): number {
  return basePrice * (1 + taxRate);
}
```

## コメント配置

行末コメントは、原則として説明対象のコードの直前に移動する。長い行の末尾に埋もれることを防ぎ、diff でも読みやすくなる。

**誤り: 行末コメント**

```typescript
const MAX_RETRIES = 3; // 最大 retry 回数
const TIMEOUT = 5000; // request timeout milliseconds

function process(data: Data): Result {
  const normalized = normalize(data); // standard format へ変換
  const validated = validate(normalized); // required field を確認
  return transform(validated); // business rule を適用
}
```

**正しい: 直前行に置く**

```typescript
// 最大 retry 回数。
const MAX_RETRIES = 3;

// Request timeout milliseconds。
const TIMEOUT = 5000;

function process(data: Data): Result {
  // standard format へ変換する。
  const normalized = normalize(data);

  // required field を確認する。
  const validated = validate(normalized);

  // business rule を適用する。
  return transform(validated);
}
```

短い補足で、行長や可読性を損なわない場合は inline comment を許容してよい。

```typescript
const result = value ?? fallback; // null/undefined の場合だけ fallback を使う。
return items.filter((item) => item > 0); // negative value を除外する。
```

## 判断基準

- コメントはコードから読めない意図、制約、例外条件を補うために使う
- 実装手順の実況は避ける
- marker comment は具体的な action と所有者を持たせる
- directive comment は整形・翻訳・移動しない
- dead code と編集履歴は残さない
