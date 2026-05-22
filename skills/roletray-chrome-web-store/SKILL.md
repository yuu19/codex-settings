---
name: roletray-chrome-web-store
description: Prepare or audit RoleTray Chrome Web Store Developer Dashboard inputs, including listing fields, privacy declarations, store assets, extension ID wiring, and final pre-submit checks. Use when the user asks to enter, verify, document, repeat, or update Chrome Web Store settings for the RoleTray extension; do not submit for review unless the user explicitly asks for submission.
---

# RoleTray Chrome Web Store

Use this skill to reproduce or verify the Chrome Web Store Developer Dashboard setup for the RoleTray extension.

## Core Rules

- Do not click `審査のため送信` unless the user explicitly asks to submit. If the user says they will submit, stop after confirming the button is enabled.
- Use the actual repository state before changing anything: check current ZIP path, manifest, assets, `wrangler.jsonc`, and git status.
- If browser authentication is required, open a visible Chrome window and wait for the user to complete auth.
- Keep generated store assets committed separately from Worker/API configuration changes.
- After the extension ID changes, update Worker production `EXTENSION_ORIGIN`, deploy Worker, verify `/health`, commit, and push if requested.

## Workflow

1. Read `references/store-inputs.md` for the canonical RoleTray field values.
2. Confirm the production ZIP exists or rebuild it with production env vars.
3. Upload the ZIP in Chrome Web Store Developer Dashboard if no draft item exists.
4. Copy the extension ID from the draft and compare it with the reference file.
5. Fill or verify listing fields, image assets, privacy declarations, and publisher contact email.
6. Check `審査のため送信` is enabled and inspect remaining errors if it is not.
7. If the extension ID changed, update Worker production origin and deploy.
8. Record results in the related GitHub issue when the work is part of review preparation.

## Browser Notes

- Prefer Playwright or Chrome DevTools automation against the visible Chrome instance the user can authenticate in.
- If a hidden MCP browser was opened by mistake, start a visible Chrome with remote debugging and connect to it.
- Treat Google re-auth and email verification as user-owned steps; wait for the user to confirm completion.

## Verification

Run focused checks that match the work:

```bash
pnpm --filter @roletray/worker typecheck
pnpm --filter @roletray/worker lint
pnpm exec playwright test --project=extension-chromium --workers=1
curl -I -s https://api.roletray.com/health
```

`pnpm test:e2e:extension` may run the extension project in parallel and can time out in local Chrome/Worker-heavy environments. A one-worker Playwright run is the reliable confirmation for this flow.
