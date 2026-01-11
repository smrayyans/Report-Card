# Report-Card

Faizan Report Studio is a desktop app for importing student data, managing results, and generating polished report card and diagnostics PDFs from customizable templates.

## What it does

- Imports student rosters and marks from Excel.
- Manages sessions, subjects, filters, and remarks.
- Renders report cards and diagnostics as PDFs using HTML/CSS templates.
- Provides a desktop UI with an Electron + React frontend and a FastAPI backend.

## Tech stack

- Electron, React, Vite
- FastAPI, pandas, psycopg2
- Jinja2 + WeasyPrint for PDF rendering
- PostgreSQL

## Repo layout

- `backend/`: FastAPI app, PDF generation, data processing.
- `discord-client/`: Electron main process and React renderer.
- `templates/`: HTML/CSS templates, fonts, and assets for PDFs.
- `settings/`: DB config, filters, and remarks defaults.
- `config/`: Sessions, subjects, and grading defaults.
- `output/`: Generated PDFs and `student_sample.xlsx`.

## Configuration

- Database: `settings/db_config.json` or env vars `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- App defaults: `config/config.json`.
- UI defaults: `settings/filters.json` and `settings/remarks.json`.

## Development

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.app:app --reload
```

### Desktop app

```powershell
cd discord-client
npm install
npm run dev
```

Note: Electron starts the backend by default. Set `FAIZAN_START_BACKEND=0` if you run the API separately.

## Build

```powershell
cd discord-client
npm run build
```

