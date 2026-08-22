# JSDoc ドキュメント標準

## 対象範囲

JSDoc は日本語で記述する。tag 名、型名、symbol 名、code fence の language identifier は翻訳しない。

Exported な関数、type alias、interface、constant、class は包括的な JSDoc を必須にする。Internal code は、読み手がコードから判断しにくい目的、制約、edge case を中心に簡潔に書く。

## directive comment は対象外

tool directive comment は変更しない。

- Linter directive: `// eslint-disable-next-line`, `// biome-ignore lint/suspicious/noExplicitAny: reason`
- Formatter directive: `// prettier-ignore`
- Tool-specific comment: `// biome-ignore-all assist/source/organizeImports: reason`
- Type checker directive: `// @ts-expect-error`, `// @ts-ignore`

これらは各 tool が要求する syntax を持つため、JSDoc の形式に合わせて修正しない。

## @example の code fence

すべての `@example` は language identifier 付きの code fence を使う。

- `.js`: `javascript`
- `.ts`: `typescript`
- `.jsx`: `jsx`
- `.tsx`: `tsx`

**誤り: code fence がない**

```ts
/**
 * @example
 * const result = add(1, 2); // 3
 */
```

**誤り: language identifier がない**

```ts
/**
 * @example
 * ```
 * const result = add(1, 2); // 3
 * ```
 */
```

**正しい: language identifier がある**

```ts
/**
 * @example
 * ```typescript
 * const result = add(1, 2); // 3
 * ```
 */
```

## 関数

### すべての function で確認する項目

- 概要説明
- 各 parameter の `@param`
- 各 generic type parameter の `@template`
- `void` 以外の戻り値に対する `@returns`

Internal code では、parameter や戻り値が signature から十分に明らかな場合、冗長な tag を避けてもよい。

### exported function で必須の項目

- throw される error ごとの `@throws`
- 動作する code snippet を含む `@example`

### 任意の tag

- `@remarks`: 追加の背景、制約、設計意図
- `@see` / `@link`: 関連 API
- `@deprecated`: 非推奨理由と移行先

### 例

**誤り: 必要な tag がない**

```ts
export function clamp(min: number, max: number, value: number): number {
  if (min > max) {
    throw new RangeError(`min (${min}) > max (${max})`);
  }
  return Math.max(min, Math.min(max, value));
}
```

**正しい: 日本語で包括的に説明する**

```ts
/**
 * 数値を指定範囲内に丸める。
 *
 * @param min - 許容する最小値。
 * @param max - 許容する最大値。
 * @param value - 範囲内に丸める数値。
 * @returns `min` 以上 `max` 以下に丸められた値。
 * @throws {RangeError} `min` が `max` より大きい場合。
 *
 * @example
 * ```typescript
 * const center = clamp(5, 15, 10); // 10
 * const low = clamp(5, 15, 2); // 5
 * const high = clamp(5, 15, 20); // 15
 * ```
 */
export function clamp(min: number, max: number, value: number): number {
  if (min > max) {
    throw new RangeError(`min (${min}) > max (${max})`);
  }
  return Math.max(min, Math.min(max, value));
}
```

**誤り: generic function に @template がない**

```ts
/**
 * 配列の最初の要素を返す。
 *
 * @param items - 先頭要素を取得する配列。
 * @returns 先頭要素。
 */
function first<T>(items: T[]): T | undefined {
  return items[0];
}
```

**正しい: @template で型パラメータを説明する**

```ts
/**
 * 配列の最初の要素を返す。
 *
 * @template T - 配列要素の型。
 * @param items - 先頭要素を取得する配列。
 * @returns 先頭要素。空配列の場合は `undefined`。
 *
 * @example
 * ```typescript
 * const num = first([1, 2, 3]); // 1
 * const str = first(['a', 'b']); // 'a'
 * const none = first([]); // undefined
 * ```
 */
function first<T>(items: T[]): T | undefined {
  return items[0];
}
```

