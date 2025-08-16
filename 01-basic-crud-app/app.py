"""
app.py: A minimal Flask + SQLite CRUD app for beginners.

Why this file?
- Shows explicit routing, templating (Jinja2), and SQL (sqlite3).
- Keeps everything in one place to reduce cognitive load for new programmers.
- Auto-creates the SQLite database & table if they don't exist.

JINJA TEMPLATING CONCEPTS FOR STUDENTS:
========================================

1. WHAT IS JINJA?
   - Jinja2 is a template engine that lets us mix HTML with Python-like code
   - It allows us to create dynamic web pages that change based on data

2. HOW IT WORKS:
   - Flask (Python) prepares data and passes it to templates
   - Templates use special syntax to display that data
   - The result is HTML that gets sent to the browser

3. KEY JINJA SYNTAX:
   - {{ variable }} - Display a variable's value
   - {% if condition %}...{% endif %} - Conditional statements
   - {% for item in list %}...{% endfor %} - Loops
   - {% extends "base.html" %} - Template inheritance
   - {% block name %}...{% endblock %} - Define blocks for inheritance

4. DATA FLOW EXAMPLE:
   - Python: items = [{"name": "Apple", "description": "Red fruit"}]
   - Template: {% for item in items %}{{ item['name'] }}{% endfor %}
   - Result: Apple

5. WHY USE TEMPLATES?
   - Separate logic (Python) from presentation (HTML)
   - Reuse common elements (navigation, footer)
   - Make pages dynamic based on data
   - Keep code organized and maintainable

How to run:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000/
"""

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3  # Built-in Python module for SQLite databases

# Name of our SQLite database file (will be created on first run)
DB_NAME = "database.db"

# Create the Flask application instance
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for session management

def get_db_connection():
    """
    Create and return a connection to the SQLite database.

    Why row_factory?
    - It lets us access columns by name (e.g., row["name"]) instead of by index (row[0]).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    """
    HOME PAGE (READ): Show a list of all items in the database.
    - SQL: SELECT * FROM items
    - Template: templates/index.html
    
    JINJA TEMPLATING EXAMPLE:
    - We pass 'items' variable to the template: render_template("index.html", items=items)
    - In the template, we can access this as {{ items }} or loop through it with {% for item in items %}
    - Each 'item' is a database row that we can access like item['name'], item['description']
    """
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    return render_template("index.html", items=items)

@app.route("/create/", methods=("GET", "POST"))
def create():
    """
    CREATE: Show a form (GET) and insert a new item (POST).
    - On GET: render the form
    - On POST: INSERT into the database and redirect to "/"
    
    JINJA TEMPLATING EXAMPLE:
    - GET request: render_template("create.html") - no variables passed, template shows empty form
    - POST request: After saving, redirect to index page (no template rendering needed)
    - The create.html template will have form fields that submit to this same route
    """
    if request.method == "POST":
        # Get data the user typed in the form fields named "name" and "description"
        name = request.form["name"].strip()
        description = request.form["description"].strip()

        # Very basic validation for beginners
        if not name or not description:
            # In a later lesson, you could add flash() messages and display feedback.
            return redirect(url_for("create"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO items (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        conn.close()

        # After saving, go back to the list page
        return redirect(url_for("index"))

    # If the method is GET, just show the empty form
    return render_template("create.html")

@app.route("/<int:item_id>/edit/", methods=("GET", "POST"))
def edit(item_id):
    """
    UPDATE: Show a form pre-filled with the existing item, then save changes.
    - GET: SELECT the item and show the form
    - POST: UPDATE the item, then redirect to "/"
    
    JINJA TEMPLATING EXAMPLE:
    - GET request: render_template("edit.html", item=item) - passes 'item' variable to template
    - In edit.html, we can pre-fill form fields like: value="{{ item['name'] }}"
    - This allows users to see and modify existing data instead of starting with empty fields
    """
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if not item:
        # If item doesn't exist, go back to the list (basic handling for beginners)
        conn.close()
        return redirect(url_for("index"))

    if request.method == "POST":
        new_name = request.form["name"].strip()
        new_description = request.form["description"].strip()

        if new_name and new_description:
            conn.execute(
                "UPDATE items SET name = ?, description = ? WHERE id = ?",
                (new_name, new_description, item_id)
            )
            conn.commit()

        conn.close()
        return redirect(url_for("index"))

    conn.close()
    # Show the form with existing values
    return render_template("edit.html", item=item)

@app.route("/<int:item_id>/delete/", methods=("POST",))
def delete(item_id):
    """
    DELETE: Remove an item. We use POST to avoid accidental deletes via URL.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/search")
def search():
    """
    SEARCH: Find items whose name or description contains the query string.
    - SQL: SELECT * FROM items WHERE name LIKE ? OR description LIKE ?
    - Template: templates/search_results.html
    
    JINJA TEMPLATING EXAMPLE:
    - We pass TWO variables: query (the search term) and results (the found items)
    - render_template("search_results.html", query=query, results=results)
    - In the template, we can show the search term: "Results for: {{ query }}"
    - And loop through results: {% for item in results %} to display each found item
    """
    query = request.args.get("q", "").strip()
    results = []
    if query:
        conn = get_db_connection()
        like_query = f"%{query}%"
        results = conn.execute(
            "SELECT * FROM items WHERE name LIKE ? OR description LIKE ?",
            (like_query, like_query)
        ).fetchall()
        conn.close()
    return render_template("search_results.html", query=query, results=results)

