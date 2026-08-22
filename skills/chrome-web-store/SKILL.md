---
name: chrome-web-store
description: Manage or audit Chrome Web Store releases with API v2-first package upload, status, submission, cancellation, and rollout workflows, using the Developer Dashboard only for unsupported initial setup and metadata. Use for extension publishing, release readiness, Store fields, privacy declarations, or extension ID wiring.
---

# Chrome Web Store Release Management

Use this skill to prepare, reproduce, automate, or verify Chrome Web Store releases. Prefer Chrome Web Store API v2 for supported operations; open the Developer Dashboard only for operations that the API does not provide.

## Core Rules

- Read `references/api-v2.md` before any Chrome Web Store API operation or release-workflow change.
- Prefer Chrome Web Store API v2 over browser automation for an existing item's package upload, status retrieval, review submission, submission cancellation, and percentage rollout.
- Use the Developer Dashboard for new item creation, first ZIP upload and item ID acquisition, Store listing, graphic assets, Privacy practices, distribution or visibility, and a final check that stops before submission.
- Do not use the deprecated v1 item-insert endpoint to avoid the Dashboard. API v2 intentionally does not create items, and v1 support ends on October 15, 2026.
- Never call `publishers.items.publish` unless the user explicitly asks Codex to submit the item for review. `blockOnWarnings: true` is not a dry-run; a successful request creates a real submission.
- Never call `cancelSubmission` or `setPublishedDeployPercentage` unless the user explicitly asks for that exact external change.
- Treat an audit, readiness check, or request to prepare instructions as read-only. Do not upload a package merely because API credentials are available.
- Keep OAuth client secrets, refresh tokens, access tokens, service-account keys, and credential files out of the repository, chat, command output, logs, artifacts, and generated documentation.
- Treat authentication, consent, reauthentication, and secret creation as user-owned steps. Provide a handoff without displaying or copying secret values.
- Inspect the actual repository before changing anything: manifest, package and build scripts, release workflow, generated ZIP, store assets, privacy policy URL, backend CORS or origin configuration, and git status.
- Derive project-specific values from repository evidence and user instructions. Do not reuse RoleTray values for a different extension.
- Keep generated store assets separate from backend or API configuration changes in version control.
- After an extension ID is created or changed, update every backend allowlist, trusted origin, OAuth redirect, CORS rule, and extension-origin configuration that depends on it. Deploy and verify only when requested.

## API and Dashboard Boundary

| Operation | Preferred route |
| --- | --- |
| Fetch current item, upload, review, and publication status | API v2 `fetchStatus` |
| Upload a ZIP to an existing item | API v2 `media.upload` |
| Submit for review after explicit user authorization | API v2 `publish` |
| Cancel an active submission after explicit user authorization | API v2 `cancelSubmission` |
| Increase an eligible published rollout after explicit user authorization | API v2 `setPublishedDeployPercentage` |
| Create a new item and obtain its first extension ID | Developer Dashboard |
| Edit listing text, screenshots, promo images, Privacy practices, policy URLs, distribution, or visibility | Developer Dashboard |
| Confirm the Dashboard submit button is enabled without submitting | Developer Dashboard |

## Workflow

1. Classify the request as read-only audit, package upload, review submission, submission cancellation, rollout change, initial setup, or metadata change. External mutations require the corresponding user request.
2. Identify whether the project is RoleTray.
   - If yes, read `references/store-inputs.md` for the current preset, then re-check it against the live repository.
   - If no, use that reference only as an example of the fields to collect.
3. Inspect the extension manifest and release path. Confirm name, version, description, icons, permissions, host permissions, content scripts, remote-code risk, package command, and ZIP output.
4. Locate the publisher ID and extension item ID in non-secret repository configuration, CI variables, or release documentation.
   - If either ID is absent because the item is new, use a visible browser for initial Dashboard setup.
   - Do not infer one project's IDs for another project.
