# =====================================================
# IMPORTS
# These bring in Python modules and libraries our app needs.
# =====================================================

import os
# "os" lets us work with the operating system (paths, directories, environment variables).

import argparse
# "argparse" is used to handle command-line arguments (like --init-db).

import sqlite3
# "sqlite3" lets us talk directly to the SQLite database file.

from datetime import datetime
# "datetime" helps us work with dates and times (e.g., timestamps).

from flask import Flask, g, render_template, request, redirect, url_for, flash, session, abort
# "flask" is the main web framework we use.
# - Flask: the core app object.
# - g: a special object for storing data during a request (like db connection).
# - render_template: loads and fills in HTML files with data (Jinja templates).
# - request: access data sent by the browser (like form input).
# - redirect: send the browser to a different page.
# - url_for: build URLs to routes in a safe way.
# - flash: show temporary messages to the user (success, error, etc).
# - session: store small bits of data across requests (e.g., login state).
# - abort: stop a request with an error code (e.g., 404 Not Found).

from werkzeug.security import generate_password_hash, check_password_hash
# "werkzeug.security" provides safe password utilities:
# - generate_password_hash: encrypts (hashes) a plain password before saving.
# - check_password_hash: compares a plain password with the stored hash.


# =====================================================
# Flask + Tailwind (CDN) + Jinja + SQLite Starter
# =====================================================
# TEACHING NOTES:
# - Raw sqlite3 + schema.sql to keep things simple.
# - Passwords are hashed. Sessions keep track of login.
# - No CSRF to keep the starter minimal (add later!).
# - CRUD for 'items' + categories + tags (many-to-many).
# =====================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Absolute paths so Flask can’t “lose” the folder when run from different CWDs
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'db')
DB_PATH = os.path.join(DB_DIR, 'app.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
REQUIRED_TABLES = {"users", "categories", "tags", "items", "item_tags"}


def _schema_needs_init(conn: sqlite3.Connection) -> bool:
    """
    Returns True if any required table is missing.
    """
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    existing = {r["name"] if isinstance(r, sqlite3.Row) else r[0] for r in rows}
    return not REQUIRED_TABLES.issubset(existing)

def ensure_db():
    """
    Ensure the DB directory exists, the DB file exists, and the schema is applied.
    If the DB exists but is missing required tables, re-run schema.sql.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    # Open (and create if needed) the database
    first_time_create = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    # Nice to have: return dict-like rows if you ever reuse this conn
    conn.row_factory = sqlite3.Row

    # Enforce foreign keys per-connection (SQLite default is OFF)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Apply schema if this is a new file or required tables are missing
    if first_time_create or _schema_needs_init(conn):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()
        print(f"[INIT] Applied schema from {SCHEMA_PATH} -> {DB_PATH}")

    conn.close()

def get_db():
    """Get a SQLite connection. Auto-create DB and run schema if needed."""
    if 'db' not in g:
        ensure_db()  # <-- guarantees schema is present
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # enforce FKs for each request connection too
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def run_script(path):
    with app.app_context():
        db = get_db()
        with open(path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()

def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()

def login_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('Please log in first.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view_func(*args, **kwargs)
    return wrapped

@app.route('/')
def index():
    user = current_user()
    counts = None
    if user:
        db = get_db()
        counts = db.execute('''
            SELECT
              (SELECT COUNT(*) FROM items WHERE owner_id = ?) AS item_count,
              (SELECT COUNT(*) FROM categories) AS category_count,
              (SELECT COUNT(*) FROM tags) AS tag_count
        ''', (user['id'],)).fetchone()
    return render_template('index.html', user=user, counts=counts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/register.html')

        db = get_db()
        exists = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if exists:
            flash('That username is taken. Please choose another.', 'error')
            return render_template('auth/register.html')

        pw_hash = generate_password_hash(password)
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, pw_hash))
        db.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')

        session['user_id'] = user['id']
        flash(f'Welcome, {username}!', 'success')
        next_url = request.args.get('next')
        return redirect(next_url or url_for('index'))
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out. See you next time!', 'info')
    return redirect(url_for('index'))

@app.route('/items')
@login_required
def items_list():
    user = current_user()
    db = get_db()

    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id')
    tag_id = request.args.get('tag_id')

    SQL = '''
    SELECT i.*, c.name AS category_name
    FROM items i
    JOIN categories c ON c.id = i.category_id
    WHERE i.owner_id = ?
    '''
    params = [user['id']]

    if q:
        SQL += ' AND i.name LIKE ?'
        params.append(f'%{q}%')
    if category_id and category_id.isdigit():
        SQL += ' AND i.category_id = ?'
        params.append(int(category_id))
    if tag_id and tag_id.isdigit():
        SQL += '''
        AND i.id IN (
            SELECT it.item_id FROM item_tags it WHERE it.tag_id = ?
        )
        '''
        params.append(int(tag_id))

    SQL += ' ORDER BY i.created_at DESC'

    items = db.execute(SQL, tuple(params)).fetchall()
    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    tags = db.execute('SELECT * FROM tags ORDER BY name').fetchall()
    return render_template('items/list.html', items=items, categories=categories, tags=tags, q=q, category_id=category_id, tag_id=tag_id)

@app.route('/items/create', methods=['GET', 'POST'])
@login_required
def items_create():
    user = current_user()
    db = get_db()
    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    tags = db.execute('SELECT * FROM tags ORDER BY name').fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'active')
        category_id = request.form.get('category_id')
        selected_tags = request.form.getlist('tags')

        if not name or not category_id:
            flash('Name and category are required.', 'error')
            return render_template('items/create.html', categories=categories, tags=tags, form=request.form)

        db.execute('''
            INSERT INTO items (name, description, status, category_id, owner_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (name, description, status, int(category_id), user['id']))
        item_id = db.execute('SELECT last_insert_rowid() AS id').fetchone()['id']

        for t in selected_tags:
            if t.isdigit():
                db.execute('INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?, ?)', (item_id, int(t)))

        db.commit()
        flash('Item created!', 'success')
        return redirect(url_for('items_list'))

    return render_template('items/create.html', categories=categories, tags=tags, form=None)

@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def items_edit(item_id):
    user = current_user()
    db = get_db()

    item = db.execute('SELECT * FROM items WHERE id = ? AND owner_id = ?', (item_id, user['id'])).fetchone()
    if not item:
        abort(404)

    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    tags = db.execute('SELECT * FROM tags ORDER BY name').fetchall()
    item_tag_ids = {row['tag_id'] for row in db.execute('SELECT tag_id FROM item_tags WHERE item_id = ?', (item['id'],)).fetchall()}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'active')
        category_id = request.form.get('category_id')
        selected_tags = {int(t) for t in request.form.getlist('tags') if t.isdigit()}

        if not name or not category_id:
            flash('Name and category are required.', 'error')
            return render_template('items/edit.html', item=item, categories=categories, tags=tags, item_tag_ids=item_tag_ids, form=request.form)

        db.execute('''
            UPDATE items
            SET name = ?, description = ?, status = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_id = ?
        ''', (name, description, status, int(category_id), item_id, user['id']))

        to_remove = item_tag_ids - selected_tags
        to_add = selected_tags - item_tag_ids
        for tid in to_remove:
            db.execute('DELETE FROM item_tags WHERE item_id = ? AND tag_id = ?', (item_id, tid))
        for tid in to_add:
            db.execute('INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?, ?)', (item_id, tid))

        db.commit()
        flash('Item updated.', 'success')
        return redirect(url_for('items_list'))

    return render_template('items/edit.html', item=item, categories=categories, tags=tags, item_tag_ids=item_tag_ids, form=None)

@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def items_delete(item_id):
    user = current_user()
    db = get_db()
    db.execute('DELETE FROM items WHERE id = ? AND owner_id = ?', (item_id, user['id']))
    db.commit()
    flash('Item deleted.', 'info')
    return redirect(url_for('items_list'))

def parse_args():
    parser = argparse.ArgumentParser(description='Flask Starter Utilities')
    parser.add_argument('--init-db', action='store_true', help='Initialize (reset) the SQLite database using schema.sql')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.init_db:
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        os.makedirs(os.path.join(os.path.dirname(__file__), 'db'), exist_ok=True)
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        sqlite3.connect(DB_PATH).close()
        run_script(schema_path)
        print('Database initialized at', DB_PATH)
    else:
        app.run(debug=True)
