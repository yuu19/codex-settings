# Project Adaptation Guide

Svelte Society の pattern を別 project に適用する前、または Playwright infrastructure を追加する前に読む。

## Existing Foundation First

編集前に次を確認する:

- package manager と workspace shape
- app-local `package.json` scripts
- `playwright.config.*`
- Vite/SvelteKit config
- route と component の場所
- backend/API test helpers
- database/migration/seed commands
- auth/session implementation
- CI expectations

E2E 基盤がある場合は拡張する。依頼上必要でない限り、config replacement、test root 移動、file rename は行わない。

## SvelteKit And Vite

SvelteKit/Vite app では次を優先する:

- 既存の dev/preview command を使う。repo が短時間で build できるなら production preview の E2E を検討する。
- `baseURL` は既存 app server port に合わせる。
- accessible locator が十分安定しない箇所だけ Svelte component に test ID を追加する。
- SSR/client race を前提にせず、navigation 後は visible UI state を assert する。
- form actions、load functions、remote functions、server routes が関係する場合は、実用的な範囲で UI result と persisted/API-visible state の両方を確認する。

## Cloudflare Workers And Hono

Workers/Hono backend が関係する場合:

- E2E 対象が SvelteKit のみか、local Worker も含むか、両方かを決める。
- 既存の local command を使う: `wrangler dev`、package scripts、repo-specific worker harness など。
- test env は production bindings と分ける。
- D1 では既存 migration tooling に合わせ、isolated database、per-test tenant、transaction-reset helper を選ぶ。
- R2、queues、durable objects、email、Stripe、Resend は fake/test bindings または explicit test-mode endpoints を優先する。

## Monorepos

monorepo では:

- config と tests は app script が期待する場所に置く。
- package filters は既存規約がある場合だけ使う。
- shared E2E helpers は複数 app が既に共有 test utility を使う場合だけ最小 shared package に置く。
- 対象が 1 package のときに root script で全 app を走らせない。

## Package Manager

repository に合わせる:

- pnpm: 既存規約なら `pnpm --filter <pkg>` を使う。
- Bun: app が既に Bun を使っているなら Bun command を維持する。
- npm/yarn: 既存 script style に合わせる。

E2E 変更の一環として lockfile を増やしたり package manager を切り替えたりしない。

## Minimal New Infrastructure

新規追加時は最小構成から始める:

- 未導入なら `@playwright/test` dev dependency。
- `playwright.config.ts`。
- smoke または依頼された flow の spec 1 つ。
- repeated interactions がある、または flow が非自明な場合だけ page object。
- 実 setup 要件がある場合だけ helpers/fixtures。
- `test:e2e`、任意で `test:e2e:ui`、`test:e2e:headed`、`test:e2e:debug`。

必要になるまでは global setup、teardown、fixture factories、database isolation を作らない。

## Database Isolation Choices

storage model に応じて選ぶ:

- SQLite/D1 local file: seeded base DB を spec/worker ごとに copy する、または migration から fresh DB を作る。
- Postgres/MySQL: per-worker schemas、per-test transactions、truncate-and-seed、disposable containers から既存 tooling に合うものを選ぶ。
- multi-tenant apps: per-test tenant/organization を作り cleanup する。
- external SaaS state: service calls を mock/fake する、または unique ID 付き test-mode API を使う。

parallel tests には deterministic isolation が必要。isolation できない場合だけ対象 `describe` を serial mode にし、理由を短く書く。

## Authentication Choices

最も壊れにくい supported path を選ぶ:

- setup project で生成した storage state
- test-only login route
- database に対する direct session factory
- cookie schema が安定して理解済みの場合だけ direct cookie
- login flow 自体を検証する場合だけ UI login

別 project の auth cookie 名や session row を hardcode しない。

## Assertions

user または API boundary から behavior を assert する:

- URL と route changes
- headings、labels、table rows、cards、empty states、validation messages
- enabled/disabled controls
- UI/API から取得できる persisted data
- mocked service calls または local test-mode event records

user-visible signal がない場合を除き、internal implementation details は assert しない。

## Verification

次の順で実行する:

1. 変更した spec の narrow Playwright command。
2. infrastructure を変更した場合は broader E2E command。
3. 触った files に必要な typecheck/lint/test。

Playwright browsers が不足する場合は repo-appropriate install command を実行または報告する。dev server が env/bindings 不足で起動できない場合は、不足 prerequisite を具体的に報告する。

