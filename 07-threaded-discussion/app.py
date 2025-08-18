from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import csv
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('discussion.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            reputation INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Threads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            is_pinned BOOLEAN DEFAULT 0,
            is_locked BOOLEAN DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    # Posts table (replies)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            parent_post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (thread_id) REFERENCES threads (id),
            FOREIGN KEY (parent_post_id) REFERENCES posts (id)
        )
    ''')
    
    # Votes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            thread_id INTEGER,
            post_id INTEGER,
            vote_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (thread_id) REFERENCES threads (id),
            FOREIGN KEY (post_id) REFERENCES posts (id),
            UNIQUE(user_id, thread_id, post_id)
        )
    ''')
    
    # Likes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            thread_id INTEGER,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (thread_id) REFERENCES threads (id),
            FOREIGN KEY (post_id) REFERENCES posts (id),
            UNIQUE(user_id, thread_id, post_id)
        )
    ''')
    
    # Attachments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            thread_id INTEGER,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (thread_id) REFERENCES threads (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    # Insert default categories
    cursor.execute('''
        INSERT OR IGNORE INTO categories (name, description) VALUES 
        ('General Discussion', 'General topics and conversations'),
        ('Technology', 'Tech-related discussions'),
        ('Help & Support', 'Questions and support requests'),
        ('Announcements', 'Important announcements and updates')
    ''')
    
    # Insert default admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES 
        ('admin', 'admin@example.com', 'admin123', 'admin')
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'latest')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT t.*, u.username, c.name as category_name,
               (SELECT COUNT(*) FROM posts WHERE thread_id = t.id) as reply_count,
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'upvote') - 
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'downvote') as vote_score
        FROM threads t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    '''
    params = []
    
    if category_id:
        query += ' AND t.category_id = ?'
        params.append(category_id)
    
    if search:
        query += ' AND (t.title LIKE ? OR t.content LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    # Add sorting
    if sort_by == 'latest':
        query += ' ORDER BY t.created_at DESC'
    elif sort_by == 'oldest':
        query += ' ORDER BY t.created_at ASC'
    elif sort_by == 'most_viewed':
        query += ' ORDER BY t.view_count DESC'
    elif sort_by == 'most_replied':
        query += ' ORDER BY reply_count DESC'
    elif sort_by == 'most_voted':
        query += ' ORDER BY vote_score DESC'
    else:
        query += ' ORDER BY t.created_at DESC'
    
    threads = conn.execute(query, params).fetchall()
    
    # Get categories for filter
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    
    # Get stats
    total_threads = conn.execute('SELECT COUNT(*) FROM threads').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_posts = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    
    conn.close()
    
    return render_template('index.html', 
                         threads=threads, 
                         categories=categories,
                         selected_category=category_id,
                         selected_sort=sort_by,
                         search=search,
                         stats={'threads': total_threads, 'users': total_users, 'posts': total_posts})

@app.route('/thread/<int:thread_id>')
def view_thread(thread_id):
    conn = get_db_connection()
    
    # Increment view count
    conn.execute('UPDATE threads SET view_count = view_count + 1 WHERE id = ?', (thread_id,))
    
    # Get thread details
    thread = conn.execute('''
        SELECT t.*, u.username, c.name as category_name,
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'upvote') - 
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'downvote') as vote_score
        FROM threads t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    ''', (thread_id,)).fetchone()
    
    if not thread:
        flash('Thread not found!', 'error')
        return redirect(url_for('index'))
    
    # Get posts with user info and vote counts
    posts = conn.execute('''
        SELECT p.*, u.username,
               (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = 'upvote') - 
               (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = 'downvote') as vote_score,
               (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.thread_id = ?
        ORDER BY p.created_at ASC
    ''', (thread_id,)).fetchall()
    
    # Get attachments for thread
    thread_attachments = conn.execute('''
        SELECT * FROM attachments WHERE thread_id = ?
    ''', (thread_id,)).fetchall()
    
    # Get attachments for posts
    post_attachments = {}
    for post in posts:
        post_attachments[post['id']] = conn.execute('''
            SELECT * FROM attachments WHERE post_id = ?
        ''', (post['id'],)).fetchall()
    
    conn.close()
    
    return render_template('view_thread.html', 
                         thread=thread, 
                         posts=posts,
                         thread_attachments=thread_attachments,
                         post_attachments=post_attachments)

