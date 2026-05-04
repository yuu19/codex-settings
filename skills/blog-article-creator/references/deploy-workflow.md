# デプロイ手順

ユーザーが明示的にデプロイを依頼した場合だけ使う。

## 認証確認

```bash
npx wrangler whoami
```

## ビルド

```bash
PUBLIC_BASE_URL=https://tech-yusuke.com npm run build
```

## 本番環境へのデプロイ

```bash
npx wrangler deploy --env production
```

## 記事 URL の確認

```bash
curl -I -s https://<worker-domain>/articles/<slug> | head -n 5
```

`HTTP/2 200` が返ることを確認する。
