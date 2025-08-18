"""
app.py: A Flask todo-list application with tagging, categorization, and due date sorting.

Features:
- Create, read, update, delete todos
- Tag and categorize todos
- Sort by due date
- Simple and clean interface using Tailwind CSS

How to run:
    python3 -m venv venv
    source venv/bin/activate (or venv\Scripts\activate on Windows)
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000/
"""

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, date
import os

# Name of our SQLite database file
DB_NAME = "todos.db"

# Create the Flask application instance
app = Flask(__name__)
app.secret_key = "todo_secret_key_2024"

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the todos table."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'General',
            tags TEXT,
            due_date DATE,
            priority TEXT DEFAULT 'Medium',
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    """Home page: Show all todos with sorting and filtering options."""
    conn = get_db_connection()
    
    # Get filter parameters
    category_filter = request.args.get('category', '')
    tag_filter = request.args.get('tag', '')
    priority_filter = request.args.get('priority', '')
    sort_by = request.args.get('sort', 'due_date')
    
    # Build the query
    query = "SELECT * FROM todos WHERE 1=1"
    params = []
    
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    
    if tag_filter:
        query += " AND tags LIKE ?"
        params.append(f'%{tag_filter}%')
    
    if priority_filter:
        query += " AND priority = ?"
        params.append(priority_filter)
    
    # Add sorting
    if sort_by == 'due_date':
        query += " ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC"
    elif sort_by == 'priority':
        query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END"
    elif sort_by == 'created_at':
        query += " ORDER BY created_at DESC"
    elif sort_by == 'title':
        query += " ORDER BY title ASC"
    
    todos = conn.execute(query, params).fetchall()
    
    # Get unique categories and tags for filter dropdowns
    categories = conn.execute("SELECT DISTINCT category FROM todos WHERE category IS NOT NULL").fetchall()
    all_tags = conn.execute("SELECT tags FROM todos WHERE tags IS NOT NULL AND tags != ''").fetchall()
    
    # Extract unique tags
    tags = set()
    for row in all_tags:
        if row['tags']:
            tags.update([tag.strip() for tag in row['tags'].split(',')])
    
    conn.close()
    
    return render_template("index.html", 
                         todos=todos, 
                         categories=categories, 
                         tags=sorted(tags),
                         current_filters={'category': category_filter, 'tag': tag_filter, 'priority': priority_filter, 'sort': sort_by})

@app.route("/create/", methods=("GET", "POST"))
def create():
    """Create a new todo."""
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        category = request.form["category"].strip()
        tags = request.form["tags"].strip()
        due_date = request.form["due_date"] if request.form["due_date"] else None
        priority = request.form["priority"]
        
        if not title:
            return render_template("create.html", error="Title is required!")
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO todos (title, description, category, tags, due_date, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, category, tags, due_date, priority)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for("index"))
    
    return render_template("create.html")

@app.route("/edit/<int:id>/", methods=("GET", "POST"))
def edit(id):
    """Edit an existing todo."""
    conn = get_db_connection()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (id,)).fetchone()
    
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        category = request.form["category"].strip()
        tags = request.form["tags"].strip()
        due_date = request.form["due_date"] if request.form["due_date"] else None
        priority = request.form["priority"]
        
        if not title:
            return render_template("edit.html", todo=todo, error="Title is required!")
        
        conn.execute(
            "UPDATE todos SET title = ?, description = ?, category = ?, tags = ?, due_date = ?, priority = ? WHERE id = ?",
            (title, description, category, tags, due_date, priority, id)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for("index"))
    
    conn.close()
    return render_template("edit.html", todo=todo)

@app.route("/delete/<int:id>/")
def delete(id):
    """Delete a todo."""
    conn = get_db_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/toggle/<int:id>/")
def toggle_complete(id):
    """Toggle the completion status of a todo."""
    conn = get_db_connection()
    todo = conn.execute("SELECT completed FROM todos WHERE id = ?", (id,)).fetchone()
    new_status = 0 if todo['completed'] else 1
    
    conn.execute("UPDATE todos SET completed = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

@app.route("/view/<int:id>/")
def view(id):
    """View a single todo in detail."""
    conn = get_db_connection()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (id,)).fetchone()
    conn.close()
    
    if todo is None:
        return redirect(url_for("index"))
    
    return render_template("view.html", todo=todo)

if __name__ == "__main__":
    # Initialize the database when the app starts
    init_db()
    app.run(debug=True)