@app.route('/thread/create', methods=['GET', 'POST'])
def create_thread():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category_id']
        
        if not title or not content or not category_id:
            flash('All fields are required!', 'error')
            return render_template('create_thread.html')
        
        conn = get_db_connection()
        
        # For demo purposes, use admin user (in real app, get from session)
        user_id = 1
        
        cursor = conn.execute('''
            INSERT INTO threads (title, content, user_id, category_id)
            VALUES (?, ?, ?, ?)
        ''', (title, content, user_id, category_id))
        
        thread_id = cursor.lastrowid
        
        # Handle file uploads
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(file_path)
                    
                    conn.execute('''
                        INSERT INTO attachments (filename, original_filename, file_path, file_size, mime_type, user_id, thread_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (new_filename, filename, file_path, os.path.getsize(file_path), file.content_type, user_id, thread_id))
        
        conn.commit()
        conn.close()
        
        flash('Thread created successfully!', 'success')
        return redirect(url_for('view_thread', thread_id=thread_id))
    
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    
    return render_template('create_thread.html', categories=categories)

@app.route('/thread/<int:thread_id>/reply', methods=['POST'])
def reply_to_thread(thread_id):
    content = request.form['content']
    
    if not content:
        flash('Reply content is required!', 'error')
        return redirect(url_for('view_thread', thread_id=thread_id))
    
    conn = get_db_connection()
    
    # For demo purposes, use admin user (in real app, get from session)
    user_id = 1
    
    cursor = conn.execute('''
        INSERT INTO posts (content, user_id, thread_id)
        VALUES (?, ?, ?)
    ''', (content, user_id, thread_id))
    
    post_id = cursor.lastrowid
    
    # Handle file uploads
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)
                
                conn.execute('''
                    INSERT INTO attachments (filename, original_filename, file_path, file_size, mime_type, user_id, post_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (new_filename, filename, file_path, os.path.getsize(file_path), file.content_type, user_id, post_id))
    
    conn.commit()
    conn.close()
    
    flash('Reply posted successfully!', 'success')
    return redirect(url_for('view_thread', thread_id=thread_id))

@app.route('/vote/<string:type>/<int:item_id>', methods=['POST'])
def vote(type, item_id):
    vote_type = request.form['vote_type']  # 'upvote' or 'downvote'
    
    conn = get_db_connection()
    
    # For demo purposes, use admin user (in real app, get from session)
    user_id = 1
    
    if type == 'thread':
        # Check if user already voted
        existing_vote = conn.execute('''
            SELECT * FROM votes WHERE user_id = ? AND thread_id = ?
        ''', (user_id, item_id)).fetchone()
        
        if existing_vote:
            # Update existing vote
            conn.execute('''
                UPDATE votes SET vote_type = ? WHERE user_id = ? AND thread_id = ?
            ''', (vote_type, user_id, item_id))
        else:
            # Create new vote
            conn.execute('''
                INSERT INTO votes (user_id, thread_id, vote_type)
                VALUES (?, ?, ?)
            ''', (user_id, item_id, vote_type))
    
    elif type == 'post':
        # Check if user already voted
        existing_vote = conn.execute('''
            SELECT * FROM votes WHERE user_id = ? AND post_id = ?
        ''', (user_id, item_id)).fetchone()
        
        if existing_vote:
            # Update existing vote
            conn.execute('''
                UPDATE votes SET vote_type = ? WHERE user_id = ? AND post_id = ?
            ''', (vote_type, user_id, item_id))
        else:
            # Create new vote
            conn.execute('''
                INSERT INTO votes (user_id, post_id, vote_type)
                VALUES (?, ?, ?)
            ''', (user_id, item_id, vote_type))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/like/<string:type>/<int:item_id>', methods=['POST'])
def like(type, item_id):
    conn = get_db_connection()
    
    # For demo purposes, use admin user (in real app, get from session)
    user_id = 1
    
    if type == 'thread':
        # Check if already liked
        existing_like = conn.execute('''
            SELECT * FROM likes WHERE user_id = ? AND thread_id = ?
        ''', (user_id, item_id)).fetchone()
        
        if existing_like:
            # Unlike
            conn.execute('''
                DELETE FROM likes WHERE user_id = ? AND thread_id = ?
            ''', (user_id, item_id))
            liked = False
        else:
            # Like
            conn.execute('''
                INSERT INTO likes (user_id, thread_id)
                VALUES (?, ?)
            ''', (user_id, item_id))
            liked = True
    
    elif type == 'post':
        # Check if already liked
        existing_like = conn.execute('''
            SELECT * FROM likes WHERE user_id = ? AND post_id = ?
        ''', (user_id, item_id)).fetchone()
        
        if existing_like:
            # Unlike
            conn.execute('''
                DELETE FROM likes WHERE user_id = ? AND post_id = ?
            ''', (user_id, item_id))
            liked = False
        else:
            # Like
            conn.execute('''
                INSERT INTO likes (user_id, post_id)
                VALUES (?, ?)
            ''', (user_id, item_id))
            liked = True
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'liked': liked})

