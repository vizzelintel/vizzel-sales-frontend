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

Keep these constants aligned with production before deploy.

## User Gate

- Users must verify email with OTP on first login before using the app.
- Calendar appointment invite is sent via email (`.ics`) for Google/Outlook compatibility.