@app.route("/<int:item_id>/")
def view(item_id):
    """
    VIEW: Show a single item's details.
    - SQL: SELECT * FROM items WHERE id = ?
    - Template: templates/view.html
    
    JINJA TEMPLATING EXAMPLE:
    - We pass a single 'item' variable: render_template("view.html", item=item)
    - In the template, we can access item properties: {{ item['name'] }}, {{ item['description'] }}
    - This is useful for showing detailed information about one specific record
    """
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if item is None:
        return render_template("404.html"), 404
    return render_template("view.html", item=item)

@app.route("/about")
def about():
    """
    ABOUT PAGE: Show information about the project.
    - Template: templates/about.html
    """
    return render_template("about.html")

def create_contact_table():
    """
    Create the contact_messages table if it doesn't exist.
    """
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

@app.route("/contact", methods=("GET", "POST"))
def contact():
    """
    CONTACT PAGE: Show a contact form and handle submissions.
    - Template: templates/contact.html
    - Saves messages to the contact_messages table.
    
    JINJA TEMPLATING EXAMPLE:
    - We pass a 'success' variable: render_template("contact.html", success=success)
    - In the template, we can show success messages: {% if success %}Thank you!{% endif %}
    - This allows us to give user feedback after form submission
    """
    success = False
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if name and email and message:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                (name, email, message)
            )
            conn.commit()
            conn.close()
            success = True
    return render_template("contact.html", success=success)

def create_users_table():
    """
    Create the users table if it doesn't exist.
    """
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('guest', 'admin'))
        )
        """
    )
    conn.commit()
    conn.close()

@app.route("/register", methods=("GET", "POST"))
def register():
    """
    REGISTER: Show registration form and handle user registration.
    - Template: templates/register.html
    - Saves new user to the users table.
    
    JINJA TEMPLATING EXAMPLE:
    - We pass TWO variables: success and error
    - render_template("register.html", success=success, error=error)
    - In the template, we can show different messages:
    - {% if success %}Registration successful!{% endif %}
    - {% if error %}{{ error }}{% endif %}
    - This pattern allows us to handle both success and error cases
    """
    success = False
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        status = request.form.get("status", "guest").strip()
        if not username or not password or status not in ("guest", "admin"):
            error = "All fields are required and status must be guest or admin."
        else:
            try:
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO users (username, password, status) VALUES (?, ?, ?)",
                    (username, password, status)
                )
                conn.commit()
                conn.close()
                success = True
            except sqlite3.IntegrityError:
                error = "Username already exists."
    return render_template("register.html", success=success, error=error)

@app.route("/login", methods=("GET", "POST"))
def login():
    """
    LOGIN: Show login form and handle user authentication.
    - Template: templates/login.html
    - Uses session to remember logged-in user.
    
    JINJA TEMPLATING EXAMPLE:
    - We pass an 'error' variable: render_template("login.html", error=error)
    - In the template, we can show error messages: {% if error %}{{ error }}{% endif %}
    - If no error, the template shows the login form; if error, it shows the form + error message
    """
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["status"] = user["status"]
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    """
    LOGOUT: Clear the session and show a logout confirmation.
    - Template: templates/logout.html
    """
    session.clear()
    return render_template("logout.html")

@app.route("/admin")
def admin_dashboard():
    """
    ADMIN DASHBOARD: Only accessible to admin users.
    Shows contact messages and user management.
    
    JINJA TEMPLATING EXAMPLE:
    - We pass TWO variables: messages and users
    - render_template("admin_dashboard.html", messages=messages, users=users)
    - In the template, we can loop through both:
    - {% for message in messages %} to show contact messages
    - {% for user in users %} to show user list
    - This demonstrates passing multiple data sets to one template
    """
    if not session.get("user_id") or session.get("status") != "admin":
        return redirect(url_for("login"))
    conn = get_db_connection()
    messages = conn.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()
    users = conn.execute("SELECT * FROM users ORDER BY username ASC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", messages=messages, users=users)

@app.route("/admin/user/<int:user_id>/edit/", methods=("GET", "POST"))
def edit_user(user_id):
    """
    EDIT USER: Admin can change a user's status and password.
    
    JINJA TEMPLATING EXAMPLE:
    - We pass THREE variables: user, error, and success
    - render_template("edit_user.html", user=user, error=error, success=success)
    - In the template, we can:
    - Show user info: {{ user['username'] }}, {{ user['status'] }}
    - Display errors: {% if error %}{{ error }}{% endif %}
    - Show success: {% if success %}User updated!{% endif %}
    - This shows how to handle multiple types of feedback in one template
    """
    if not session.get("user_id") or session.get("status") != "admin":
        return redirect(url_for("login"))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    error = None
    success = False
    if not user:
        conn.close()
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        status = request.form.get("status", "guest")
        password = request.form.get("password", "").strip()
        if status not in ("guest", "admin"):
            error = "Invalid status."
        else:
            if password:
                conn.execute(
                    "UPDATE users SET status = ?, password = ? WHERE id = ?",
                    (status, password, user_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET status = ? WHERE id = ?",
                    (status, user_id)
                )
            conn.commit()
            success = True
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template("edit_user.html", user=user, error=error, success=success)

if __name__ == "__main__":
    # On startup: create the database tables if they don't exist.
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    create_contact_table()
    create_users_table()

    # Start the Flask development server
    # debug=True auto-reloads when you save changes; great for learning.
    app.run(debug=True)