@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    
    # Get stats
    total_threads = conn.execute('SELECT COUNT(*) FROM threads').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_posts = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    total_attachments = conn.execute('SELECT COUNT(*) FROM attachments').fetchone()[0]
    
    # Get recent activity
    recent_threads = conn.execute('''
        SELECT t.*, u.username FROM threads t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC LIMIT 5
    ''').fetchall()
    
    # Get top users by reputation
    top_users = conn.execute('''
        SELECT username, reputation FROM users
        ORDER BY reputation DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         stats={'threads': total_threads, 'users': total_users, 'posts': total_posts, 'attachments': total_attachments},
                         recent_threads=recent_threads,
                         top_users=top_users)

@app.route('/admin/threads')
def admin_threads():
    conn = get_db_connection()
    
    threads = conn.execute('''
        SELECT t.*, u.username, c.name as category_name,
               (SELECT COUNT(*) FROM posts WHERE thread_id = t.id) as reply_count
        FROM threads t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_threads.html', threads=threads)

@app.route('/admin/thread/<int:thread_id>/toggle_pin', methods=['POST'])
def toggle_pin_thread(thread_id):
    conn = get_db_connection()
    
    current_status = conn.execute('SELECT is_pinned FROM threads WHERE id = ?', (thread_id,)).fetchone()['is_pinned']
    new_status = 0 if current_status else 1
    
    conn.execute('UPDATE threads SET is_pinned = ? WHERE id = ?', (new_status, thread_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'pinned': bool(new_status)})

@app.route('/admin/thread/<int:thread_id>/toggle_lock', methods=['POST'])
def toggle_lock_thread(thread_id):
    conn = get_db_connection()
    
    current_status = conn.execute('SELECT is_locked FROM threads WHERE id = ?', (thread_id,)).fetchone()['is_locked']
    new_status = 0 if current_status else 1
    
    conn.execute('UPDATE threads SET is_locked = ? WHERE id = ?', (new_status, thread_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'locked': bool(new_status)})

@app.route('/admin/thread/<int:thread_id>/delete', methods=['POST'])
def delete_thread(thread_id):
    conn = get_db_connection()
    
    # Delete attachments first
    attachments = conn.execute('SELECT file_path FROM attachments WHERE thread_id = ?', (thread_id,)).fetchall()
    for attachment in attachments:
        try:
            os.remove(attachment['file_path'])
        except:
            pass
    
    # Delete votes, likes, posts, and attachments
    conn.execute('DELETE FROM votes WHERE thread_id = ?', (thread_id,))
    conn.execute('DELETE FROM likes WHERE thread_id = ?', (thread_id,))
    conn.execute('DELETE FROM attachments WHERE thread_id = ?', (thread_id,))
    conn.execute('DELETE FROM posts WHERE thread_id = ?', (thread_id,))
    conn.execute('DELETE FROM threads WHERE id = ?', (thread_id,))
    
    conn.commit()
    conn.close()
    
    flash('Thread deleted successfully!', 'success')
    return redirect(url_for('admin_threads'))

@app.route('/export/csv')
def export_csv():
    conn = get_db_connection()
    
    # Get all threads with user and category info
    threads = conn.execute('''
        SELECT t.*, u.username, c.name as category_name,
               (SELECT COUNT(*) FROM posts WHERE thread_id = t.id) as reply_count,
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'upvote') - 
               (SELECT COUNT(*) FROM votes WHERE thread_id = t.id AND vote_type = 'downvote') as vote_score
        FROM threads t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    # Get all posts
    posts = conn.execute('''
        SELECT p.*, u.username, t.title as thread_title
        FROM posts p
        JOIN users u ON p.user_id = u.id
        JOIN threads t ON p.thread_id = t.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write threads
    writer.writerow(['Threads'])
    writer.writerow(['ID', 'Title', 'Author', 'Category', 'Created', 'Replies', 'Views', 'Vote Score', 'Pinned', 'Locked'])
    for thread in threads:
        writer.writerow([
            thread['id'], thread['title'], thread['username'], 
            thread['category_name'], thread['created_at'], thread['reply_count'],
            thread['view_count'], thread['vote_score'], 
            'Yes' if thread['is_pinned'] else 'No',
            'Yes' if thread['is_locked'] else 'No'
        ])
    
    writer.writerow([])
    writer.writerow(['Posts'])
    writer.writerow(['ID', 'Content', 'Author', 'Thread', 'Created', 'Parent Post'])
    for post in posts:
        writer.writerow([
            post['id'], post['content'][:100] + '...' if len(post['content']) > 100 else post['content'],
            post['username'], post['thread_title'], post['created_at'],
            post['parent_post_id'] if post['parent_post_id'] else 'N/A'
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'discussion_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
