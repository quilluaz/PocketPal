# PocketPal Mobile

Expo Managed Workflow app for PocketPal. It keeps manual transactions in a local SQLite queue, syncs with the FastAPI backend using stable local UUIDs and client revisions, and renders the projected ledger balance as the primary dashboard number.

## Commands

```bash
npm install
npx expo start
```

Set `EXPO_PUBLIC_API_URL` when the backend is not running on `http://localhost:8000`.

