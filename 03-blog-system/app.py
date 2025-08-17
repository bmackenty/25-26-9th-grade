"""
blog_app.py: A modern blogging platform for students to learn Flask and web development.

This application demonstrates:
- Blog post creation, editing, and management
- User authentication and author profiles
- Comment system with moderation
- Tag-based categorization
- Search functionality
- Rich text editing (simulated with markdown-style formatting)
- Different visual design using Tailwind CSS

Learning Objectives:
- Flask routing and request handling
- Database relationships (users, posts, comments, tags)
- Jinja templating with complex data structures
- User input validation and sanitization
- Search and filtering functionality
- Modern web design patterns

Student Notes:
- This app shows how the same Flask framework can create completely different applications
- Notice the different database schema and user interface design
- Compare this to the CRUD app and help desk system to see Flask's versatility
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import os
import re
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "blog_secret_key_2024"

# Image upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database configuration
DB_NAME = "blog.db"

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables for the blog system."""
    conn = get_db_connection()
    
    # Users table - stores author information
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT,
            avatar TEXT DEFAULT 'default-avatar.png',
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table - for organizing blog posts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT DEFAULT 'indigo'
        )
    """)
    
    # Tags table - for flexible post labeling
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT 'gray'
        )
    """)
    
    # Posts table - the main blog content
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            slug TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'published' CHECK(status IN ('draft', 'published', 'archived')),
            featured BOOLEAN DEFAULT 0,
            category_id INTEGER,
            author_id INTEGER NOT NULL,
            view_count INTEGER DEFAULT 0,
            featured_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    """)
    
    # Post tags relationship table (many-to-many)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (post_id, tag_id),
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
    """)
    
    # Comments table - for user discussions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parent_id INTEGER,
            content TEXT NOT NULL,
            is_approved BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (parent_id) REFERENCES comments (id)
        )
    """)
    
    # Add featured_image column if it doesn't exist (database migration)
    try:
        conn.execute("ALTER TABLE posts ADD COLUMN featured_image TEXT")
        print("Added featured_image column to posts table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("featured_image column already exists")
        else:
            print(f"Error adding featured_image column: {e}")
    
    # Insert default data
    try:
        # Default categories
        categories = [
            ('Technology', 'Latest tech trends and tutorials', 'blue'),
            ('Travel', 'Adventures and travel tips', 'green'),
            ('Food', 'Recipes and culinary experiences', 'orange'),
            ('Lifestyle', 'Personal development and wellness', 'purple'),
            ('Education', 'Learning resources and insights', 'indigo')
        ]
        
        for name, desc, color in categories:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, description, color) VALUES (?, ?, ?)",
                (name, desc, color)
            )
        
        # Default tags
        tags = [
            ('python', 'teal'),
            ('flask', 'blue'),
            ('webdev', 'green'),
            ('tutorial', 'yellow'),
            ('tips', 'orange'),
            ('beginner', 'purple')
        ]
        
        for name, color in tags:
            conn.execute(
                "INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)",
                (name, color)
            )
        
        # Default admin user
        conn.execute(
            "INSERT OR IGNORE INTO users (username, email, password, bio, is_admin) VALUES (?, ?, ?, ?, ?)",
            ('admin', 'admin@blog.com', 'admin123', 'Blog administrator and tech enthusiast', 1)
        )
        
        # Sample blog post
        conn.execute("""
            INSERT OR IGNORE INTO posts (title, content, excerpt, slug, status, featured, category_id, author_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Welcome to Our Blog!',
            'This is our first blog post. Welcome to our platform where we share insights about technology, education, and more.\n\n## Getting Started\n\nThis blog is built with Flask and demonstrates modern web development practices.\n\n### Features\n- User authentication\n- Post management\n- Comment system\n- Tag-based organization\n\nWe hope you enjoy reading our content!',
            'Welcome to our new blog platform built with Flask!',
            'welcome-to-our-blog',
            'published',
            1,
            1,
            1
        ))
        
        conn.commit()
    except Exception as e:
        print(f"Error inserting default data: {e}")
    
    conn.close()

