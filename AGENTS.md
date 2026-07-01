# AGENTS.md - SIOTK

Short, repo-specific guidance for agents working on SIOTK ("Stuff I ought to know"), a small Flask flashcard app.

## Repo Shape

- `app.py` is the standalone Flask app entry point.
- `SIOTK.py` exposes the same app as a Flask `Blueprint` using `SIOTK_templates/` and `SIOTK_static/`.
- `templates/` and `static/` support `app.py`; `SIOTK_templates/` and `SIOTK_static/` support the blueprint variant.
- `decks.json` is the current data store. Treat it as user data: do not rewrite, reformat, truncate, or regenerate it unless the task explicitly requires that.
- `static/resources/` and `SIOTK_static/resources/` contain flashcard media/resources. Preserve filenames because cards may reference them directly.

## Commands

- Run standalone app: `.venv/bin/python app.py`
- Run blueprint module directly: `.venv/bin/python SIOTK.py`
- Ruff lint: `.venv/bin/ruff check .`
- Ruff format: `.venv/bin/ruff format .`

## Working Rules

- Keep changes small and local. This repo is intentionally simple; do not introduce a framework, database, build step, or package manager unless asked.
- When changing routes or card/deck behavior, update both `app.py` and `SIOTK.py` if the behavior should stay consistent between standalone and blueprint modes.
- When changing UI markup, update the matching file in both template trees when relevant.
- Preserve the existing deck/card JSON shape: decks have `name`, `description`, `importance`, and `cards`; cards have `question`, `answer`, and `importance`.
- Keep media type detection aligned with `type_form_filepath()` unless deliberately changing how cards render resources.
- Do not commit `.venv`, `__pycache__`, `.DS_Store`, local databases, secrets, or generated scratch files.

## Validation

- There is no dedicated automated test suite in this repo right now.
- After Python changes, run Ruff check when available.
- For behavior changes, run the Flask app and manually exercise the affected route/page.
