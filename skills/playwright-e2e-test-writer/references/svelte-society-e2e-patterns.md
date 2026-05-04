# Svelte Society E2E Patterns

参照元: GitHub `svelte-society/sveltesociety.dev`

- `tests/README.md`
- `playwright.config.ts`
- `tests/e2e/public/search.spec.ts`
- `tests/pages/BasePage.ts`
- `tests/helpers/database-isolation.ts`
- `tests/helpers/auth.ts`
- `tests/setup/global-setup.ts`
- `tests/setup/global-teardown.ts`
- `tests/fixtures/test-data.ts`

このファイルは参照元の要約であり、source project の code を丸ごと移植するためのものではない。

## Structure

Svelte Society は Playwright の責務を明確に分けている:

```text
tests/
  e2e/
    public/
    auth/
    content/
    admin/
  pages/
    BasePage.ts
    HomePage.ts
    ContentListPage.ts
    LoginPage.ts
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

spec は feature area ごとに置く。Page Object Models は `tests/pages`、cross-cutting setup/auth/isolation は `tests/helpers`、決定的な seed data は `tests/fixtures` が担当する。

## Config Pattern

Playwright config の特徴:

- `testDir: './tests'`
- TypeScript の spec/test file matching
- `fullyParallel: true`
- CI-only `forbidOnly` と retries
- failure traces、screenshots、videos
- main suite は単一 Chromium project
- app を build/preview する `webServer`
- local DB、auth、email、Stripe、seeding 用の test-mode environment variables
- isolated test database 用の `globalSetup` と `globalTeardown`

適用時は、対象 project の command、port、env 名、storage technology を優先する。

## Page Object Model

`BasePage` は共通 page behavior を持つ:

- constructor で Playwright `Page` を受け取る。
- 汎用 `goto(path)` を持つ。
- current URL/title helper を持つ。
- header/footer/nav など共通 locator を持つ。
- login/home/reload など共通 action を持つ。

個別 page object はこの base を継承または compose し、search、submit、filter、edit、expect content など domain action を公開する。spec は user flow と assertion を中心にし、低レベル locator の重複を避ける。

## Database Isolation

参照元は seeded base SQLite database を 1 つ用意し、spec file ごとに isolated copy を作る。helper が browser cookie を設定し、application がその cookie に応じた database へ request を route する。identifier は呼び出し元 `.spec.ts` path から導出され、setup/teardown と共有される。

移植できる考え方:

- 高コストな seed state は 1 回だけ準備する。
- spec file または worker ごとに isolated storage namespace を持たせる。
- test-only mechanism で app request をその namespace に route する。
- runtime 作成が遅い、または flaky になる場合は global setup で pre-create する。
- teardown で generated database files、WAL files、SHM files を消す。

cookie name、database filename、server routing は対象 app に合わせる。参照元の値を決め打ちしない。

## Auth Helper

参照元は external OAuth を通さず、deterministic fixture user の session cookie を直接設定する。helper は cookie 設定後に cookie を読み戻し、silent failure を早期に検出する。

適用時の判断:

- project-supported test login route、storage state、session factory、direct cookie のうち、app が正式に認識する方法を使う。
- owner/admin/member/viewer など role は明示し、可能なら union type にする。
- routine E2E では real OAuth provider、real email link、real payment credentials を使わない。

## Fixtures And Test Data

fixture data は users、roles、content、tags、saved items、sponsors、time-derived helper values などを typed module に集約している。spec は inline data を都度作らず、named records を参照する。

対象 domain では、organizations、reservations、billing plans、staff members、resources、customers、invoices などを stable ID と ownership が分かる fixture として定義する。

## Representative Spec Style

search spec から得られる pattern:

- behavior ごとに `test.describe` を分ける。
- isolation は `beforeEach` で呼ぶ。
- 大きな navigation/search action は page object に寄せる。
- application-specific widget には `getByTestId` を使う。
- visibility、URL change、value、focus、list contents は Playwright web assertions で検証する。
- async suggestions など複数の valid state に落ち着き得る箇所では `toPass` を使う。
- focus と async suggestion loading が干渉する group だけ serial mode にする。

新規 coverage でも、setup は上部に集め、繰り返し操作は page object に寄せ、assertion は user-visible outcome の近くに置く。

## Commands

参照元は通常実行、UI mode、headed、debug、single-file、grep の command を持つ。同じ考え方を対象 project の package manager に合わせて用意する:

- full E2E suite
- authoring 用 UI mode
- local debugging 用 headed mode
- 必要時の debug mode
- quick iteration 用の file/grep command

`bun`、`pnpm`、`npm`、package filters は対象 repository の既存規約に合わせる。E2E 追加のために package manager を増やさない。

