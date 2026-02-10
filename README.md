# anime-db

Scraper + API untuk otakudesu anime list.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # optional; edit as needed
```

## Menjalankan API

```bash
uvicorn main:app --reload
```

## Menjalankan scraper (blocking)

```bash
python - <<'PY'
from app.scraper.pipeline import run_blocking_scrape

run_blocking_scrape()
PY
```

Kendalikan jumlah anime yang di-scrape dengan env `SCRAPER_MAX_ITEMS` (opsional, default tidak dibatasi).

## Endpoint
- `GET /health`
- `GET /anime?status=on-going|completed&q=search&limit=20&offset=0`
- `GET /anime/{id}`
- `GET /anime/{id}/episodes?order=asc|desc&limit=50&offset=0`

## Tests

```bash
pytest
```
