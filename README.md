# Flask Starter Template

A minimal Flask + SQLite CRUD application with Tailwind CSS and Alpine.js for interactivity.  
Heavily commented and beginner-friendly, this template gives students full visibility into routing, templating, and database code.

## Project Structure

```
flask-starter/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── create.html
│   └── edit.html
└── static/
    ├── css/
    └── js/
```

## Setup (macOS)

```bash
cd ~/Desktop/Programming/flask-starter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/

## What this teaches
- Routing (Flask), Templating (Jinja2), SQL (sqlite3), Basic HTML forms, Tailwind + Alpine basics.

## Extend later
- Auth (Flask-Login), forms/validation (Flask-WTF), file uploads, blueprints, and testing.
