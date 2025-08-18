"""
app.py: A Flask student project tracker application for teachers.

Features:
- Manage classes and students
- Create projects with due dates
- Automatic checkpoint generation
- Track project status (late, on time, completed)
- Generate reports and CSV exports
- Visual project status dashboard

How to run:
    python3 -m venv venv
    source venv/bin/activate (or venv\Scripts\activate on Windows)
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000/
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import sqlite3
from datetime import datetime, date, timedelta
import csv
import io
import os

# Name of our SQLite database file
DB_NAME = "student_tracker.db"

# Create the Flask application instance
app = Flask(__name__)
app.secret_key = "student_tracker_secret_key_2024"

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the required tables."""
    conn = get_db_connection()
    
    # Classes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Students table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            class_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
    ''')
    
    # Projects table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            class_id INTEGER NOT NULL,
            due_date DATE NOT NULL,
            total_points INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
    ''')
    
    # Checkpoints table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date DATE NOT NULL,
            points INTEGER DEFAULT 0,
            order_num INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    
    # Student project submissions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            checkpoint_id INTEGER,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP,
            points_earned INTEGER DEFAULT 0,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (checkpoint_id) REFERENCES checkpoints (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_checkpoints(project_id, due_date, total_points):
    """Automatically create checkpoints for a project."""
    conn = get_db_connection()
    
    # Calculate checkpoint dates and points
    project_start = date.today()
    project_end = datetime.strptime(due_date, '%Y-%m-%d').date()
    days_duration = (project_end - project_start).days
    
    if days_duration <= 7:
        # Short project: 2 checkpoints
        checkpoint_dates = [
            project_start + timedelta(days=days_duration // 2),
            project_end
        ]
        checkpoint_points = [total_points // 2, total_points // 2]
        checkpoint_titles = ["Midpoint Review", "Final Submission"]
    elif days_duration <= 14:
        # Medium project: 3 checkpoints
        checkpoint_dates = [
            project_start + timedelta(days=days_duration // 3),
            project_start + timedelta(days=2 * days_duration // 3),
            project_end
        ]
        checkpoint_points = [total_points // 3, total_points // 3, total_points // 3]
        checkpoint_titles = ["Initial Progress", "Midpoint Review", "Final Submission"]
    else:
        # Long project: 4 checkpoints
        checkpoint_dates = [
            project_start + timedelta(days=days_duration // 4),
            project_start + timedelta(days=days_duration // 2),
            project_start + timedelta(days=3 * days_duration // 4),
            project_end
        ]
        checkpoint_points = [total_points // 4, total_points // 4, total_points // 4, total_points // 4]
        checkpoint_titles = ["Initial Progress", "Quarter Review", "Midpoint Review", "Final Submission"]
    
    # Create checkpoints
    for i, (checkpoint_date, points, title) in enumerate(zip(checkpoint_dates, checkpoint_points, checkpoint_titles)):
        conn.execute('''
            INSERT INTO checkpoints (project_id, title, due_date, points, order_num)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, title, checkpoint_date.strftime('%Y-%m-%d'), points, i + 1))
    
    conn.commit()
    conn.close()

@app.route("/")
def index():
    """Home page: Dashboard with overview of classes and projects."""
    conn = get_db_connection()
    
    # Get basic counts
    class_count = conn.execute("SELECT COUNT(*) as count FROM classes").fetchone()['count']
    student_count = conn.execute("SELECT COUNT(*) as count FROM students").fetchone()['count']
    project_count = conn.execute("SELECT COUNT(*) as count FROM projects").fetchone()['count']
    
    # Get recent projects
    recent_projects = conn.execute('''
        SELECT p.*, c.name as class_name, 
               (SELECT COUNT(*) FROM students WHERE class_id = p.class_id) as student_count
        FROM projects p
        JOIN classes c ON p.class_id = c.id
        ORDER BY p.due_date ASC
        LIMIT 5
    ''').fetchall()
    
    # Get overdue projects
    overdue_projects = conn.execute('''
        SELECT p.*, c.name as class_name
        FROM projects p
        JOIN classes c ON p.class_id = c.id
        WHERE p.due_date < date('now')
        ORDER BY p.due_date ASC
    ''').fetchall()
    
    # Get students to contact (overdue submissions)
    students_to_contact = conn.execute('''
        SELECT DISTINCT s.first_name, s.last_name, s.email, c.name as class_name,
               p.title as project_title, cp.title as checkpoint_title, cp.due_date
        FROM students s
        JOIN classes c ON s.class_id = c.id
        JOIN projects p ON s.class_id = p.class_id
        JOIN checkpoints cp ON p.id = cp.project_id
        LEFT JOIN submissions sub ON (s.id = sub.student_id AND cp.id = sub.checkpoint_id)
        WHERE cp.due_date < date('now') 
        AND (sub.id IS NULL OR sub.status = 'pending')
        ORDER BY cp.due_date ASC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template("index.html", 
                         class_count=class_count,
                         student_count=student_count,
                         project_count=project_count,
                         recent_projects=recent_projects,
                         overdue_projects=overdue_projects,
                         students_to_contact=students_to_contact)

@app.route("/classes/")
def classes():
    """List all classes."""
    conn = get_db_connection()
    classes = conn.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM students WHERE class_id = c.id) as student_count,
               (SELECT COUNT(*) FROM projects WHERE class_id = c.id) as project_count
        FROM classes c
        ORDER BY c.academic_year DESC, c.name ASC
    ''').fetchall()
    conn.close()
    
    return render_template("classes.html", classes=classes)

@app.route("/classes/create/", methods=("GET", "POST"))
def create_class():
    """Create a new class."""
    if request.method == "POST":
        name = request.form["name"].strip()
        subject = request.form["subject"].strip()
        academic_year = request.form["academic_year"].strip()
        
        if not name or not subject or not academic_year:
            return render_template("create_class.html", error="All fields are required!")
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO classes (name, subject, academic_year) VALUES (?, ?, ?)",
            (name, subject, academic_year)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for("classes"))
    
    return render_template("create_class.html")

@app.route("/classes/<int:class_id>/")
def view_class(class_id):
    """View a specific class with students and projects."""
    conn = get_db_connection()
    
    class_info = conn.execute("SELECT * FROM classes WHERE id = ?", (class_id,)).fetchone()
    if not class_info:
        return redirect(url_for("classes"))
    
    students = conn.execute("SELECT * FROM students WHERE class_id = ? ORDER BY last_name, first_name", (class_id,)).fetchall()
    projects = conn.execute("SELECT * FROM projects WHERE class_id = ? ORDER BY due_date ASC", (class_id,)).fetchall()
    
    conn.close()
    
    return render_template("view_class.html", 
                         class_info=class_info, 
                         students=students, 
                         projects=projects)

@app.route("/students/")
def students():
    """List all students."""
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.last_name, s.first_name
    ''').fetchall()
    conn.close()
    
    return render_template("students.html", students=students)

@app.route("/students/create/", methods=("GET", "POST"))
def create_student():
    """Create a new student."""
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip()
        class_id = request.form["class_id"] if request.form["class_id"] else None
        
        if not first_name or not last_name:
            return render_template("create_student.html", error="First and last names are required!")
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO students (first_name, last_name, email, class_id) VALUES (?, ?, ?, ?)",
            (first_name, last_name, email, class_id)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for("students"))
    
    conn = get_db_connection()
    classes = conn.execute("SELECT * FROM classes ORDER BY name").fetchall()
    conn.close()
    
    return render_template("create_student.html", classes=classes)

@app.route("/projects/")
def projects():
    """List all projects."""
    conn = get_db_connection()
    projects = conn.execute('''
        SELECT p.*, c.name as class_name,
               (SELECT COUNT(*) FROM students WHERE class_id = p.class_id) as total_students,
               (SELECT COUNT(*) FROM submissions s 
                JOIN students st ON s.student_id = st.id 
                WHERE st.class_id = p.class_id AND s.project_id = p.id AND s.status = 'completed') as completed_submissions
        FROM projects p
        JOIN classes c ON p.class_id = c.id
        ORDER BY p.due_date ASC
    ''').fetchall()
    conn.close()
    
    return render_template("projects.html", projects=projects)

@app.route("/projects/create/", methods=("GET", "POST"))
def create_project():
    """Create a new project."""
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        class_id = request.form["class_id"]
        due_date = request.form["due_date"]
        total_points = int(request.form["total_points"])
        
        if not title or not class_id or not due_date:
            return render_template("create_project.html", error="Title, class, and due date are required!")
        
        conn = get_db_connection()
        cursor = conn.execute(
            "INSERT INTO projects (title, description, class_id, due_date, total_points) VALUES (?, ?, ?, ?, ?)",
            (title, description, class_id, due_date, total_points)
        )
        project_id = cursor.lastrowid
        
        # Create automatic checkpoints
        create_checkpoints(project_id, due_date, total_points)
        
        conn.commit()
        conn.close()
        
        return redirect(url_for("projects"))
    
    conn = get_db_connection()
    classes = conn.execute("SELECT * FROM classes ORDER BY name").fetchall()
    conn.close()
    
    return render_template("create_project.html", classes=classes)

@app.route("/projects/<int:project_id>/")
def view_project(project_id):
    """View a specific project with checkpoints and student progress."""
    conn = get_db_connection()
    
    project = conn.execute('''
        SELECT p.*, c.name as class_name
        FROM projects p
        JOIN classes c ON p.class_id = c.id
        WHERE p.id = ?
    ''', (project_id,)).fetchone()
    
    if not project:
        return redirect(url_for("projects"))
    
    checkpoints = conn.execute('''
        SELECT * FROM checkpoints 
        WHERE project_id = ? 
        ORDER BY order_num
    ''', (project_id,)).fetchall()
    
    students = conn.execute('''
        SELECT s.*, 
               (SELECT COUNT(*) FROM submissions sub 
                WHERE sub.student_id = s.id AND sub.project_id = ? AND sub.status = 'completed') as completed_checkpoints
        FROM students s
        WHERE s.class_id = ?
        ORDER BY s.last_name, s.first_name
    ''', (project_id, project['class_id'])).fetchall()
    
    conn.close()
    
    return render_template("view_project.html", 
                         project=project, 
                         checkpoints=checkpoints, 
                         students=students)

@app.route("/export/csv/")
def export_csv():
    """Export project data to CSV."""
    conn = get_db_connection()
    
    # Get all project data
    data = conn.execute('''
        SELECT 
            c.name as class_name,
            p.title as project_title,
            p.due_date as project_due_date,
            s.first_name,
            s.last_name,
            s.email,
            cp.title as checkpoint_title,
            cp.due_date as checkpoint_due_date,
            sub.status,
            sub.points_earned,
            cp.points as max_points,
            sub.submitted_at
        FROM projects p
        JOIN classes c ON p.class_id = c.id
        JOIN students s ON s.class_id = c.id
        JOIN checkpoints cp ON p.id = cp.project_id
        LEFT JOIN submissions sub ON (s.id = sub.student_id AND cp.id = sub.checkpoint_id)
        ORDER BY c.name, p.title, s.last_name, s.first_name, cp.order_num
    ''').fetchall()
    
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Class', 'Project', 'Project Due Date', 'Student First Name', 'Student Last Name', 
        'Email', 'Checkpoint', 'Checkpoint Due Date', 'Status', 'Points Earned', 
        'Max Points', 'Submitted At'
    ])
    
    # Write data
    for row in data:
        writer.writerow([
            row['class_name'], row['project_title'], row['project_due_date'],
            row['first_name'], row['last_name'], row['email'], row['checkpoint_title'],
            row['checkpoint_due_date'], row['status'] or 'Not Started',
            row['points_earned'] or 0, row['max_points'], row['submitted_at'] or 'Not Submitted'
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'student_project_tracker_{date.today()}.csv'
    )

@app.route("/api/update_submission/", methods=["POST"])
def update_submission():
    """Update a student's submission status."""
    data = request.get_json()
    student_id = data.get('student_id')
    checkpoint_id = data.get('checkpoint_id')
    status = data.get('status')
    points_earned = data.get('points_earned', 0)
    feedback = data.get('feedback', '')
    
    conn = get_db_connection()
    
    # Check if submission exists
    existing = conn.execute('''
        SELECT * FROM submissions 
        WHERE student_id = ? AND checkpoint_id = ?
    ''', (student_id, checkpoint_id)).fetchone()
    
    if existing:
        # Update existing submission
        conn.execute('''
            UPDATE submissions 
            SET status = ?, points_earned = ?, feedback = ?, submitted_at = ?
            WHERE student_id = ? AND checkpoint_id = ?
        ''', (status, points_earned, feedback, datetime.now(), student_id, checkpoint_id))
    else:
        # Create new submission
        conn.execute('''
            INSERT INTO submissions (student_id, checkpoint_id, status, points_earned, feedback, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, checkpoint_id, status, points_earned, feedback, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

if __name__ == "__main__":
    # Initialize the database when the app starts
    init_db()
    app.run(debug=True)
