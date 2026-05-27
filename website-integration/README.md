# Embed the corner chat on your website (separate repo)

## 1) Run the API (this repo)

```powershell
cd AwesomeTactics-Copilot
.venv\Scripts\activate
uvicorn app.server:app --reload --port 8000
```

Check:

- http://127.0.0.1:8000/health → `{"ok": true}`
- http://127.0.0.1:8000/widget.js → widget script

## 2) CORS (this repo `.env`)

```env
CORS_ALLOW_ORIGINS=https://s2group.cs.vu.nl,http://localhost:4000,http://127.0.0.1:4000
```

Restart uvicorn after changing `.env`.

## 3) Website repo — before `</body>`

Local dev (API on your machine):

```html
<script
  src="http://localhost:8000/widget.js"
  data-api-base="http://localhost:8000"
  data-title="Tactics Copilot"
  data-subtitle="Ask about tactics"
  data-mode="recommend"
  data-top-k="8"
></script>
```

**Production:** `https://s2group.cs.vu.nl` cannot call `http://localhost:8000` (mixed content + not public). Deploy this API on HTTPS (e.g. `https://copilot.your-domain`) and use that URL for `src` and `data-api-base`. Add any extra origins to `CORS_ALLOW_ORIGINS`.

Optional Jekyll: set `tactics_copilot_api_base` in `_config.yml` (no trailing slash) and use it for both `src` and `data-api-base`.
