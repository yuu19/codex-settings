# RoleTray Chrome Web Store Inputs

Use these values for the RoleTray Chrome Web Store draft unless the repo or user gives a newer value.

## Item Identity

- Developer Dashboard publisher ID: `401a5388-debb-4878-ae59-4df40c823fba`
- Extension item ID: `aeafpambpfjdifaihjlfejfdjeonjohp`
- Item name: `RoleTray`
- Status during preparation: `ドラフト`
- ZIP path: `apps/extension/.output/roletrayextension-0.1.0-chrome.zip`

## Listing

- Package title: `RoleTray`
- Package summary: `Save job posts and track application status from the browser.`
- Category: `ワークフローと計画`
- Language: `日本語`
- Homepage URL: `https://roletray.com`
- Support URL: `https://roletray.com`
- Adult content: off

Description:

```text
RoleTrayは、求人ページを見ながらChromeのサイドパネルまたはポップアップから求人情報を保存し、応募ステータスを追跡できるChrome拡張機能です。

主な機能:
- 求人ページのタイトル、会社名、URLなどを読み取り、保存フォームに反映
- サイドパネルから求人をすばやく保存
- 応募状況、メモ、タグ、勤務地、給与などを整理
- RoleTrayアカウントでログインするとWebダッシュボードと同期
- ローカル保存でも利用可能

保存した求人情報は、本人のブラウザ内またはログイン時のRoleTrayアカウントに保存されます。求人応募の進捗管理を、求人サイトを横断して一元化できます。
```

## Assets

- Shop icon: `apps/extension/public/icons/icon-128.png`
- Screenshot: `apps/extension/store-assets/screenshot-1280x800.png`
- Small promo tile: `apps/extension/store-assets/promo-small-440x280.png`
- Optional marquee tile: not prepared

Chrome Web Store screenshot/tile uploads must be JPEG or 24-bit PNG with no alpha. Verify dimensions with `identify`.

## Privacy

- Privacy policy URL: `https://roletray.com/privacy`
- Public contact email: `privacy@roletray.com`
- Remote code: `いいえ、リモートコードを使用していません`
- Leave remote-code reason blank when "No" is selected.

Single purpose:

```text
求人ページから求人情報を保存し、応募ステータス・メモ・タグ・期限などを整理して、応募活動をRoleTray内で管理できるようにすること。
```

Permission reasons:

```text
activeTab:
ユーザーが現在開いている求人ページを明示的に保存するときに、現在のタブのタイトル、URL、ページ内の求人情報を取得して保存フォームに反映するため。

storage:
ログイン前でも求人情報、タグ、同期状態をこのChromeのローカル保存に保持し、ユーザーが後から確認・編集できるようにするため。

tabs:
現在のタブのURLとタイトルを読み取り、サイドパネルまたはポップアップから保存対象ページを判定するため。

sidePanel:
求人ページを開いたまま、サイドパネルで保存フォームや保存済み求人を表示・編集できるようにするため。

ホスト権限:
ユーザーが任意の求人サイトで保存操作を行えるよう、求人ページの本文、構造化データ、URL、タイトルを読み取り、保存フォームに反映するため。読み取りは保存操作の文脈に限定します。
```

Data use categories to check:

- 個人を特定できる情報
- 認証に関する情報
- ウェブ履歴
- ウェブサイトのコンテンツ

Required declarations to check:

- 私は、承認されている以外の用途で第三者にユーザーデータを販売、転送しません
- 私はアイテムの唯一の目的と関係のない目的でユーザーデータを使用または転送しません
- 私は信用力を判断する目的または融資目的でユーザーデータを使用または転送しません

## Worker Origin

Production `apps/worker/wrangler.jsonc` should contain:

```jsonc
"EXTENSION_ORIGIN": "chrome-extension://aeafpambpfjdifaihjlfejfdjeonjohp"
```

Production should only trust the fixed extension origin. Dynamic `chrome-extension://...` origins should be limited to local development or E2E.

## Pre-Submit Stop Point

Before the user submits, verify:

- `審査のため送信` is enabled.
- No visible "公開できません" error list remains.
- Worker production deploy is complete and `/health` returns `200`.
- Git status is clean and pushed if the user requested commit/push.

Stop there unless the user explicitly asks Codex to submit the item.
