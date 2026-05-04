# Frontmatter とパス

## デフォルトのパス規約（yusuke-blog）

- 記事ディレクトリ: `articles/`
- 1 記事 1 ファイル: `articles/<slug>.md`

## 必須 frontmatter キー

```yaml
title: '...'
description: '...'
emoji: '📝'
date: YYYY-MM-DD
topics: ["topic1", "topic2"]
blog_published: True
published: False
```

## 補足

- `blog_published` はブログの記事一覧に表示するかどうかを制御する。
- `published` は外部公開用の別フラグとして扱う。
- `date` は ISO 形式の `YYYY-MM-DD` にする。
- `slug` はファイルシステムで安全に扱える、小文字英字・数字・ハイフンに限定する。

## Slug の指針

- 良い例: `crypto-delta-neutral-theory`
- スペース、アンダースコア、大文字英字は避ける。
