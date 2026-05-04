---
name: saas-user-manual-screenshot-writer
description: create or update japanese end-user markdown manuals with screenshots for saas features by reading existing docs-app manuals, repository docs, and relevant backend or api code, then navigating the product with playwright mcp or playwright cli to capture accurate user-facing screenshots. use when chatgpt should produce apps/docs/src/routes/manuals/ markdown pages with step-by-step images for onboarding, settings, billing, integrations, forms, account flows, or other user workflows from a project repository.
---

# SaaS User Manual Screenshot Writer

## Overview

既存の `apps/docs/src/routes/manuals/` とリポジトリ内の関連 docs、backend / API code を読み、機能のユーザー向け挙動を確認したうえで、Playwright で実際の画面を操作し、スクリーンショット付きの日本語マニュアルを `apps/docs/src/routes/manuals/` 配下に作成または更新する。

既存ドキュメントの用語を優先し、挙動は実装と実画面で裏取りする。画面名、ボタン名、権限、スクリーンショットを推測で補わない。

## Workflow

1. 依頼文から対象機能、想定読者、出力先ファイルを特定する。
2. `apps/docs/src/routes/manuals/` 配下の既存マニュアルを先に読み、用語、章立て、リンク形式、画像配置ルールを把握する。必要に応じて `docs/` 配下の関連資料も読む。
3. 関連する backend / API code を読み、ユーザーに見える挙動、前提条件、状態遷移、制約を確認する。
4. 撮影計画を短く作る。どの画面が必要か、どの手順に画像が必要か、どの状態を見せるべきかを決める。
5. Playwright で実際の画面を開き、安定したユーザー向けスクリーンショットを取得する。
6. 必要な場合だけ、GIMP などの画像編集ツールで最小限の後処理を行う。主にトリミング、リサイズ、操作対象 UI の赤枠強調を扱う。
7. 画像は docs app の既存規約に合わせて保存する。規約がなければ `apps/docs/static/manuals/<topic-slug>/` を使う。
8. `apps/docs/src/routes/manuals/` 配下の Markdown を作成または更新し、適切な手順の直後に画像を埋め込む。
9. 仕上げに、用語統一、画像の対応関係、推測表現の有無、機密情報の写り込み、編集による誤解の有無を見直す。

## Source Priority

情報源は次の優先順で扱う。

1. `apps/docs/src/routes/manuals/` 配下の既存マニュアル
2. `docs/` 配下や各 app の README など、関連する repository docs
3. 対象機能に直接関係する backend / API code
4. 共有モデル、バリデーション、定数、ユーザー向けメッセージ、通知文言
5. 仕様の補助としてのテストコード
6. Playwright で確認した実画面

TODO コメント、死んだコード、古い migration、実装と矛盾する古い docs は一次情報として扱わない。

## Browser Automation Rule

環境で利用できるなら Playwright MCP を優先する。利用できない場合は Playwright CLI にフォールバックする。

優先順は次のとおり。

1. 認証済みブラウザセッションを利用できる Playwright MCP
2. ローカル環境、staging 環境、指定 URL に対する Playwright CLI
3. どちらも使えない場合は制約を明示して停止する

実際に撮影していない画面を撮影したことにしない。

## Authentication and Environment

認証が必要な画面は、既存の認証済みセッションがある場合、またはユーザーが明示的に安全なログイン方法を提供した場合にのみ操作する。

- 資格情報を推測しない。
- 認証を回避しない。
- API キー、トークン、個人情報、支払い情報などの秘密情報が見える画面は使わない。
- エンドユーザー向け文書では、サンプルデータ、空状態、検証用の安全なアカウントを優先する。

安全にログインできず撮影が進められない場合は、その制約を明確に説明して停止する。ユーザーが明示的に許可したときだけ、画像なしの本文ドラフトに切り替える。

## Screenshot Rules

撮影前に `references/playwright-capture-guide.md` を読む。

以下を守る。

- 意味のあるユーザー向け手順だけを撮影する。すべてのクリックを撮らない。
- 現在の説明を裏付ける範囲だけを写す。
- ローディング中ではなく、安定して読み込み終わった状態を優先する。
- モバイルやタブレット表示が主題でない限り、1つのマニュアル内では同じ viewport を保つ。
- ブラウザ chrome、ブックマークバー、開発者ツール、無関係なナビゲーション、デバッグ表示を写さない。
- 機密値が写る場合は再撮影または安全な状態へ切り替える。
- ノイズが多い画面は説明でごまかさず、より良い状態で撮り直す。

## Screenshot Post-Processing

撮影後の画像編集は、理解を助けるための最小限にとどめる。