def migrate_database():
    """Add new columns to existing database tables."""
    conn = get_db_connection()
    
    try:
        # Check if featured_image column exists
        cursor = conn.execute("PRAGMA table_info(posts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'featured_image' not in columns:
            conn.execute("ALTER TABLE posts ADD COLUMN featured_image TEXT")
            print("✅ Added featured_image column to posts table")
        else:
            print("✅ featured_image column already exists")
        
        conn.commit()
        print("✅ Database migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error during database migration: {e}")
        conn.rollback()
    finally:
        conn.close()

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(file):
    """Validate image file for security and size."""
    # Check if file exists and has a name
    if not file or file.filename == '':
        return False, "No file selected"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Check file extension
    if not allowed_file(file.filename):
        return False, "Invalid file type. Please upload PNG, JPG, GIF, or WebP images only"
    
    return True, "File is valid"

def create_slug(title):
    """Convert a title to a URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def format_content(content):
    """Convert markdown-style content to HTML for display."""
    # This is a simple markdown parser - in production you'd use a library like markdown2
    # Convert headers
    content = re.sub(r'^### (.*$)', r'<h3 class="text-lg font-semibold mt-4 mb-2">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2 class="text-xl font-bold mt-6 mb-3">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1 class="text-2xl font-bold mt-8 mb-4">\1</h1>', content, flags=re.MULTILINE)
    
    # Convert bold and italic
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    
    # Convert line breaks to paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []
    for p in paragraphs:
        if p.strip():
            if p.startswith('<h'):
                formatted_paragraphs.append(p)
            else:
                formatted_paragraphs.append(f'<p class="mb-4 leading-relaxed">{p}</p>')
    
    return '\n'.join(formatted_paragraphs)

# Routes
@app.route('/')
def index():
    """Home page showing featured and recent blog posts."""
    conn = get_db_connection()
    
    # Get featured posts (posts marked as featured)
    featured_posts = conn.execute("""
        SELECT p.*, u.username as author_name, c.name as category_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.status = 'published' AND p.featured = 1
        ORDER BY p.created_at DESC LIMIT 3
    """).fetchall()
    
    # Get recent published posts
    recent_posts = conn.execute("""
        SELECT p.*, u.username as author_name, c.name as category_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.status = 'published'
        ORDER BY p.created_at DESC LIMIT 6
    """).fetchall()
    
    # Get categories for navigation
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    
    # Get popular tags
    tags = conn.execute("""
        SELECT t.*, COUNT(pt.post_id) as post_count
        FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        JOIN posts p ON pt.post_id = p.id
        WHERE p.status = 'published'
        GROUP BY t.id
        ORDER BY post_count DESC
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         featured_posts=featured_posts, 
                         recent_posts=recent_posts,
                         categories=categories,
                         tags=tags)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('Login successful! Welcome back!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out. Come back soon!', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio', '')
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, bio) VALUES (?, ?, ?, ?)",
                (username, email, password, bio)
            )
            conn.commit()
            flash('Registration successful! Please login to start blogging.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/posts')
def posts():
    """List all published blog posts with filtering and search."""
    conn = get_db_connection()
    
    # Get filter parameters from URL query string
    category_filter = request.args.get('category', '')
    tag_filter = request.args.get('tag', '')
    search_query = request.args.get('search', '')
    
    # Build the base query for posts
    # Show published posts to everyone, drafts only to their authors
    query = """
        SELECT p.*, u.username as author_name, c.name as category_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.status = 'published' OR (p.status = 'draft' AND p.author_id = ?)
    """
    params = [session.get('user_id', 0)]
    
    # Add category filter if specified
    if category_filter:
        query += " AND c.name = ?"
        params.append(category_filter)
    
    # Add tag filter if specified
    if tag_filter:
        query += " AND p.id IN (SELECT pt.post_id FROM post_tags pt JOIN tags t ON pt.tag_id = t.id WHERE t.name = ?)"
        params.append(tag_filter)
    
    # Add search filter if specified
    if search_query:
        query += " AND (p.title LIKE ? OR p.content LIKE ? OR p.excerpt LIKE ?)"
        search_pattern = f'%{search_query}%'
        params.extend([search_pattern, search_pattern, search_pattern])
    
    query += " ORDER BY p.created_at DESC"
    
    # Execute the query
    posts = conn.execute(query, params).fetchall()
    
    # Get categories and tags for filter dropdowns
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    tags = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
    
    conn.close()
    
    return render_template('posts.html', 
                         posts=posts, 
                         categories=categories, 
                         tags=tags,
                         current_category=category_filter,
                         current_tag=tag_filter,
                         search_query=search_query)

