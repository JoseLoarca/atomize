# atomize-web

Next.js (App Router, TypeScript, Tailwind) PWA frontend for Atomize, per [docs/TECH_STACK.md](../../docs/TECH_STACK.md). Deployed to AWS Amplify Hosting; calls the `atomize-api` backend over HTTP (never talks to the database directly), so a future native app can reuse the same API.

## Setup

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scripts

```bash
npm run dev      # local dev server
npm run build    # production build
npm run lint      # eslint
```
