# Playwright 撮影ガイド

エンドユーザー向けマニュアルのためにスクリーンショットを撮る前に、このガイドを確認する。

## 1. 何を撮るべきかを先に決める

次のどれかを説明するために必要な画面だけを撮る。

- どこから始めるか
- どの UI をクリックまたは入力するか
- 成功状態がどう見えるか
- 重要な警告や確認がどう表示されるか
- 操作後に何が変わるか

本文の内容をただ繰り返すだけの画像は撮らない。

## 2. 最小限の撮影計画を立てる

アプリを開く前に、必要な画面を箇条書きにする。

例:

- 対象機能のトップ画面
- 設定画面
- 確認画面
- 保存後の成功状態

これにより不要な撮影を減らし、文書全体の一貫性を保てる。

## 3. 安定した状態を撮る

UI の読み込みが終わってから撮影する。

良い対象:

- 見出しが表示された読み込み完了ページ
- 主要項目が見えているフォーム
- 最終状態まで開いた確認ダイアログ
- 成功メッセージが確認できる保存後の画面

避ける対象:

- ローディング中のスピナー
- 途中のアニメーション
- 主題でない一時的なドロップダウン開閉
- 消えやすい toast を慌てて撮った不安定な画面

## 4. ユーザー向けの範囲だけを写す

画像は、利用者が理解に必要な範囲だけを写す。

優先する内容:

- 関係するコンテンツ領域
- 位置関係が分かる程度の周辺 UI
- 現在位置の把握に必要なナビゲーション

避ける内容:

- ブラウザのタブやブックマークバー
- OS の UI
- 開発者ツール
- 無関係なサイドバー
- 管理者専用 UI が主題でないのに写り込む構成

## 5. 安全なデータを使う

公開向け、または一般ユーザー向けの文書では、実在の個人情報や秘密情報を写さない。

避けるもの:

- 実在のメールアドレス
- API キーやトークン
- 支払い情報
- 私的情報を含む内部 ID
- 実在の顧客名や個人名

安全なデータが用意できない場合は、空状態やダミーデータで撮り直すか、その画像を使わない。

## 6. 文書全体で一貫性を保つ

モバイル画面が主題でない限り、1つのマニュアル内では同じ表示条件を保つ。

推奨:

- 同じ desktop viewport を使う
- 同じ zoom level を使う
- ダークモードが主題でない限り同じテーマを使う
- 役割差分を説明する場合を除き、同じ権限ロールを使う

標準の撮影設定は `apps/docs/scripts/manual-screenshot-preset.mjs` を使う。

```js
import { chromium } from 'playwright';
import {
	createManualScreenshotPage,
	manualScreenshotOptions,
	waitForManualScreenshotReady
} from './manual-screenshot-preset.mjs';

const browser = await chromium.launch({ headless: true });
const { context, page } = await createManualScreenshotPage(browser);

await page.goto('http://127.0.0.1:5174/admin/contracts');
await waitForManualScreenshotReady(page, {
	locator: page.getByRole('heading', { name: '契約', level: 1 })
});

await page.screenshot({
	path: 'apps/docs/static/manuals/example/01-example.png',
	...manualScreenshotOptions
});

await context.close();
await browser.close();
```

標準設定は `locale: 'ja-JP'`、`timezoneId: 'Asia/Tokyo'`、`viewport: { width: 1440, height: 960 }`、`deviceScaleFactor: 2`、`scale: 'device'`、ライトモード、アニメーション無効を使う。ページ全体が必要な画像だけ `manualFullPageScreenshotOptions` を使う。

## 7. 撮影後に必要最小限の編集をする

必要なら、撮影後に軽い画像編集を行ってよい。GIMP が使えるなら使ってよいが、必須ではない。

目的は次の3つに限る。

- 主題だけを見せるためのトリミング
- 文書全体の読みやすさをそろえるためのリサイズ
- 操作対象 UI を見失いにくくするための赤枠強調

守ること:

- 元の UI の文言、状態、順序、色の意味を改変しない
- 赤枠は必要なときだけ使う
- 1枚の画像で強調する UI は原則 1〜2 箇所までに抑える
- 赤枠は細い単純な矩形を基本とし、過剰な装飾や説明の描き込みはしない
- トリミングしても、利用者が現在位置を理解するための最低限の文脈は残す

編集後に、強調がなくても本文だけで手順を追えるかを確認する。

## 8. 並び替えやすいファイル名にする

連番と短い step slug を使う。

例:

- `01-open-settings.png`
- `02-enter-api-key.png`
- `03-confirm-save.png`
- `04-success-state.png`

## 9. 手順の直後に画像を置く

画像は、対応する番号付き手順のすぐ下に置く。

良い例:

```markdown
2. `通知設定` を開きます。

   ![通知設定画面](/manuals/notifications/02-open-notification-settings.png)
```

悪い例:

- 画像だけを末尾にまとめる
- 手順との対応が分からない画像
- ファイル名だけを並べて本文で説明しない構成

## 10. 撮らない判断もする

次の場合は、画像を付けない。

- 本文だけで十分に伝わる
- 安全に撮影できない
- 機密情報が写る
- すでに前の画像で十分に説明できる

## 11. 保存前の最終確認

各画像について次を確認する。

- 本文の手順と合っているか。
- 重要な UI が見えているか。
- 機密情報や個人情報が露出していないか。
- 編集で UI の意味を変えていないか。
- 赤枠が必要以上に多くないか。
- ファイル名が分かりやすいか。
- 利用者にとって本当に役立つか。

1つでも満たせない場合は、撮り直すか削除する。
