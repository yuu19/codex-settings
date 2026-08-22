# Chrome Web Store Inputs Reference

This file is an example and RoleTray preset. For any non-RoleTray extension, collect equivalent values from that repository and user instructions instead of copying these values.

## Generic Input Checklist

Collect these fields for any Chrome extension:

- Extension name
- Package summary
- Detailed description
- Category and language
- Homepage URL
- Support URL
- Privacy policy URL
- Public publisher contact email
- Built ZIP path
- Extension item ID after draft upload
- Store asset paths: 128x128 icon, screenshots, optional promotional tiles
- Single-purpose statement
- Permission reasons for every permission and host permission
- Data-use categories that match the implementation
- Remote-code declaration
- Backend/web origin settings that must allow `chrome-extension://<id>`

Use repository evidence for all values. For permissions and data use, inspect manifest, content scripts, background/service worker code, API/auth clients, storage usage, and privacy policy.

## Generic Pre-Submit Stop Point

Before the user submits, verify:

- `審査のため送信` is enabled.
- No visible "公開できません" error list remains.
- Any backend or web app that depends on the extension ID has been updated and deployed.
- Production health checks pass where applicable.
- Git status is clean and pushed if the user requested commit/push.

Stop there unless the user explicitly asks Codex to submit the item.

## RoleTray Preset

Use these values only for the RoleTray Chrome Web Store draft unless the repo or user gives a newer value.

### Item Identity

- Developer Dashboard publisher ID: `401a5388-debb-4878-ae59-4df40c823fba`
- Extension item ID: `aeafpambpfjdifaihjlfejfdjeonjohp`
- Item name: `RoleTray`
- Status during preparation: `既存アイテムの更新準備`
- ZIP path: `apps/extension/.output/roletrayextension-0.1.4-chrome.zip`

### Listing

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
- RoleTrayアカウントでログインし、Webダッシュボードとクラウド同期
- 応募期限の前日18:00と当日9:00にアプリ内通知・ブラウザ通知でリマインド

保存した求人情報は、本人のRoleTrayアカウントに紐づくRoleTrayクラウドに保存されます。求人応募の進捗管理を、求人サイトを横断して一元化できます。
```

### Assets

- Shop icon: `apps/extension/public/icons/icon-128.png`
- Screenshot: `apps/extension/store-assets/screenshot-1280x800.png`
- Small promo tile: `apps/extension/store-assets/promo-small-440x280.png`
- Optional marquee tile: not prepared

Chrome Web Store screenshot/tile uploads must be JPEG or 24-bit PNG with no alpha. Verify dimensions with `identify`.

### Privacy

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
ユーザーが現在開いている求人ページを明示的に保存または再読み込みするときに、現在のタブのURL、タイトル、ページ内の求人候補情報を保存フォームに反映するため。

alarms:
応募期限通知の確認処理を定期的に実行し、配信対象の通知をRoleTray APIから取得するため。

notifications:
応募期限の前日18:00と当日9:00に、Chromeのブラウザ通知としてリマインドを表示するため。

storage:
拡張機能用APIキー、クラウド連携状態、連携解除状態など、RoleTray APIへ安全に接続するための最小限の拡張機能状態をChrome local storageに保持するため。

scripting:
ユーザーが保存操作を行った現在のタブに限定して、求人ページのmeta情報、JSON-LD、URL、タイトル、勤務地・給与・雇用形態・応募期限などの候補情報を解析するため。

sidePanel:
求人ページを開いたまま、サイドパネルで保存フォームや保存済み求人を表示・編集できるようにするため。

ホスト権限:
`https://api.roletray.com/*` に接続し、ログイン連携、求人、タグ、応募履歴、通知、通知設定をRoleTrayクラウドと同期するため。
```

Data use categories to check:

- 個人を特定できる情報
- 認証に関する情報
- ウェブ履歴: ユーザーが保存した求人URL、掲載元ドメイン、関連する保存日時を扱う場合
- ウェブサイトのコンテンツ: ユーザーが保存操作を行った求人ページのURL、タイトル、meta情報、JSON-LD、勤務地・給与・雇用形態・応募期限などを抽出する場合

Notification data to disclose in the privacy policy and data-use notes:

- 応募期限通知の設定
- 通知予定、送信、既読、非表示、キャンセルの状態
- Chrome拡張によるブラウザ通知の配信成功または失敗の状態

Required declarations to check:

- 私は、承認されている以外の用途で第三者にユーザーデータを販売、転送しません
- 私はアイテムの唯一の目的と関係のない目的でユーザーデータを使用または転送しません
- 私は信用力を判断する目的または融資目的でユーザーデータを使用または転送しません

### Worker Origin

Production `apps/worker/wrangler.jsonc` should contain:

```jsonc
"EXTENSION_ORIGIN": "chrome-extension://aeafpambpfjdifaihjlfejfdjeonjohp"
```

Production should only trust the fixed extension origin. Dynamic `chrome-extension://...` origins should be limited to local development or E2E.