5. For an existing item, use API v2 `fetchStatus` before changing it. Record the published and pending version or state needed to detect version mistakes and active submissions.
6. When upload is requested, build or package with the repository's existing scripts. Inspect the ZIP and ensure the manifest version is higher than the currently uploaded or published version.
7. Upload the ZIP with API v2, then poll `fetchStatus` with a bounded timeout and backoff until processing succeeds or fails. Do not treat the initial HTTP success as completed processing.
8. Compare repository changes with the current Store metadata contract.
   - If listing, privacy, assets, policy URL, distribution, or visibility must change, use the Developer Dashboard only for those fields.
   - If none changed, do not open a browser merely to repeat the upload or status check.
9. Verify extension-ID-dependent backend and web configuration. Keep local validation, deployment, commit, and push results distinct.
10. Handle submission according to the user's intent.
    - If the user explicitly asks Codex to submit, confirm the intended `publishType` (`DEFAULT_PUBLISH` or `STAGED_PUBLISH`), call API v2 `publish` with `blockOnWarnings: true`, and inspect the response and `fetchStatus` result.
    - If the user will submit, open the Dashboard, confirm the submit button is enabled, and stop without clicking it.
    - If submission was not requested, stop after upload and status verification.
11. For cancellation or rollout, show the current state and requested target first, then call the corresponding API only after the user has explicitly requested that action. Verify the resulting status.
12. Record sanitized results in the related issue, release, or checklist when requested. Include item ID, package version, operation, state, and timestamp, but no credentials.

## Authentication

- Prefer a service account for unattended CI/CD when the publisher has already authorized that model. API v2 formally supports service accounts, but only one service account can currently be linked to a publisher.
- For local CLI work, prefer short-lived access tokens obtained through service-account impersonation when available.
- OAuth 2.0 with the `https://www.googleapis.com/auth/chromewebstore` scope remains valid. Store its client ID, client secret, and refresh token in the project's approved secret store, never in tracked files.
- Do not introduce a third-party publishing action or package when direct API calls or an existing reviewed project tool are sufficient. If the repository already uses a publishing tool, inspect its API version and pin before retaining it.
- On `invalid_grant`, stop. Ask the authorized operator to rotate or replace the refresh token in the secret store, then rerun the failed release job. Never request the token value in chat.

## Store Field Collection

For non-RoleTray projects, collect these values before Dashboard entry:

- Publisher ID and extension item ID.
- Extension name, summary, detailed description, category, language, homepage URL, support URL, privacy policy URL, and public publisher contact email.
- Built ZIP path and manifest version.
- Store asset paths and dimensions.
- Single-purpose statement.
- Permission reasons for each requested permission and host permission.
- Data-use categories that match the implementation.
- Whether remote code is used, based on packaged code and runtime behavior.
- Distribution, visibility, review, automatic-versus-staged publication, and rollout intent.
- Backend or web app origin settings that must trust the final `chrome-extension://<id>` origin.

## Browser Notes

- Open a visible browser only when the operation is in the Dashboard-only boundary or the user requests visual verification.
- Prefer Playwright or Chrome DevTools automation against the visible Chrome instance the user can authenticate in.
- If a hidden browser was opened by mistake, start a visible Chrome with remote debugging and connect to it.
- Stop at Google reauthentication, consent, email verification, and credential creation so the user can complete them.

## Verification

Run focused checks that match the project before packaging. Typical checks:

```bash
pnpm typecheck
pnpm lint
pnpm test
```

After an API operation, verify the response and call `fetchStatus`. If production configuration changed, run the repository's health checks separately.

For RoleTray specifically, use:

```bash
pnpm --filter @roletray/worker typecheck
pnpm --filter @roletray/worker lint
pnpm exec playwright test --project=extension-chromium --workers=1
curl -I -s https://api.roletray.com/health
```

`pnpm test:e2e:extension` may run the RoleTray extension project in parallel and can time out in local Chrome or Worker-heavy environments. A one-worker Playwright run is the reliable confirmation for that flow.

## Completion Report

Distinguish these outcomes explicitly:

- repository checks completed;
- package built and inspected;
- API upload accepted and processing completed;
- review submission created;
- Store review or publication completed;
- Dashboard-only metadata verified or changed;
- production configuration deployed;
- Git commit created and pushed.

Do not describe an accepted upload as submitted, approved, published, deployed, committed, or pushed unless each separate outcome is verified.
