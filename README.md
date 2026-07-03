# Vizzel Sales Frontend

LIFF mini app for Vizzel Sales CRM (static HTML/JS — no build step).

## URLs

| Environment | Frontend | API |
|---|---|---|
| Production | `https://sale.vizzeltrack.com/` | `https://sale-api.vizzeltrack.com` |
| Staging | `https://staging-sale.vizzeltrack.com/` | `https://staging-sale-api.vizzeltrack.com` |
| Legacy (transition) | `https://vizzelintel.github.io/vizzel-sales-frontend/` | `https://vizzel-sales-api.fly.dev` |

## Runtime config

`js/config.js` picks the environment from hostname (or `localStorage.vizzel_config_env` override):

- `config/config.production.js`
- `config/config.staging.js`
- `config/config.local.js`
- `config/config.legacy.js`

Loaded before inline scripts in `index.html` and `upload.html`.

## Document download

Self-hosted API stores files locally. The app opens documents via authenticated
`GET /api/v1/documents/:id/download` (JWT Bearer). Legacy Supabase public URLs still open in a new tab.

## Smoke check before deploy

```bash
node -e "const fs=require('fs');const s=fs.readFileSync('index.html','utf8').split('<script>').pop().split('</script>')[0];new Function(s);console.log('OK');"
```

## Deploy

- **GitHub Pages (legacy):** push to `main` → `.github/workflows/deploy.yml`
- **Staging server:** push to `main` → rsync to `/opt/vizzel-sales-frontend-staging/`
- **Production server:** tag `sale-v*` → rsync to `/opt/vizzel-sales-frontend/`

GitHub secrets: `SALES_DEPLOY_SSH_KEY`, `SALES_DEPLOY_USER`, `SALES_STAGING_HOST`, `SALES_PROD_HOST`

## User gate

- Users must verify email with OTP on first login before using the app.
- Calendar appointment invite is sent via email (`.ics`) for Google/Outlook compatibility.
