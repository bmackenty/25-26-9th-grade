"""
helpdesk_app.py: A comprehensive help desk ticket management system for students.

This application demonstrates:
- User authentication and role-based access control
- Complex database relationships (users, tickets, responses)
- Advanced Jinja templating with two-column layouts
- Different Tailwind CSS styling for visual variety
- Ticket workflow management (status, priority, categories)

Learning Objectives:
- Flask sessions for authentication
- SQLite for database management
- Advanced Jinja template inheritance
- Modern UI/UX design patterns
- RESTful API design principles
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "helpdesk_secret_key_2024"

# Database configuration
DB_NAME = "helpdesk.db"

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer', 'agent', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT DEFAULT 'blue'
        )
    """)
    
    # Tickets table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
            priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
            category_id INTEGER,
            customer_id INTEGER NOT NULL,
            assigned_agent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (assigned_agent_id) REFERENCES users (id)
        )
    """)
    
    # Responses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Insert default data
    try:
        # Default categories
        categories = [
            ('Technical Support', 'Hardware and software issues', 'red'),
            ('Account Issues', 'Login, password, and account problems', 'blue'),
            ('Billing', 'Payment and subscription questions', 'green'),
            ('Feature Request', 'Suggestions for new features', 'purple'),
            ('General', 'Other questions and inquiries', 'gray')
        ]
        
        for name, desc, color in categories:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, description, color) VALUES (?, ?, ?)",
                (name, desc, color)
            )
        
        # Default admin user
        conn.execute(
            "INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ('admin', 'admin@helpdesk.com', 'admin123', 'admin')
        )
        
        conn.commit()
    except Exception as e:
        print(f"Error inserting default data: {e}")
    
    conn.close()

# Routes
@app.route('/')
def index():
    """Home page with dashboard overview."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Get ticket statistics based on user role
    if user['role'] == 'admin':
        total_tickets = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        open_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'").fetchone()[0]
        in_progress = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'in_progress'").fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'resolved'").fetchone()[0]
    elif user['role'] == 'agent':
        total_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE assigned_agent_id = ?", (user['id'],)).fetchone()[0]
        open_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE assigned_agent_id = ? AND status = 'open'", (user['id'],)).fetchone()[0]
        in_progress = conn.execute("SELECT COUNT(*) FROM tickets WHERE assigned_agent_id = ? AND status = 'in_progress'", (user['id'],)).fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE assigned_agent_id = ? AND status = 'resolved'", (user['id'],)).fetchone()[0]
    else:  # customer
        total_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE customer_id = ?", (user['id'],)).fetchone()[0]
        open_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE customer_id = ? AND status = 'open'", (user['id'],)).fetchone()[0]
        in_progress = conn.execute("SELECT COUNT(*) FROM tickets WHERE customer_id = ? AND status = 'in_progress'", (user['id'],)).fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE customer_id = ? AND status = 'resolved'", (user['id'],)).fetchone()[0]
    
    # Get recent tickets
    if user['role'] in ['admin', 'agent']:
        recent_tickets = conn.execute("""
            SELECT t.*, u.username as customer_name, c.name as category_name 
            FROM tickets t 
            JOIN users u ON t.customer_id = u.id 
            LEFT JOIN categories c ON t.category_id = c.id 
            ORDER BY t.updated_at DESC LIMIT 5
        """).fetchall()
    else:
        recent_tickets = conn.execute("""
            SELECT t.*, c.name as category_name 
            FROM tickets t 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE t.customer_id = ? 
            ORDER BY t.updated_at DESC LIMIT 5
        """, (user['id'],)).fetchall()
    
    conn.close()
    
    stats = {
        'total': total_tickets,
        'open': open_tickets,
        'in_progress': in_progress,
        'resolved': resolved
    }
    
    return render_template('index.html', user=user, stats=stats, recent_tickets=recent_tickets)

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
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, password, 'customer')
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/tickets')
def tickets():
    """List all tickets with filtering."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    category_filter = request.args.get('category', '')
    
    # Build query based on user role
    if user['role'] == 'admin':
        query = """
            SELECT t.*, u.username as customer_name, u2.username as agent_name, c.name as category_name 
            FROM tickets t 
            JOIN users u ON t.customer_id = u.id 
            LEFT JOIN users u2 ON t.assigned_agent_id = u2.id 
            LEFT JOIN categories c ON t.category_id = c.id
        """
        params = []
    elif user['role'] == 'agent':
        query = """
            SELECT t.*, u.username as customer_name, c.name as category_name 
            FROM tickets t 
            JOIN users u ON t.customer_id = u.id 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE t.assigned_agent_id = ?
        """
        params = [user['id']]
    else:  # customer
        query = """
            SELECT t.*, c.name as category_name 
            FROM tickets t 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE t.customer_id = ?
        """
        params = [user['id']]
    
    # Add filters
    where_clauses = []
    if status_filter:
        where_clauses.append("t.status = ?")
        params.append(status_filter)
    if priority_filter:
        where_clauses.append("t.priority = ?")
        params.append(priority_filter)
    if category_filter:
        where_clauses.append("t.category_id = ?")
        params.append(category_filter)
    
    if where_clauses:
        query += " AND " + " AND ".join(where_clauses)
    
    query += " ORDER BY t.updated_at DESC"
    
    tickets = conn.execute(query, params).fetchall()
    
    # Get categories for filter dropdown
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    
    conn.close()
    
    return render_template('tickets.html', tickets=tickets, categories=categories, user=user)

@app.route('/tickets/new', methods=['GET', 'POST'])
def new_ticket():
    """Create a new ticket."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        priority = request.form.get('priority')
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO tickets (title, description, category_id, priority, customer_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, category_id, priority, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Ticket created successfully!', 'success')
        return redirect(url_for('tickets'))
    
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    
    return render_template('new_ticket.html', categories=categories)

@app.route('/tickets/<int:ticket_id>')
def view_ticket(ticket_id):
    """View a specific ticket and its responses."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # Get ticket with related information
    ticket = conn.execute("""
        SELECT t.*, u.username as customer_name, u2.username as agent_name, c.name as category_name 
        FROM tickets t 
        JOIN users u ON t.customer_id = u.id 
        LEFT JOIN users u2 ON t.assigned_agent_id = u2.id 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.id = ?
    """, (ticket_id,)).fetchone()
    
    if not ticket:
        conn.close()
        flash('Ticket not found', 'error')
        return redirect(url_for('tickets'))
    
    # Check if user can view this ticket
    if user['role'] == 'customer' and ticket['customer_id'] != user['id']:
        conn.close()
        flash('Access denied', 'error')
        return redirect(url_for('tickets'))
    
    # Get responses
    responses = conn.execute("""
        SELECT r.*, u.username 
        FROM responses r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.ticket_id = ? 
        ORDER BY r.created_at ASC
    """, (ticket_id,)).fetchall()
    
    # Get agents for assignment (admin only)
    agents = None
    if user['role'] == 'admin':
        agents = conn.execute("SELECT * FROM users WHERE role = 'agent' ORDER BY username").fetchall()
    
    conn.close()
    
    return render_template('view_ticket.html', ticket=ticket, responses=responses, user=user, agents=agents)

@app.route('/tickets/<int:ticket_id>/respond', methods=['POST'])
def respond_to_ticket(ticket_id):
    """Add a response to a ticket."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    message = request.form.get('message')
    if not message:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    conn = get_db_connection()
    
    # Check if user can respond to this ticket
    ticket = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        flash('Ticket not found', 'error')
        return redirect(url_for('tickets'))
    
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if user['role'] == 'customer' and ticket['customer_id'] != user['id']:
        conn.close()
        flash('Access denied', 'error')
        return redirect(url_for('tickets'))
    
    # Add response
    conn.execute("""
        INSERT INTO responses (ticket_id, user_id, message) 
        VALUES (?, ?, ?)
    """, (ticket_id, session['user_id'], message))
    
    # Update ticket status if agent responds
    if user['role'] in ['agent', 'admin'] and ticket['status'] == 'open':
        conn.execute("UPDATE tickets SET status = 'in_progress' WHERE id = ?", (ticket_id,))
    
    # Update ticket timestamp
    conn.execute("UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
    
    conn.commit()
    conn.close()
    
    flash('Response added successfully!', 'success')
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/tickets/<int:ticket_id>/update', methods=['POST'])
def update_ticket(ticket_id):
    """Update ticket status, priority, or assignment (admin/agent only)."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if user['role'] not in ['agent', 'admin']:
        conn.close()
        flash('Access denied', 'error')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    # Update ticket fields
    status = request.form.get('status')
    priority = request.form.get('priority')
    assigned_agent_id = request.form.get('assigned_agent_id')
    
    updates = []
    params = []
    
    if status:
        updates.append("status = ?")
        params.append(status)
    if priority:
        updates.append("priority = ?")
        params.append(priority)
    if assigned_agent_id and user['role'] == 'admin':
        updates.append("assigned_agent_id = ?")
        params.append(assigned_agent_id)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?"
        params.append(ticket_id)
        
        conn.execute(query, params)
        conn.commit()
        flash('Ticket updated successfully!', 'success')
    
    conn.close()
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for system overview."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get system statistics
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_tickets = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    open_tickets = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'").fetchone()[0]
    
    # Get recent tickets
    recent_tickets = conn.execute("""
        SELECT t.*, u.username as customer_name, c.name as category_name 
        FROM tickets t 
        JOIN users u ON t.customer_id = u.id 
        LEFT JOIN categories c ON t.category_id = c.id 
        ORDER BY t.created_at DESC LIMIT 10
    """).fetchall()
    
    # Get user statistics
    customers = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
    agents = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'agent'").fetchone()[0]
    
    conn.close()
    
    stats = {
        'total_users': total_users,
        'customers': customers,
        'agents': agents,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets
    }
    
    return render_template('admin_dashboard.html', stats=stats, recent_tickets=recent_tickets, user=user)

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Start the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
