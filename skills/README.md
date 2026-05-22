# Codex Skills

このディレクトリは、Codex で再利用する個人用スキルを管理します。
各スキルはサブディレクトリごとに分かれており、`SKILL.md` を入口として、必要に応じて `references/`、`scripts/`、`agents/` を含みます。

## 収録スキル

| スキル | 用途 |
| --- | --- |
| `docs-japanese-writing` | 日本語ドキュメント、README、運用ガイド、プロダクト挙動説明を業務読者に伝わる形で作成・改訂します。 |
| `japanese-conventional-commit` | Conventional Commits 形式で、日本語の件名・本文を持つコミットメッセージを作成・レビューします。 |
| `playwright-e2e-test-writer` | TypeScript Web アプリ向けに、Playwright E2E テスト、Page Object、fixtures、setup helper を追加・改善します。 |
| `chrome-web-store` | Chrome 拡張の Web Store 掲載情報、プライバシー申告、拡張 ID 反映手順を確認・再入力します。RoleTray の入力値はプリセットとして参照できます。 |
| `saas-user-manual-screenshot-writer` | SaaS のエンドユーザー向け日本語マニュアルを、実画面スクリーンショット付きで作成・更新します。 |
| `blog-article-creator` | リポジトリ管理の技術ブログ記事を、frontmatter と本文構成を整えて作成・改稿します。 |

## 前提

- GitHub CLI の `gh` v2.90.0 以降がインストールされていること。
- GitHub への認証が済んでいること。
- Codex のスキル配置先が `$CODEX_HOME/skills`、または既定の `~/.codex/skills` であること。

バージョンは次のコマンドで確認します。

```bash
gh --version
```

認証状態は次のコマンドで確認します。

```bash
gh auth status
```

未認証の場合は、次のコマンドでログインします。

```bash
gh auth login
```

## `gh skill` を使ったインストール

GitHub CLI v2.90.0 以降では、`gh skill` で GitHub リポジトリからスキルを直接インストールできます。
この機能は public preview です。
コマンドや挙動は変更される可能性があります。

スキルは AI エージェントの動作に影響する指示、補助スクリプト、参考資料を含みます。
インストール前に内容を確認してください。

```bash
gh skill preview yuu19/codex-settings skills/docs-japanese-writing
```

Codex のユーザー全体で使う場合は、`--agent codex --scope user` を指定します。

```bash
gh skill install yuu19/codex-settings skills/docs-japanese-writing --agent codex --scope user
```

現在の Git リポジトリだけで使う場合は、プロジェクトスコープにインストールします。
プロジェクトスコープでは、Codex など複数のエージェントが `.agents/skills` を共有します。

```bash
gh skill install yuu19/codex-settings skills/docs-japanese-writing --agent codex --scope project
```

スキル名を指定せずに実行すると、対象リポジトリ内のスキルを対話的に選択できます。

```bash
gh skill install yuu19/codex-settings --agent codex --scope user
```

同名スキルを上書きしたい場合は、`--force` を付けます。

```bash
gh skill install yuu19/codex-settings skills/docs-japanese-writing --agent codex --scope user --force
```

インストール元を固定したい場合は、タグまたはコミット SHA を指定します。

```bash
gh skill install yuu19/codex-settings skills/docs-japanese-writing --agent codex --scope user --pin <tag-or-sha>
```

インストール済みスキルの更新確認と更新は、`gh skill update` で行います。

```bash
gh skill update
gh skill update --all
```

インストール後、Codex が新しいスキルを読み込むには再起動が必要な場合があります。

参考:

- [Manage agent skills with GitHub CLI](https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/)

## 手動コピーでのインストール

GitHub CLI の `gh skill` が使えない環境では、手動コピーでもインストールできます。
この手順では `gh skill update` 用の追跡情報は追加されません。
通常は `gh skill install` を使ってください。

まず、GitHub からこのリポジトリを取得します。

```bash
tmpdir="$(mktemp -d)"
gh repo clone yuu19/codex-settings "$tmpdir/codex-settings" -- --depth 1
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
```

必要なスキルだけをインストールする場合は、対象ディレクトリをコピーします。

```bash
cp -R "$tmpdir/codex-settings/skills/docs-japanese-writing" "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R "$tmpdir/codex-settings/skills/japanese-conventional-commit" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

すべてのスキルをまとめてインストールする場合は、次のコマンドを使います。

```bash
for skill in \
  docs-japanese-writing \
  japanese-conventional-commit \
  playwright-e2e-test-writer \
  chrome-web-store \
  saas-user-manual-screenshot-writer \
  blog-article-creator
do
  cp -R "$tmpdir/codex-settings/skills/$skill" "${CODEX_HOME:-$HOME/.codex}/skills/"
done
```

インストール済みの同名スキルを更新したい場合は、古いディレクトリを削除してからコピーし直します。

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/docs-japanese-writing"
cp -R "$tmpdir/codex-settings/skills/docs-japanese-writing" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## 動作確認

インストール先に `SKILL.md` が存在することを確認します。

```bash
ls "${CODEX_HOME:-$HOME/.codex}/skills/docs-japanese-writing/SKILL.md"
```

複数のスキルを入れた場合は、次のように一覧を確認します。

```bash
find "${CODEX_HOME:-$HOME/.codex}/skills" -maxdepth 2 -name SKILL.md -print
```

## メンテナンス

- スキルを追加したら、この README の「収録スキル」を更新します。
- `SKILL.md` の frontmatter にある `name` とディレクトリ名は一致させます。
- 参考資料や補助スクリプトを追加する場合は、スキル本文から必要なファイルだけを読む流れにします。
- 機密情報、個人用トークン、プロジェクト固有の秘密値はスキルに含めません。
