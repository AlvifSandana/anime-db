# AGENTS.md

Purpose
- Guidance for agentic contributors working in this repo.
- Summarizes commands, workflows, and code style.

Repository Overview
- Python 3.12 FastAPI app + scraper.
- Entry points:
  - API: `main.py` / `app/main.py`
  - Scraper: `app/scraper/pipeline.py`
- DB: SQLAlchemy models under `app/db`.

Build / Run Commands
- Create venv: `python -m venv venv`
- Activate venv: `source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run API (dev): `uvicorn main:app --reload`
- Run scraper (blocking): `python -m app.scraper.pipeline`

Test Commands
- Run full test suite: `pytest`
- Run a single test file: `pytest tests/unit/test_parsers.py`
- Run a single test by name: `pytest tests/unit/test_parsers.py -k "parse_anime_list"`
- Run a single test in integration: `pytest tests/integration/test_api_mirrors.py -k "test_get_episode_mirrors_empty"`

Lint / Format
- No dedicated lint/format tool is configured in this repo.
- Keep formatting consistent with existing code (PEP 8 style, 4-space indents).

Project Conventions
Imports
- Group standard library, third-party, then local imports.
- Prefer explicit imports over wildcard imports.
- Keep related imports grouped and sorted.

Formatting
- 4 spaces for indentation.
- Use trailing commas in multi-line literals.
- Keep line lengths reasonable; follow existing style in the file.

Typing
- Type hints are used in several modules (e.g., repository, pipeline, parsers).
- Use `Optional[...]` or `| None` for nullable values.
- Cast only when necessary; avoid masking real type issues.

Naming
- snake_case for functions and variables.
- PascalCase for classes.
- Constants in UPPER_SNAKE_CASE (config keys are env-driven).

Error Handling
- Scraper uses defensive try/except with logging (see `app/scraper/pipeline.py`).
- Prefer `logger.warning` with context in `extra` for recoverable failures.
- Use `session.rollback()` on DB write errors.
- Avoid broad `except` unless logging and re-raising or safe to continue.

Logging
- Use module-level logger (`logger = logging.getLogger(__name__)`).
- Include relevant context in `extra` for scraping failures.

Database
- Use repository helpers in `app/db/repository.py` for DB access.
- When updating models, set `updated_at` and `last_scraped_at` appropriately.
- Keep transactions small; open sessions with `SessionLocal()` and close via context.

Scraper Flow (required)
- Always follow the sequence: list -> episodes -> mirrors.
- For completed anime, skip detail/episodes/mirrors only when fully mirrored.
- Completed + fully mirrored logic is centralized in `is_anime_fully_mirrored`.

API
- FastAPI routes live in `app/api/routes`.
- Responses use Pydantic schemas in `app/schemas`.
- Validate query params with `Query(...)` constraints.

Tests
- Unit tests in `tests/unit`.
- Integration tests in `tests/integration`.
- Use pytest for all tests; no other test runners configured.

Config
- `.env` values are loaded via `app/core/config.py`.
- Prefer env-driven configuration; do not hardcode base URLs or secrets.

Dependencies
- Keep `requirements.txt` updated when adding/removing packages.

Repository Notes
- No `.cursor/rules`, `.cursorrules`, or Copilot instructions detected.
- If rules are added later, update this file accordingly.

When Making Changes
- Read the relevant module before editing to match its style.
- Keep edits minimal and consistent with existing patterns.
- Avoid changing unrelated files.
- Add tests when behavior changes.

Single-Test Examples
- Run a unit test file: `pytest tests/unit/test_mirror_parsers.py`
- Run one test function: `pytest tests/unit/test_mirror_parsers.py -k "test_parse_mirrors"`

Common Pitfalls
- Do not scrape mirrors before episodes are persisted.
- Do not skip completed anime unless mirrors are complete for all episodes.
- Ensure `status_list_page` is populated when list data is available.
- Avoid loading large relationships when a count query suffices.

File References
- Scraper pipeline: `app/scraper/pipeline.py`
- Parsers: `app/scraper/parsers.py`
- DB models: `app/db/models.py`
- Repository: `app/db/repository.py`
- API routes: `app/api/routes/anime.py`
- Schemas: `app/schemas/anime.py`, `app/schemas/mirror.py`
