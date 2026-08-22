# Chrome Web Store API v2 Reference

Use this reference for API-first Chrome Web Store release work. Confirm the current official documentation before changing endpoints, fields, or authentication because this is an external API.

## Sources and Decision

- Repository decision: [codex-settings Discussion #1](https://github.com/yuu19/codex-settings/discussions/1)
- Official overview: [Chrome Web Store API](https://developer.chrome.com/docs/webstore/api/)
- Official tutorial: [Use the Chrome Web Store API](https://developer.chrome.com/docs/webstore/using-api)
- Official REST reference: [Chrome Web Store API v2](https://developer.chrome.com/docs/webstore/api/reference/rest)
- Official service-account setup: [Use a service account](https://developer.chrome.com/docs/webstore/service-accounts)
- Official v2 migration announcement: [Introducing a new Chrome Web Store API](https://developer.chrome.com/blog/cws-api-v2)

The repository decision is API-first, not API-only. Use v2 for an existing item's package and release lifecycle. Use the Developer Dashboard for new items and metadata the API does not expose.

## Supported Operations

API v2 exposes these release operations:

| Method | Endpoint suffix | Purpose |
| --- | --- | --- |
| `media.upload` | `:upload` | Upload a package to an existing item |
| `publishers.items.fetchStatus` | `:fetchStatus` | Read published and pending item state |
| `publishers.items.publish` | `:publish` | Create a real review or publication submission |
| `publishers.items.cancelSubmission` | `:cancelSubmission` | Cancel an active submission |
| `publishers.items.setPublishedDeployPercentage` | `:setPublishedDeployPercentage` | Increase an eligible published rollout |

API v2 does not create a new item or edit Store listing text, screenshots, promotional images, Privacy practices, privacy policy URLs, distribution, or visibility. Use the Dashboard for these operations.

Do not use the v1 item-insert endpoint as a fallback. V1 support ends on October 15, 2026, and v2 intentionally removed new-item creation because the remaining metadata still requires the Dashboard.

## Required Identity and Authentication

Keep these non-secret identifiers in repository configuration or CI variables:

- `CWS_PUBLISHER_ID`
- `CWS_EXTENSION_ID`

Keep credentials only in an approved secret store. API calls require a short-lived bearer token with this scope:

```text
https://www.googleapis.com/auth/chromewebstore
```

For local service-account impersonation, the authorized user can obtain a short-lived token without committing a JSON key:

```bash
gcloud auth print-access-token \
  --impersonate-service-account="$CWS_SERVICE_ACCOUNT" \
  --scopes=https://www.googleapis.com/auth/chromewebstore
```

Do not paste the result into chat or logs. Export it only in the shell that performs the API request. A publisher can currently link only one service account in the Developer Dashboard.

OAuth client credentials and refresh tokens are also supported. On `invalid_grant`, stop and hand off refresh-token replacement to the authorized operator.

## Read Status

Use `fetchStatus` before upload and after every mutation:

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CWS_ACCESS_TOKEN:?}" \
  "https://chromewebstore.googleapis.com/v2/publishers/${CWS_PUBLISHER_ID:?}/items/${CWS_EXTENSION_ID:?}:fetchStatus"
```

Inspect published and pending revisions, versions, item state, upload state, and warnings. Sanitize stored output and never persist request headers.

## Upload an Existing Item

Uploading changes the existing item's draft. Perform it only when the user asks to upload, release, or otherwise update the Store item.

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CWS_ACCESS_TOKEN:?}" \
  -X POST \
  -T "${CWS_ZIP_FILE:?}" \
  "https://chromewebstore.googleapis.com/upload/v2/publishers/${CWS_PUBLISHER_ID:?}/items/${CWS_EXTENSION_ID:?}:upload"
```

The response contains `itemId`, `crxVersion`, and `uploadState`. If the state is `UPLOAD_IN_PROGRESS`, poll `fetchStatus` with a bounded timeout and backoff. Fail on an unsuccessful terminal state or version mismatch.

Uploading does not submit the item for review.

## Submit for Review

`publish` has no validation-only or dry-run mode. `blockOnWarnings: true` converts warnings into blocking errors, but a successful request still creates a real submission.

Call it only after explicit user authorization and after confirming the desired publication behavior:

- `DEFAULT_PUBLISH`: publish automatically after approval.
- `STAGED_PUBLISH`: stage after approval for a later explicit publication action.

Example for staged publication:

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CWS_ACCESS_TOKEN:?}" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"publishType":"STAGED_PUBLISH","blockOnWarnings":true}' \
  "https://chromewebstore.googleapis.com/v2/publishers/${CWS_PUBLISHER_ID:?}/items/${CWS_EXTENSION_ID:?}:publish"
```

Do not set `skipReview: true` unless the user explicitly requests it and the item is known to qualify. After a successful request, call `fetchStatus` and report the resulting submission state.

If the user wants to submit personally, do not call this endpoint. Open the Dashboard, confirm the submit button is enabled, and stop.

## Cancel a Submission

Cancellation is a real external mutation. Call it only when explicitly requested:

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CWS_ACCESS_TOKEN:?}" \
  -X POST \
  "https://chromewebstore.googleapis.com/v2/publishers/${CWS_PUBLISHER_ID:?}/items/${CWS_EXTENSION_ID:?}:cancelSubmission"
```

Verify the result with `fetchStatus`.

## Increase Percentage Rollout

The API can increase the target rollout percentage for eligible published items. The official tutorial states that percentage rollout is available to items with more than 10,000 seven-day active users.

```bash
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CWS_ACCESS_TOKEN:?}" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"deployPercentage":100}' \
  "https://chromewebstore.googleapis.com/v2/publishers/${CWS_PUBLISHER_ID:?}/items/${CWS_EXTENSION_ID:?}:setPublishedDeployPercentage"
```

Confirm the current and requested percentages before the call. Do not use this endpoint to reduce rollout or assume eligibility.

## Error Handling

- `401` or `403`: verify API enablement, publisher ownership, service-account linkage, scope, and token expiry without printing credentials.
- `invalid_grant`: the OAuth refresh token is invalid or expired; require authorized operator rotation.
- Version rejection: compare the ZIP manifest version with pending and published versions returned by `fetchStatus`.
- `UPLOAD_IN_PROGRESS`: poll with a timeout; do not immediately retry the upload.
- Warnings or validation errors from `publish`: report structured reasons and leave the item unsubmitted when the request failed.
- Network or `5xx` failure: use bounded retries with exponential backoff only for idempotent reads. Before retrying a mutation, call `fetchStatus` to determine whether it already succeeded.

## Dashboard Fallback

Use a visible, user-operable browser for:

- Add new item and first package upload.
- Extension ID acquisition.
- Listing text, localization, screenshots, promo images, and related URLs.
- Privacy practices, permission reasons, data-use declarations, and privacy policy URL.
- Distribution, regions, trusted testers, and visibility.
- Confirming that submission is possible without creating a submission.

Do not describe Dashboard work as API automation. Record which fields still required the browser.
