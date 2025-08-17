from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "school_store_secret_key_2024"

# Database configuration
DB_NAME = "school_store.db"

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables for the school store system."""
    conn = get_db_connection()
    
    # Users table - store staff and admin users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff' CHECK(role IN ('admin', 'staff')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table - for organizing products
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)
    
    # Products table - store inventory items
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            category_id INTEGER,
            sku TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)
    
    # Sales table - track all transactions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'cash',
            status TEXT NOT NULL DEFAULT 'completed' CHECK(status IN ('completed', 'refunded', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Sale items table - individual items in each sale
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Insert default categories
    default_categories = [
        ('School Supplies', 'Pens, pencils, notebooks, and other school essentials'),
        ('Electronics', 'Calculators, headphones, and electronic devices'),
        ('Clothing', 'School uniforms, t-shirts, and accessories'),
        ('Food & Drinks', 'Snacks, beverages, and cafeteria items'),
        ('Books', 'Textbooks, novels, and reference materials')
    ]
    
    for category in default_categories:
        conn.execute("""
            INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)
        """, category)
    
    # Insert default admin user if none exists
    admin_exists = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
    if admin_exists == 0:
        conn.execute("""
            INSERT INTO users (username, email, password, role) 
            VALUES (?, ?, ?, ?)
        """, ('admin', 'admin@schoolstore.com', 'admin123', 'admin'))
    
    conn.commit()
    conn.close()

def migrate_database():
    """Add new columns to existing database tables."""
    conn = get_db_connection()
    
    try:
        # Check if any new columns need to be added
        cursor = conn.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'min_stock_level' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN min_stock_level INTEGER DEFAULT 5")
            print("✅ Added min_stock_level column to products table")
        
        if 'sku' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN sku TEXT")
            print("✅ Added sku column to products table")
        
        conn.commit()
        print("✅ Database migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error during database migration: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_transaction_id():
    """Generate a unique transaction ID for sales."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"TXN{timestamp}"

# Routes
@app.route('/')
def index():
    """Home page with quick stats and recent activity."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get quick stats
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    low_stock_products = conn.execute("""
        SELECT COUNT(*) FROM products WHERE stock_quantity <= min_stock_level
    """).fetchone()[0]
    
    # Get recent sales
    recent_sales = conn.execute("""
        SELECT s.*, u.username as cashier_name
        FROM sales s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        LIMIT 5
    """).fetchall()
    
    # Get low stock alerts
    low_stock_items = conn.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.stock_quantity <= p.min_stock_level
        ORDER BY p.stock_quantity ASC
        LIMIT 5
    """).fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales,
                         low_stock_items=low_stock_items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        user = conn.execute("""
            SELECT * FROM users WHERE username = ? AND password = ?
        """, (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/inventory')
def inventory():
    """Display all products in inventory."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', '')
    
    # Build query
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.sku LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    
    query += " ORDER BY p.name"
    
    products = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    
    conn.close()
    
    return render_template('inventory.html', products=products, categories=categories)

@app.route('/inventory/add', methods=['GET', 'POST'])
def add_product():
    """Add a new product to inventory."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        cost = request.form.get('cost')
        stock_quantity = request.form.get('stock_quantity', 0)
        min_stock_level = request.form.get('min_stock_level', 5)
        category_id = request.form.get('category_id')
        sku = request.form.get('sku', '')
        
        # Validate required fields
        if not name or not price or not cost:
            flash('Name, price, and cost are required', 'error')
            return redirect(url_for('add_product'))
        
        try:
            price = float(price)
            cost = float(cost)
            stock_quantity = int(stock_quantity)
            min_stock_level = int(min_stock_level)
        except ValueError:
            flash('Invalid numeric values', 'error')
            return redirect(url_for('add_product'))
        
        conn = get_db_connection()
        
        # Generate SKU if not provided
        if not sku:
            sku = f"SKU{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Insert the product
        conn.execute("""
            INSERT INTO products (name, description, price, cost, stock_quantity, min_stock_level, category_id, sku)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, cost, stock_quantity, min_stock_level, category_id, sku))
        
        conn.commit()
        conn.close()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('inventory'))
    
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    
    return render_template('add_product.html', categories=categories)

@app.route('/inventory/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Edit an existing product."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        cost = request.form.get('cost')
        stock_quantity = request.form.get('stock_quantity', 0)
        min_stock_level = request.form.get('min_stock_level', 5)
        category_id = request.form.get('category_id')
        sku = request.form.get('sku', '')
        
        # Validate required fields
        if not name or not price or not cost:
            flash('Name, price, and cost are required', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        
        try:
            price = float(price)
            cost = float(cost)
            stock_quantity = int(stock_quantity)
            min_stock_level = int(min_stock_level)
        except ValueError:
            flash('Invalid numeric values', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        
        # Update the product
        conn.execute("""
            UPDATE products 
            SET name = ?, description = ?, price = ?, cost = ?, stock_quantity = ?, 
                min_stock_level = ?, category_id = ?, sku = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, description, price, cost, stock_quantity, min_stock_level, category_id, sku, product_id))
        
        conn.commit()
        conn.close()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('inventory'))
    
    product = conn.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,)).fetchone()
    
    if not product:
        conn.close()
        flash('Product not found', 'error')
        return redirect(url_for('inventory'))
    
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    
    return render_template('edit_product.html', product=product, categories=categories)