**誤り: void function に @returns がある**

```ts
/**
 * メッセージを console に出力する。
 *
 * @param message - 出力するメッセージ。
 * @returns 何も返さない。
 */
function log(message: string): void {
  console.log(message);
}
```

**正しい: void function では @returns を省く**

```ts
/**
 * メッセージを console に出力する。
 *
 * @param message - 出力するメッセージ。
 *
 * @example
 * ```typescript
 * log('Hello, world!');
 * ```
 */
function log(message: string): void {
  console.log(message);
}
```

## Object parameter と分割代入

object parameter を分割代入する場合は、parameter 本体と property を dot notation で説明する。

**誤り: object の property が説明されていない**

```tsx
/**
 * 複数の accordion をまとめる container component。
 *
 * @param props - Accordion group props。
 * @returns 描画された accordion group component。
 */
export function AccordionGroup({
  ref,
  children,
  className,
  variant = 'cozy',
  isDisabled,
  ...rest
}: AccordionGroupProps) {
  // ...
}
```

**誤り: 分割後の変数を個別 parameter として説明している**

```tsx
/**
 * 複数の accordion をまとめる container component。
 *
 * @param ref - Accordion group element の ref。
 * @param children - group 内に表示する accordion component。
 * @param className - 追加 CSS class。
 * @param variant - 表示密度。
 * @param isDisabled - すべての accordion を disabled にするか。
 * @returns 描画された accordion group component。
 */
export function AccordionGroup({
  ref,
  children,
  className,
  variant = 'cozy',
  isDisabled,
  ...rest
}: AccordionGroupProps) {
  // ...
}
```

**正しい: object parameter と property を dot notation で説明する**

```tsx
/**
 * shared configuration を持つ複数の accordion をまとめる。
 *
 * 複数 section を同時に開けるかなど、group 全体の挙動を制御する。
 *
 * @param props - Accordion group props。
 * @param props.ref - root div element への reference。
 * @param props.children - group 内に表示する accordion component。
 * @param props.className - 追加 CSS class。
 * @param props.variant - accordion の表示密度。`compact` または `cozy`。
 * @param props.isDisabled - group 内の accordion をすべて disabled にするか。
 * @returns Accordion group component。
 *
 * @example
 * ```tsx
 * <AccordionGroup variant="compact">
 *   <Accordion title="Section 1">Content 1</Accordion>
 *   <Accordion title="Section 2">Content 2</Accordion>
 * </AccordionGroup>
 * ```
 */
export function AccordionGroup({
  ref,
  children,
  className,
  variant = 'cozy',
  isDisabled,
  ...rest
}: AccordionGroupProps) {
  // ...
}
```

**正しい: nested object property**

```ts
/**
 * 設定値から database connection を初期化する。
 *
 * @param config - Database configuration options。
 * @param config.host - Database server hostname。
 * @param config.port - Database server port。
 * @param config.credentials - 認証情報。
 * @param config.credentials.username - Database username。
 * @param config.credentials.password - Database password。
 * @param config.pool - Connection pool settings。
 * @param config.pool.min - 最小 connection 数。
 * @param config.pool.max - 最大 connection 数。
 * @returns 初期化済み database connection。
 *
 * @example
 * ```typescript
 * const db = initDatabase({
 *   host: 'localhost',
 *   port: 5432,
 *   credentials: { username: 'admin', password: 'secret' },
 *   pool: { min: 2, max: 10 },
 * });
 * ```
 */
function initDatabase(config: DatabaseConfig): Database {
  // ...
}
```

## 型と interface

### 確認する項目

- 概要説明
- generic type parameter ごとの `@template`
- exported type/interface では public property の説明
- 制約、default、単位、状態遷移などがある場合は説明

**誤り: type に説明がない**

```ts
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

**正しい: type の意味と型パラメータを説明する**

```ts
/**
 * 成功または失敗のどちらかを表す operation result。
 *
 * @template T - 成功時の値の型。
 * @template E - 失敗時の error の型。
 */
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