- 必要に応じて GIMP を使ってよい。GIMP が使えない場合は同等の軽い編集手段でもよいし、編集なしで進めてもよい。
- トリミングは、操作対象と前後関係が分かる範囲を残してノイズを減らす目的で行う。
- リサイズは、文書内で読みやすさと一貫性を保つ目的で行う。
- 赤枠は、ユーザーが実際に操作する UI が密集していて、本文だけでは見失いやすい場合に限って使う。
- 赤枠で囲う対象は、原則としてその手順で操作する UI 1〜2 箇所までに絞る。
- 赤枠は細く単純な矩形を基本とし、過剰な装飾、吹き出し、説明テキストの描き込みは避ける。
- 編集で UI ラベル、状態、並び順、表示内容を改変しない。編集は強調と読みやすさの向上に限る。
- 赤枠を足したことで誤った操作対象に見える場合は、その画像を使わず撮り直す。

## Output Structure

出力は `apps/docs/src/routes/manuals/` 配下の Markdown と、その文書から参照される `apps/docs/static/manuals/` 配下の画像ファイルとする。

既存の repository 規約があればそれに従う。規約がない場合の既定値は次のとおり。

- Markdown: `apps/docs/src/routes/manuals/<topic-slug>/+page.md`
- 画像: `apps/docs/static/manuals/<topic-slug>/01-<step-slug>.png`, `02-<step-slug>.png` のような連番付きファイル名

本文構成は `references/manual-template-with-screenshots.md` を基本にする。

## Writing Rules

- 出力言語は日本語。
- 想定読者は一般ユーザーであり、社内開発者ではない。
- 文体は落ち着いたサポートドキュメント調にする。宣伝調にしない。
- 段落は短くし、操作説明は手順中心で書く。
- 操作は番号付きリストで書く。
- UI ラベルは、実画面または信頼できる docs で確認できた場合のみバッククォートで囲んで正確に書く。
- 危険な操作や制約は、該当手順の後ろではなく前に書く。
- 内部実装の詳細は出さず、ユーザーが理解・操作に必要な内容だけを書く。

## Screenshot Embedding Rules

スクリーンショットはギャラリーとして末尾にまとめず、対応する手順の直後に配置する。

Markdown の標準画像構文を使い、alt text は短く実用的にする。

例:

```markdown
1. `アカウント設定` を開きます。

   ![アカウント設定画面](/manuals/account-settings/01-open-account-settings.png)
```

1枚の画像が複数の連続手順を支える場合は、その最後の手順の直後に置き、本文でどの範囲を示す画像か分かるようにする。

赤枠を使った画像でも、本文は画像参照に依存させず、手順自体を明確に書く。

## Handling Uncertainty

次の内容は推測しない。

- 画面名
- ボタン名
- 権限
- 実際の UI に存在するかどうか
- 実際の手順順序
- 通知メールや確認ダイアログの有無
- スクリーンショットの見た目

コードから一部の挙動だけ確認でき、UI では未確認の場合は、確認できた本文だけを書き、画像は捏造しない。必要なら末尾に HTML コメントで要確認事項を残す。

例:

```html
<!-- 要確認:
- 保存完了後に確認ダイアログが表示されるか
- 一般ユーザーにもこの画面が表示されるか
-->
```

## Playwright Capture Strategy

自動操作の前に、小さな撮影計画を立てる。

- このマニュアルで本当に必要な画面は何か。
- 参考扱いでよい画面は何か。
- どの状態が最も説明に向いているか。空状態、設定途中、確認画面、成功状態、警告状態など。
- 複数の手順で使い回せる画像はあるか。

説明価値のない画像は撮らない。

## Final Check

仕上げ前に必ず確認する。

- 画像と本文の手順が一致しているか。
- 本文の手順が実際の操作フローに一致しているか。
- 用語が既存マニュアルと関連 docs でそろっているか。
- 機密情報や個人情報が写っていないか。
- トリミングやリサイズで必要な文脈を削りすぎていないか。
- 赤枠が本当に必要な箇所だけに使われ、誤解を生まないか。
- 画像 URL が `apps/docs/static/manuals/` の配置と一致しているか。
- そのまま docs app にコミットできる品質か。

## Example Triggers

- 「ユーザー向けの設定手順をスクリーンショット付きで manuals に追加してください」
- 「Playwright で画面を取りながらオンボーディングガイドを書いてください」
- 「課金設定のヘルプ記事を画像付きの日本語 markdown にしてください」
- 「既存マニュアルと backend code を見て、実画面のスクリーンショット付きマニュアルにしてください」
