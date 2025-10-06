
# Flask + Tailwind (CDN) + Jinja + SQLite Starter

A **minimal but complete** starter template for 9th graders using **Flask**, **Jinja**, **Tailwind via CDN (no Node/npm)**, and **SQLite** with a single `schema.sql` file.

## What's Included
- User authentication: **register, login, logout**
- CRUD for `items` (Create, Read, Update, Delete)
- Multiple tables: `users`, `categories`, `tags`, `items`, `item_tags` (many-to-many)
- `schema.sql` to (re)create the database quickly
- Heavily commented `app.py` with clear teaching notes
- Tailwind via CDN (no build step)
- Jinja base template with navbar/footer + a reusable form partial containing **text input, textarea, radio, and checkboxes**

## Project Structure
```
flask_tailwind_starter/
├─ app.py
├─ schema.sql
├─ requirements.txt
├─ README.md
├─ db/
│  └─ app.db                # created after first run/init
├─ templates/
│  ├─ base.html             # layout with Tailwind CDN
│  ├─ index.html
│  ├─ auth/
│  │  ├─ login.html
│  │  └─ register.html
│  ├─ items/
│  │  ├─ list.html          # list, search, filter
│  │  ├─ create.html        # uses the form partial
│  │  └─ edit.html          # uses the form partial
│  └─ partials/
│     └─ item_form_fields.html  # text, textarea, radio, checkboxes
├─ static/
│  └─ app.css (optional, empty)
└─ tests/
   └─ smoke_test.py
```

## Setup

1) **Download** this folder and unzip it.
2) Open **VS Code** in the folder.
3) Create & activate a virtual environment:
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
py -m venv .venv
.venv\Scripts\Activate.ps1
```
4) Install requirements:
```bash
pip install -r requirements.txt
```
5) Initialize the SQLite database (one-time or anytime you want to reset):
```bash
python app.py --init-db
```
6) Run the app:
```bash
flask --app app run --debug
# visit http://127.0.0.1:5000
```