**誤り: public interface の property 説明がない**

```ts
/**
 * API client の設定。
 */
interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}
```

**正しい: property を説明する**

```ts
/**
 * API client の設定。
 */
interface ApiConfig {
  /** API request の base URL。 */
  baseUrl: string;

  /** Request timeout milliseconds。 */
  timeout: number;

  /** 失敗した request を retry する回数。 */
  retries: number;
}
```

## 定数

constant には意味を説明する。値だけで用途が分からない場合は、単位、範囲、制約、default として使われる場面を書く。

**誤り: constant に説明がない**

```ts
const MAX_RETRIES = 3;
```

**正しい: 意味を説明する**

```ts
/**
 * 失敗した request の最大 retry 回数。
 */
const MAX_RETRIES = 3;
```

**正しい: 複雑な constant**

```ts
/**
 * API response で扱う HTTP status code の対応表。
 */
const STATUS_CODES = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  NOT_FOUND: 404,
} as const;
```

## class

### 確認する項目

- class の責務
- generic type parameter ごとの `@template`
- exported class では `@example`
- public constructor と public method の説明

**誤り: class に説明がない**

```ts
class Queue<T> {
  private items: T[] = [];

  enqueue(item: T): void {
    this.items.push(item);
  }

  dequeue(): T | undefined {
    return this.items.shift();
  }
}
```

**正しい: class と public method を説明する**

```ts
/**
 * FIFO 順で値を保持する generic queue。
 *
 * @template T - queue に格納する要素の型。
 *
 * @example
 * ```typescript
 * const queue = new Queue<number>();
 * queue.enqueue(1);
 * queue.enqueue(2);
 * console.log(queue.dequeue()); // 1
 * console.log(queue.dequeue()); // 2
 * console.log(queue.dequeue()); // undefined
 * ```
 */
class Queue<T> {
  private items: T[] = [];

  /**
   * queue の末尾に item を追加する。
   *
   * @param item - 追加する item。
   *
   * @example
   * ```typescript
   * queue.enqueue(42);
   * ```
   */
  enqueue(item: T): void {
    this.items.push(item);
  }

  /**
   * queue の先頭 item を取り出す。
   *
   * @returns 先頭 item。空の場合は `undefined`。
   *
   * @example
   * ```typescript
   * const item = queue.dequeue();
   * ```
   */
  dequeue(): T | undefined {
    return this.items.shift();
  }
}
```

**誤り: deprecated class に移行先がない**

```ts
/**
 * 旧認証 handler。
 */
class AuthHandler {
  authenticate(token: string): boolean {
    // ...
  }
}
```

**正しい: deprecated の理由と移行先を書く**

```ts
/**
 * 旧認証 handler。
 *
 * @deprecated 代わりに `AuthService` を使用する。この class は v3.0 で削除予定。
 * @see {@link AuthService}
 *
 * @example
 * ```typescript
 * // 使用しない:
 * const auth = new AuthHandler();
 *
 * // 代わりに使用する:
 * const auth = new AuthService();
 * ```
 */
class AuthHandler {
  /**
   * token で user を認証する。
   *
   * @param token - 認証 token。
   * @returns 認証に成功した場合は true。
   *
   * @deprecated 代わりに `AuthService.authenticate()` を使用する。
   */
  authenticate(token: string): boolean {
    // ...
  }
}
```

## よくある edge case

- Overload: overload signature 全体の目的を 1 つの docblock にまとめ、必要に応じて複数の `@example` を書く
- Callback parameter: callback の parameter は `@param options.onChange` のように dot notation で説明する
- Builder pattern: chain した使い方を `@example` に入れる
- Event emitter: event name、payload shape、発火条件を説明する
- Utility type: 変換前後の型の意味を自然言語で説明し、複雑な conditional type の HOW を長く書きすぎない