@app.route('/pos')
def pos():
    """Point of sale interface."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    products = conn.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.stock_quantity > 0
        ORDER BY p.name
    """).fetchall()
    conn.close()
    
    return render_template('pos.html', products=products)

@app.route('/pos/checkout', methods=['POST'])
def checkout():
    """Process a sale transaction."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    data = request.get_json()
    items = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    
    if not items:
        return jsonify({'success': False, 'message': 'No items in cart'})
    
    conn = get_db_connection()
    
    try:
        # Calculate total
        total_amount = sum(item['quantity'] * item['price'] for item in items)
        
        # Create sale record
        transaction_id = generate_transaction_id()
        cursor = conn.execute("""
            INSERT INTO sales (transaction_id, user_id, total_amount, payment_method)
            VALUES (?, ?, ?, ?)
        """, (transaction_id, session['user_id'], total_amount, payment_method))
        
        sale_id = cursor.lastrowid
        
        # Add sale items and update inventory
        for item in items:
            # Insert sale item
            conn.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, item['id'], item['quantity'], item['price'], item['quantity'] * item['price']))
            
            # Update product stock
            conn.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (item['quantity'], item['id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Sale completed successfully!',
            'transaction_id': transaction_id,
            'total_amount': total_amount
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Error processing sale: {str(e)}'})

@app.route('/analytics')
def analytics():
    """Sales analytics and reporting."""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get date range from query parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build date filter
    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = "WHERE DATE(s.created_at) BETWEEN ? AND ?"
        params = [start_date, end_date]
    
    # Get sales summary
    sales_summary = conn.execute(f"""
        SELECT 
            COUNT(*) as total_sales,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_sale,
            SUM(total_amount) - (
                SELECT SUM(si.quantity * p.cost)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s2 ON si.sale_id = s2.id
                {date_filter.replace('s.', 's2.') if date_filter else ''}
            ) as total_profit
        FROM sales s
        {date_filter}
    """, params).fetchone()
    
    # Get top selling products
    top_products = conn.execute(f"""
        SELECT 
            p.name,
            p.sku,
            SUM(si.quantity) as total_sold,
            SUM(si.total_price) as total_revenue
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        {date_filter}
        GROUP BY p.id, p.name, p.sku
        ORDER BY total_sold DESC
        LIMIT 10
    """, params).fetchall()
    
    # Get sales by category
    category_sales = conn.execute(f"""
        SELECT 
            c.name as category_name,
            SUM(si.quantity) as total_sold,
            SUM(si.total_price) as total_revenue
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN sales s ON si.sale_id = s.id
        {date_filter}
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC
    """, params).fetchall()
    
    # Get daily sales for chart
    daily_sales = conn.execute(f"""
        SELECT 
            DATE(s.created_at) as date,
            COUNT(*) as sales_count,
            SUM(s.total_amount) as daily_revenue
        FROM sales s
        {date_filter}
        GROUP BY DATE(s.created_at)
        ORDER BY date DESC
        LIMIT 30
    """, params).fetchall()
    
    conn.close()
    
    return render_template('analytics.html',
                         sales_summary=sales_summary,
                         top_products=top_products,
                         category_sales=category_sales,
                         daily_sales=daily_sales,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for managing the store."""
    if not session.get('user_id') or session.get('role') != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    # Get system stats
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    low_stock_count = conn.execute("""
        SELECT COUNT(*) FROM products WHERE stock_quantity <= min_stock_level
    """).fetchone()[0]
    
    # Get recent activity
    recent_sales = conn.execute("""
        SELECT s.*, u.username as cashier_name
        FROM sales s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_sales=total_sales,
                         low_stock_count=low_stock_count,
                         recent_sales=recent_sales)

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run database migration to add new columns
    migrate_database()
    
    # Start the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
