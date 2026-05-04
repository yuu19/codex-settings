---
name: blog-article-creator
description: Create, revise, and publish Markdown blog articles for repository-based technical blogs (especially yusuke-blog). Use when users ask to generate new articles, rewrite article drafts, enforce frontmatter fields (`title`, `description`, `date`, `topics`, `blog_published`, `published`), produce theory-first technical explanations, or deploy updated articles after writing.
---

# Blog Article Creator

## Overview

Create high-quality technical blog articles in Markdown with correct frontmatter, consistent structure, and optional deploy flow.

Use this workflow for article generation requests in code repositories where article files are stored on disk.

## Workflow

1. Confirm target repository conventions.
2. Create or update article files under the configured article directory.
3. Keep frontmatter complete and valid for publication filters.
4. Write content with a clear technical structure (definitions, model, derivation, assumptions, risks, summary).
5. Run optional build/deploy steps only when requested.

## Repository Convention Loading

Read only what is needed:

- Read `references/frontmatter-and-path.md` when deciding file path, slug, and metadata keys.
- Read `references/theory-writing-patterns.md` when the user asks for mathematically rigorous or theory-heavy writing.
- Read `references/deploy-workflow.md` when asked to deploy after writing.

## Fast Path For New Articles

For deterministic scaffolding, use:

```bash
python3 scripts/new_article.py \
  --title "<title>" \
  --slug "<slug>" \
  --description "<description>" \
  --topics "topic1,topic2" \
  --blog-published true \
  --published false
```

Then expand the generated body sections with task-specific content.

## Quality Rules

- Keep frontmatter and body consistent with the user request.
- Prefer explicit assumptions over vague statements.
- For quant/math articles, define symbols before using formulas.
- Distinguish model assumptions from empirical claims.
- Do not deploy unless the user requested deployment.

## Completion Checklist

- Article file exists in the correct directory.
- Frontmatter includes all required keys.
- `blog_published` is set exactly as requested.
- If deployment was requested: build, deploy, and verify article URL response.
