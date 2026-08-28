# Codex Skills

このディレクトリでは、複数のLinux環境で再利用する個人用skillsを管理します。
各skillはサブディレクトリに置き、`SKILL.md`を入口とします。

必要に応じて、次の補助ディレクトリを含められます。

- `references/`: 作業時に必要な参考資料
- `scripts/`: 再現可能な補助処理
- `assets/`: テンプレートや画像
- `agents/`: 表示情報と依存ツールの宣言

## 配布対象

配布対象とcapabilityは、リポジトリ直下の [manifest.toml](../manifest.toml) を正本とします。
ディレクトリを追加しただけでは、利用環境へ同期されません。

### core

- `blog-article-creator`
- `create-er-reference-html`
- `natural-japanese`
- `japanese-conventional-commit`
- `playwright-e2e-test-writer`
- `ts-documentation`

### browser

- `chrome-web-store`
- `saas-user-manual-screenshot-writer`

`browser`は、ブラウザ操作そのものを成果物の作成や検証に必要とするskillだけに使用します。
ブラウザを扱うコードを書くという理由だけで、`playwright-e2e-test-writer`をbrowserへ分類しません。

## ユーザー環境への同期

通常はリポジトリ直下の同期コマンドを使います。

```bash
./bin/codex-settings setup
./bin/codex-settings sync
```

ユーザースコープの配置先は、現行のCodex仕様に合わせて `~/.agents/skills` とします。
`~/.codex/skills` は新しい配布先として使用しません。

現在のリポジトリだけで使うskillは、対象リポジトリの `.agents/skills` で管理してください。
プロジェクト固有のskillをこの共有一覧へ追加しないでください。

## skillの追加

1. `skills/<skill-name>/SKILL.md`を作成する。
2. frontmatterの`name`とディレクトリ名を一致させる。
3. `description`へ利用場面と対象外の境界を書く。
4. 必要な補助ファイルだけを段階的に読む構成にする。
5. `manifest.toml`へskillとcapabilityを追加する。
6. テストを実行する。

```bash
python3 -m unittest discover -s tests -v
```

環境にskill validatorがある場合は、対象skillも検証します。

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

## 変更時の規則

- `manifest.toml`にないskillは配布されません。
- READMEの一覧とmanifestの不一致はテストで検出します。
- browser必須のskillだけを`browser`へ分類します。
- 機密情報、トークン、認証ファイル、個人データを含めません。
- 外部のskillを取り込む場合は、配布元、commit SHA、ライセンスを記録します。
- 外部skillへのローカル変更は、配布元との差分と理由をskill内の出典記録へ残します。
- 補助スクリプトは入力を検証し、失敗時に明確なエラーを返します。
- skillの追加と既存skillの大幅な変更は、可能な限り別のコミットに分けます。

Codexはskillの変更を通常は自動検出します。
一覧へ反映されない場合はCodexを再起動してください。
