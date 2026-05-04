---
name: playwright-e2e-test-writer
description: Build and extend Playwright E2E tests for TypeScript web apps, especially SvelteKit E2E flows, using Page Object Model structure, setup helpers, fixtures, database isolation, and @playwright/test assertions. Use when adding Playwright E2E tests, creating .spec.ts or .e2e.ts coverage, introducing Playwright config, test setup, fixtures, Page Object Model classes, authentication helpers, database isolation helpers, or adapting Svelte Society style tests.
---

# Playwright E2E Test Writer

## 概要

Playwright E2E は、再現性、分離性、拡張しやすさを優先して実装する。まず対象プロジェクトの既存規約を読み取り、その上で Svelte Society の `tests/` 構成を参照パターンとして適用する。spec はユーザーフローと検証に集中させ、Page Object は UI 操作、helpers は環境準備、fixtures は安定したテストデータを担当する。

必要に応じて次の参照を読む:

- `references/svelte-society-e2e-patterns.md`: 参照元の構成、POM、database isolation、auth helper、fixture、commands、代表 spec の書き方を確認するとき。
- `references/project-adaptation.md`: SvelteKit、Vite、Cloudflare Workers、Bun、pnpm、monorepo、backend/API、database、authentication の差分に合わせて基盤を追加・変更するとき。

## Workflow

1. 既存の Playwright 基盤を検出する:
   - `playwright.config.*`、`@playwright/test`、`tests/e2e`、`e2e`、`.spec.ts`、`.e2e.ts`、page objects、helpers、fixtures、setup、package scripts を探す。
   - 既存の `testDir`、`testMatch`、package manager、dev server command、port、browser projects、reporter、retries、命名規則は、明示的な移行依頼がない限り維持する。

2. 対象 app/package を特定する:
   - monorepo では app-local `package.json`、framework config、routes、既存 tests を読んでから追加場所を決める。
   - 新規 E2E ファイルは既存 E2E root の近くに置く。未整備なら、対象 app または repo root に package scripts と整合する最小構成を置く。

3. product code から対象フローを理解する:
   - 依頼されたフローに関係する route、page、component、API を読む。
   - 安定した user-facing assertions、必要な test data、auth state、external services、cleanup/isolation 要件を洗い出す。
   - `data-testid` は role locator や accessible name では不十分または不安定なときだけ追加する。

4. 実装レベルを選ぶ:
   - 既存基盤がある場合: config を書き換えず、spec、page object、helper、fixture を追加または拡張する。
   - 未整備の場合: 依頼フローに必要な最小の Playwright setup を追加し、backend/test-data の前提は必要最小限の code comment または script に残す。

5. POM を標準として実装する:
   - 共通 navigation、URL、共通 element helper は `BasePage` に置く。
   - 画面固有の操作と検証 helper は page object に置く。
   - spec は user flow、setup、高価値な assertions に集中させる。
   - sleep ではなく `expect(locator)` の web-first assertions と Playwright auto-waiting を使う。

6. ローカルで検証する:
   - まず変更対象 spec の最小 Playwright command を実行し、必要に応じて lint/type/test を追加実行する。
   - browser binaries や dev-server dependencies が不足している場合は、失敗した正確な command と blocker を報告する。

## Baseline Structure

E2E 基盤がない場合でも、依頼フローに必要なものだけ追加する:

```text
tests/
  e2e/
    <area>/<flow>.spec.ts
  pages/
    BasePage.ts
    <FlowPage>.ts
    index.ts
  helpers/
    auth.ts
    database-isolation.ts
  fixtures/
    test-data.ts
  setup/
    global-setup.ts
    global-teardown.ts
```

root は `tests/`、`apps/web/tests/`、package-local path など既存構成に合わせる。baseline にあるという理由だけで未使用 folder を作らない。

## Playwright Config

`playwright.config.ts` を追加・変更するときは保守的に扱う:

- `testDir` と `testMatch` は選んだ file layout に合わせる。
- `use.baseURL` は app の local server に合わせる。
- `webServer` は対象プロジェクトの package manager と app command を使う。
- 実用的な初期値として `forbidOnly: !!process.env.CI`、CI retries、failure traces/screenshots/videos、単一 Chromium project を検討する。
- `globalSetup`/`globalTeardown` は test data、database、service setup が必要な場合だけ追加する。
- secret、production URL、production database、実 third-party credentials を hardcode しない。

## Test Style

新規 spec はこの形を基準にし、実際の directory depth と setup 要件に合わせて調整する:

```typescript
import { expect, test } from '@playwright/test'
import { setupDatabaseIsolation } from '../../helpers/database-isolation'
import { LoginPage } from '../../pages'

test.describe('login flow', () => {
  test.beforeEach(async ({ page }) => {
    await setupDatabaseIsolation(page)
  })

  test('allows an owner to sign in', async ({ page }) => {
    const loginPage = new LoginPage(page)
    await loginPage.goto()
    await loginPage.signInAsOwner()
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible()
  })
})
```

database/auth helper は、そのフローで必要な場合だけ呼ぶ。

## Selectors

selector は次の順で選ぶ:

1. UI が安定した name を持つ場合は `getByRole`、`getByLabel`、`getByPlaceholder` などの accessible locators。
2. 複雑な widget、繰り返し card、icon-only control、生成 content、不安定な copy には `getByTestId`。
3. list や card の検証では scoped locator と `filter({ hasText })`。
4. より良い semantics がない構造要素には CSS selector。
5. XPath と brittle な text-only selector は最後の手段。

必要な要素に安定 selector がない場合は、component に最小の `data-testid` を追加し、domain-specific な名前にする。

## Data, Auth, And Isolation

persistence や authentication があるプロジェクトでは次を守る:

- ad hoc な inline data より、決定的な test users と fixtures を使う。
- fixture data は中央集約し、可能なら typed にする。
- third-party auth provider は、project-supported test hook、session creation、storage state、cookie など実装に合う方法でだけ bypass する。
- parallel execution を有効にするなら、database name、tenant ID、seed namespace は test file、worker、test info などから導出する。
- Svelte Society の cookie name、session schema、database filename、Stripe ID、seed record を決め打ちしない。対象 project を読んで matching helper を実装する。
- cleanup は SQLite WAL/SHM、temporary uploads、queued jobs、per-test tenant records など副産物も対象にする。

## Assertions And Reliability

- URL、visible content、enabled/disabled state、persisted data、API-visible state、notification messages、navigation など user-observable outcomes を検証する。
- eventual consistency には `await expect(locator).toBeVisible()`、`toHaveText`、`toHaveURL`、`toHaveValue`、`expect.poll`、`toPass` を使う。
- `waitForTimeout` は避け、具体的な UI state または application/network state を待つ。
- serial mode は安全に isolation できない flow だけに使い、短い comment で理由を書く。
- `test.only`、意図しない `test.skip`、debug logs、generated screenshots、Playwright reports を残さない。

