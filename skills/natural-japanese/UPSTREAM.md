# Upstream provenance

- Repository: https://github.com/coji/natural-japanese
- Upstream path: `skills/natural-japanese/`
- Version: `v1.3.0`
- Commit: `b54954f8deb4f110f0959f4e4fac295708900120`
- License: MIT（同梱の`LICENSE`を参照）

## Local changes

- `SKILL.md`から`references/technical-document-policy.md`を参照するルーティングを追加した。
- 置換前の`docs-japanese-writing`が定めていた、読者に見える挙動を実装識別子より先に説明する方針を、上記の参照ファイルへ移した。
- 補助スクリプトをユーザーのプロジェクトから誤って探索しないよう、パスをskillディレクトリ基準で解決する指示を追加した。
- Codexのskill validatorが受け付けないfrontmatterの`argument-hint`を削除した。呼び出し形式の説明は本文に残している。
- CodexのUIからskill名と用途を確認できるよう、`agents/openai.yaml`を追加した。
- `git diff --check`に合わせ、4ファイルのEOF直前にあった余分な空行を削除した。

上流を更新するときは、固定するtagとcommitを変更し、同梱スクリプトとライセンスを再確認したうえで、このローカル差分を適用し直す。
