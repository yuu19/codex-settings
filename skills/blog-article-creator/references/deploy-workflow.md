# Deploy Workflow

Use this only when deployment is explicitly requested.

## Authentication check

```bash
npx wrangler whoami
```

## Build

```bash
PUBLIC_BASE_URL=https://tech-yusuke.com npm run build
```

## Deploy to production environment

```bash
npx wrangler deploy --env production
```

## Verify article availability

```bash
curl -I -s https://<worker-domain>/articles/<slug> | head -n 5
```

Expect `HTTP/2 200`.