@app.route('/posts/new', methods=['GET', 'POST'])
def new_post():
    """Create a new blog post (requires login)."""
    if not session.get('user_id'):
        flash('Please login to create a new post', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt', '')
        category_id = request.form.get('category_id')
        action = request.form.get('action', 'draft')
        featured = request.form.get('featured', 0)
        tags_input = request.form.get('tags', '')
        
        # Set status based on action button clicked
        status = 'published' if action == 'published' else 'draft'
        
        # Validate required fields
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('new_post'))
        
        # Handle image upload
        featured_image = None
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and file.filename != '':
                try:
                    # Validate the image file
                    is_valid, message = validate_image_file(file)
                    if not is_valid:
                        flash(message, 'error')
                        return redirect(url_for('new_post'))
                    
                    # Secure the filename and create unique name
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Save the file
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    featured_image = f"uploads/{filename}"
                    
                except Exception as e:
                    flash(f'Error uploading image: {str(e)}', 'error')
                    return redirect(url_for('new_post'))
        
        conn = get_db_connection()
        
        # Create slug from title
        slug = create_slug(title)
        
        # Insert the post
        cursor = conn.execute("""
            INSERT INTO posts (title, content, excerpt, slug, status, featured, category_id, author_id, featured_image) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, content, excerpt, slug, status, featured, category_id, session['user_id'], featured_image))
        
        post_id = cursor.lastrowid
        
        # Handle tags
        if tags_input:
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                # Create tag if it doesn't exist
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()[0]
                
                # Link tag to post
                conn.execute("INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)", (post_id, tag_id))
        
        conn.commit()
        conn.close()
        
        # Show appropriate message based on action
        if action == 'published':
            flash('Post published successfully!', 'success')
        else:
            flash('Draft saved successfully! You can edit and publish it later.', 'info')
        
        return redirect(url_for('view_post', slug=slug))
    
    # GET request - show the form
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    tags = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
    conn.close()
    
    return render_template('new_post.html', categories=categories, tags=tags)

@app.route('/posts/<slug>')
def view_post(slug):
    """View a specific blog post and its comments."""
    conn = get_db_connection()
    
    # Get the post with author and category information
    # Allow viewing published posts or drafts by the author
    post = conn.execute("""
        SELECT p.*, u.username as author_name, u.bio as author_bio, c.name as category_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.slug = ? AND (p.status = 'published' OR (p.status = 'draft' AND p.author_id = ?))
    """, (slug, session.get('user_id', 0))).fetchone()
    
    if not post:
        conn.close()
        flash('Post not found', 'error')
        return redirect(url_for('posts'))
    
    # Increment view count
    conn.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = ?", (post['id'],))
    
    # Get post tags
    tags = conn.execute("""
        SELECT t.* FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = ?
    """, (post['id'],)).fetchall()
    
    # Get approved comments
    comments = conn.execute("""
        SELECT c.*, u.username, u.avatar
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ? AND c.is_approved = 1 AND c.parent_id IS NULL
        ORDER BY c.created_at ASC
    """, (post['id'],)).fetchall()
    
    # Convert sqlite3.Row objects to dictionaries and get replies for each comment
    comments_list = []
    for comment in comments:
        comment_dict = dict(comment)
        replies = conn.execute("""
            SELECT c.*, u.username, u.avatar
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.parent_id = ? AND c.is_approved = 1
            ORDER BY c.created_at ASC
        """, (comment_dict['id'],)).fetchall()
        
        # Convert replies to dictionaries too
        replies_list = [dict(reply) for reply in replies]
        comment_dict['replies'] = replies_list
        comments_list.append(comment_dict)
    
    # Get related posts (same category)
    related_posts = conn.execute("""
        SELECT p.*, u.username as author_name
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.category_id = ? AND p.id != ? AND p.status = 'published'
        ORDER BY p.created_at DESC
        LIMIT 3
    """, (post['category_id'], post['id'])).fetchall()
    
    conn.commit()
    conn.close()
    
    # Format the content for display
    formatted_content = format_content(post['content'])
    
    return render_template('view_post.html', 
                         post=post, 
                         tags=tags, 
                         comments=comments_list,
                         related_posts=related_posts,
                         formatted_content=formatted_content)

@app.route('/posts/<slug>/comment', methods=['POST'])
def add_comment(slug):
    """Add a comment to a blog post."""
    if not session.get('user_id'):
        flash('Please login to comment', 'error')
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('view_post', slug=slug))
    
    conn = get_db_connection()
    
    # Get the post ID
    post = conn.execute("SELECT id FROM posts WHERE slug = ?", (slug,)).fetchone()
    if not post:
        conn.close()
        flash('Post not found', 'error')
        return redirect(url_for('posts'))
    
    # Insert the comment
    conn.execute("""
        INSERT INTO comments (post_id, user_id, parent_id, content) 
        VALUES (?, ?, ?, ?)
    """, (post['id'], session['user_id'], parent_id, content))
    
    conn.commit()
    conn.close()
    
    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_post', slug=slug))

@app.route('/profile')
def profile():
    """User profile page showing their posts and information."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Get user's posts
    posts = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM posts p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.author_id = ? 
        ORDER BY p.created_at DESC
    """, (session['user_id'],)).fetchall()
    
    # Get user's comments
    comments = conn.execute("""
        SELECT c.*, p.title as post_title, p.slug as post_slug
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
        LIMIT 10
    """, (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('profile.html', user=user, posts=posts, comments=comments)

@app.route('/posts/<slug>/delete', methods=['POST'])
def delete_post(slug):
    """Delete a blog post (requires login and ownership or admin status)."""
    if not session.get('user_id'):
        flash('Please login to delete posts', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get the post to check ownership
    post = conn.execute("""
        SELECT p.*, u.username as author_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        WHERE p.slug = ?
    """, (slug,)).fetchone()
    
    if not post:
        conn.close()
        flash('Post not found', 'error')
        return redirect(url_for('posts'))
    
    # Check if user owns the post
    if post['author_id'] != session['user_id']:
        conn.close()
        flash('You can only delete your own posts', 'error')
        return redirect(url_for('view_post', slug=slug))
    
    # Delete related data first (foreign key constraints)
    # Delete comments
    conn.execute("DELETE FROM comments WHERE post_id = ?", (post['id'],))
    
    # Delete post tags
    conn.execute("DELETE FROM post_tags WHERE post_id = ?", (post['id'],))
    
    # Delete the post
    conn.execute("DELETE FROM posts WHERE id = ?", (post['id'],))
    
    conn.commit()
    conn.close()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('posts'))

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for managing the blog."""
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get system statistics
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    pending_comments = conn.execute("SELECT COUNT(*) FROM comments WHERE is_approved = 0").fetchone()[0]
    
    # Get recent posts
    recent_posts = conn.execute("""
        SELECT p.*, u.username as author_name 
        FROM posts p 
        JOIN users u ON p.author_id = u.id 
        ORDER BY p.created_at DESC LIMIT 5
    """).fetchall()
    
    # Get recent comments
    recent_comments = conn.execute("""
        SELECT c.*, u.username, p.title as post_title 
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN posts p ON c.post_id = p.id
        ORDER BY c.created_at DESC LIMIT 5
    """).fetchall()
    
    conn.close()
    
    stats = {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'pending_comments': pending_comments
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run database migration to add new columns
    migrate_database()
    
    # Start the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
