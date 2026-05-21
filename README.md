# Vizzel Sales Frontend

LIFF mini app for Vizzel Sales CRM (production only).

## Production URLs

- Frontend: `https://vizzelintel.github.io/vizzel-sales-frontend/`
- Backend API: `https://vizzel-sales-api.fly.dev/api/v1`

## Runtime Constants

Configured in `index.html` and `upload.html`:

- `LIFF_ID`
- `API` / `API_BASE`
- `FRONTEND_BASE_URL`

Keep these constants aligned with production before deploy. Use the same `API` + `API_BASE` pattern in both HTML files.

## Smoke check before deploy

```bash
node -e "const fs=require('fs');const s=fs.readFileSync('index.html','utf8').split('<script>').pop().split('</script>')[0];new Function(s);console.log('OK');"
```

## User Gate

- Users must verify email with OTP on first login before using the app.
- Calendar appointment invite is sent via email (`.ics`) for Google/Outlook compatibility.
