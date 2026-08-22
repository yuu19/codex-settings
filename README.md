# codex-settings

自分が管理するLinux環境へ、Codexの共通設定と共有skillsを安全に導入するためのリポジトリです。
WSL2、VPS、SSH先で同じ設定を再現できます。

機密情報、認証情報、承認規則、sandbox、ネットワーク権限、プロジェクトの信頼設定は同期しません。
各環境で必要な権限と認証を個別に設定してください。

## 前提

- Linux
- Git
- Codex CLI 0.148.0以上
- Python 3.11以上

Codex CLIとGitHubの認証情報は、このリポジトリでは管理しません。
ブラウザ機能を有効にする場合だけ、Node.js、`npx`、Google ChromeまたはChromiumが必要です。

## 初回セットアップ

publicリポジトリをcloneし、内容を確認してからセットアップを実行します。

```bash
git clone --depth 1 https://github.com/yuu19/codex-settings.git
cd codex-settings
./bin/codex-settings setup
```

セットアップは変更差分を表示し、適用前に確認を求めます。
確認できない非対話環境では、`--yes`を明示してください。

```bash
./bin/codex-settings setup --yes
```

ブラウザ操作も利用する環境では、初回セットアップ時に追加します。

```bash
./bin/codex-settings setup --with browser
```

変更せずに結果だけ確認する場合は、`--dry-run`を使います。

```bash
./bin/codex-settings setup --dry-run
```

## 更新

GitHubからの取得とローカル設定への反映は別の操作です。
`sync`はネットワークから更新を取得しません。

```bash
git pull --ff-only
./bin/codex-settings sync
```

同期元は、通常は未コミット変更のないcheckoutに限定されます。
開発中の動作確認に限り、`--allow-dirty`を明示できます。

```bash
./bin/codex-settings sync --allow-dirty --dry-run
```

## Capability

導入する機能は `core` と `browser` に分かれています。

### core

すべての環境で有効になります。

- portableなCodex既定設定
- HTTPで接続するドキュメント・開発支援MCP
- `blog-article-creator`
- `create-er-reference-html`
- `docs-japanese-writing`
- `japanese-conventional-commit`
- `playwright-e2e-test-writer`
- `ts-documentation`

### browser

必要な環境だけで明示的に有効にします。

- Playwright MCP
- Chrome DevTools MCP
- Cloudflare Browser Rendering MCP
- `chrome-web-store`
- `saas-user-manual-screenshot-writer`

有効化したcapabilityは次回以降も維持されます。

```bash
./bin/codex-settings capability enable browser
./bin/codex-settings sync
```

無効化すると、次の同期でこのリポジトリが管理しているbrowser設定とskillsだけを撤去します。

```bash
./bin/codex-settings capability disable browser
./bin/codex-settings sync
```

## 管理範囲

| 対象 | 配置先 | 同期方法 |
| --- | --- | --- |
| Codex設定 | `~/.codex/config.toml` | `manifest.toml`が所有するキーだけを更新 |
| 共有skills | `~/.agents/skills` | 選択中のcapabilityに属するディレクトリを同期 |
| 同期state | `${XDG_STATE_HOME:-~/.local/state}/codex-settings/state.json` | 所有対象、反映元コミット、ハッシュを記録 |
| 変更記録 | `${XDG_STATE_HOME:-~/.local/state}/codex-settings/backups/` | 管理対象の変更内容だけを記録 |

既存のローカル設定は保持します。
管理対象の値だけがリポジトリの値へ更新されます。

次の項目は変更しません。

- `sandbox_mode`
- `approval_policy`、`approvals_reviewer`
- sandbox内のネットワーク権限
- プロジェクトごとの`trust_level`
- ツールごとの承認規則
- 認証、プラグイン、marketplace、通知、UIの状態

このリポジトリが以前に同期した項目をmanifestから削除した場合は、次の同期で自動撤去します。
ユーザーが追加した項目や、内容が異なる同名skillは削除せず、競合として停止します。

旧配置の `~/.codex/skills` に、現在または過去のcodex-settingsコミットと一致するskillがある場合は、`~/.agents/skills` へ移行して旧コピーを撤去します。
Git履歴から配布元を確認できない場合は自動移行しません。

## 状態確認と診断

同期差分を確認します。

```bash
./bin/codex-settings status
```

設定、認証、依存コマンド、MCPの状態を診断します。

```bash
./bin/codex-settings doctor
```

`sync`はローカルの構文と配置を厳格に検証します。
外部サービスの認証未完了や一時的な接続障害は、同期失敗ではなく`doctor`の診断結果として扱います。

## 安全性

- 適用候補はTOMLとして検証した後、実行中のCodex CLIでもstrict検証します。
- 設定、skills、stateの途中更新に失敗した場合は、変更前の状態へ戻します。
- stateと変更記録には、認証ファイルや管理対象外の設定値を保存しません。
- browser MCPのローカルパッケージはexact versionへ固定します。
- `manifest.toml`をskills、capability、対応バージョンの正本とします。

## 開発と検証

標準ライブラリの`unittest`で検証します。

```bash
python3 -m unittest discover -s tests -v
```

GitHub ActionsではPython 3.11、3.12、3.13を使ってLinux上でテストします。
初回リリース前には、`ssh codex-platform`でclone、セットアップ、skill検出、再同期の冪等性を別工程として確認します。

skillsの追加・保守方法は [skills/README.md](skills/README.md) を参照してください。

## 参考資料

- [OpenAI Codex configuration reference](https://developers.openai.com/codex/config-reference/)
- [OpenAI Codex skills](https://developers.openai.com/codex/skills/)
- [Context7 installation](https://github.com/upstash/context7#installation)
