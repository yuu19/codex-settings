---
name: chrome-web-store
description: Prepare or audit Chrome Web Store Developer Dashboard inputs for Chrome extensions, including listing fields, privacy declarations, store assets, extension ID wiring, deployment follow-up, and final pre-submit checks. Use when the user asks to enter, verify, document, repeat, or update Chrome Web Store settings for any Chrome extension; also supports the RoleTray preset in references/store-inputs.md. Do not submit for review unless the user explicitly asks for submission.
---

# Chrome Web Store Preparation

Use this skill to prepare, reproduce, or verify Chrome Web Store Developer Dashboard setup for a Chrome extension. It is generic; RoleTray-specific values are only a bundled preset.

## Core Rules

- Do not click `審査のため送信` unless the user explicitly asks to submit. If the user says they will submit, stop after confirming the button is enabled.
- Inspect the actual repository before changing anything: manifest, package/build scripts, generated ZIP, store assets, privacy policy URL, backend CORS/origin configuration, and git status.
- Derive project-specific values from the repository and user instructions. Do not reuse RoleTray values for a different extension.
- If browser authentication is required, open a visible Chrome window and wait for the user to complete auth.
- Keep generated store assets committed separately from backend/API configuration changes.
- After an extension ID is created or changed, update any backend allowlist, auth trusted origin, OAuth redirect, CORS, or extension-origin configuration that depends on it. Deploy and verify when the project has a production backend.

## Workflow

1. Identify whether the current project is RoleTray.
   - If yes, read `references/store-inputs.md` for the canonical RoleTray values.
   - If no, use `references/store-inputs.md` only as an example of the fields to collect, not as source data.
2. Confirm the production extension artifact exists. If missing, build or package it using the repository's existing scripts.
3. Inspect the generated manifest for name, version, description, icons, permissions, host permissions, content scripts, and remote-code risk.
4. Confirm required store assets exist: 128x128 icon, at least one 1280x800 or 640x400 screenshot, and optional promotional tiles. Verify screenshot/tile PNGs are 24-bit and have no alpha.
5. Open Chrome Web Store Developer Dashboard in a visible browser. Upload the ZIP if no draft exists.
6. Copy the extension ID from the draft and compare it with any backend or docs configuration.
7. Fill or verify listing fields, image assets, privacy declarations, data-use categories, permission reasons, and publisher contact email.
8. Check `審査のため送信` is enabled and inspect remaining errors if it is not.
9. If the extension ID changed, update dependent backend/config values, deploy, verify health checks, commit, and push if requested.
10. Record results in the related issue or release checklist when the work is part of review preparation.

## Field Collection

For non-RoleTray projects, collect these values before entering Store fields:

- Extension name, summary, detailed description, category, language, homepage URL, support URL, privacy policy URL, publisher contact email.
- Built ZIP path and manifest version.
- Store asset paths and dimensions.
- Single-purpose statement.
- Permission reasons for each requested permission and host permission.
- Data-use categories that match the real implementation.
- Whether remote code is used, based on packaged code and runtime behavior.
- Backend or web app origin settings that must trust the final `chrome-extension://<id>` origin.

## Browser Notes

- Prefer Playwright or Chrome DevTools automation against the visible Chrome instance the user can authenticate in.
- If a hidden MCP browser was opened by mistake, start a visible Chrome with remote debugging and connect to it.
- Treat Google re-auth and email verification as user-owned steps; wait for the user to confirm completion.

## Verification

Run focused checks that match the project. Typical checks:

```bash
pnpm typecheck
pnpm lint
pnpm test
curl -I -s <production-health-url>
```

For RoleTray specifically, use:

```bash
pnpm --filter @roletray/worker typecheck
pnpm --filter @roletray/worker lint
pnpm exec playwright test --project=extension-chromium --workers=1
curl -I -s https://api.roletray.com/health
```

`pnpm test:e2e:extension` may run the RoleTray extension project in parallel and can time out in local Chrome/Worker-heavy environments. A one-worker Playwright run is the reliable confirmation for that flow.
