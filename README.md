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
python -m app.scraper.pipeline
```

Kendalikan jumlah anime yang di-scrape dengan env `SCRAPER_MAX_ITEMS` (opsional, default tidak dibatasi).

Pengaturan concurrency:
- `SCRAPER_CONCURRENCY` untuk jumlah task anime paralel (default 8).
- `SCRAPER_EPISODE_CONCURRENCY` untuk jumlah fetch episode paralel (default 2).
- `SCRAPER_MIRROR_CONCURRENCY` untuk jumlah fetch mirror paralel (default 4).

## Endpoint
- `GET /health`
- `GET /anime?status=on-going|completed&q=search&limit=20&offset=0`
- `GET /anime/{id}`
- `GET /anime/{id}/episodes?order=asc|desc&limit=50&offset=0`

## Tests

```bash
pytest
```
