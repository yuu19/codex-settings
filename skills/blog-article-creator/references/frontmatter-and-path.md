# Frontmatter And Path

## Default path convention (yusuke-blog)

- Article directory: `articles/`
- One article per file: `articles/<slug>.md`

## Required frontmatter keys

```yaml
title: '...'
description: '...'
emoji: '📝'
date: YYYY-MM-DD
topics: ["topic1", "topic2"]
blog_published: True
published: False
```

## Notes

- `blog_published` controls visibility in blog article lists.
- `published` is a separate external-publish flag.
- `date` should be ISO format: `YYYY-MM-DD`.
- Keep `slug` filesystem-safe: lowercase letters, digits, hyphens.

## Slug guidance

- Good: `crypto-delta-neutral-theory`
- Avoid spaces, underscores, and uppercase letters.

