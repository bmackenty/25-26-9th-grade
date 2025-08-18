# Student Project Tracker

A comprehensive web application for teachers to manage classes, track student progress, and monitor project checkpoints with automatic deadline management and CSV export functionality.

## Features

- 🏫 **Class Management**: Create and manage classes with subjects and academic years
- 👥 **Student Management**: Add students to classes with email contact information
- 📋 **Project Creation**: Create projects with automatic checkpoint generation
- ⏰ **Automatic Checkpoints**: System generates checkpoints based on project duration
- 📊 **Progress Tracking**: Monitor individual student progress through checkpoints
- 🚨 **Overdue Alerts**: Visual indicators for late projects and submissions
- 📧 **Student Contact**: Quick access to student emails for communication
- 📈 **Dashboard Analytics**: Overview of classes, students, and project status
- 📤 **CSV Export**: Export comprehensive project data for external analysis
- 🎨 **Modern UI**: Clean, responsive interface using Tailwind CSS

## Screenshots

The application features:
- **Dashboard**: Overview statistics and recent activity
- **Class Management**: Create classes and view student rosters
- **Project Tracking**: Monitor progress with visual indicators
- **Student Progress**: Individual checkpoint tracking and status updates
- **CSV Export**: Comprehensive data export for reporting

## Installation & Setup

1. **Navigate to the project directory:**
   ```bash
   cd 06-student-project-tracker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open your browser and go to:**
   ```
   http://127.0.0.1:5000
   ```

## Database Schema

The application automatically creates a SQLite database with the following structure:

### Classes Table
```sql
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    class_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
```

### Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    class_id INTEGER NOT NULL,
    due_date DATE NOT NULL,
    total_points INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
```

### Checkpoints Table
```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_date DATE NOT NULL,
    points INTEGER DEFAULT 0,
    order_num INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);
```

### Submissions Table
```sql
CREATE TABLE submissions (
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
);
```

## Usage

### Getting Started
1. **Create Classes**: Start by adding classes for your subjects
2. **Add Students**: Enroll students in your classes
3. **Create Projects**: Assign projects with due dates
4. **Monitor Progress**: Track student progress through checkpoints

### Class Management
- **Create Class**: Add new classes with subject and academic year
- **View Class**: See enrolled students and assigned projects
- **Email Students**: Send bulk emails to all students in a class

### Student Management
- **Add Students**: Enroll students with contact information
- **Assign Classes**: Place students in appropriate classes
- **Contact Students**: Quick access to student emails

### Project Management
- **Create Projects**: Add projects with descriptions and due dates
- **Automatic Checkpoints**: System generates checkpoints based on duration
- **Progress Tracking**: Monitor individual student progress
- **Status Updates**: Update student checkpoint status and points

### Automatic Checkpoint Generation
The system automatically creates checkpoints based on project duration:

- **Short Projects (≤7 days)**: 2 checkpoints
  - Midpoint Review
  - Final Submission

- **Medium Projects (8-14 days)**: 3 checkpoints
  - Initial Progress
  - Midpoint Review
  - Final Submission

- **Long Projects (>14 days)**: 4 checkpoints
  - Initial Progress
  - Quarter Review
  - Midpoint Review
  - Final Submission

### Progress Tracking
- **Visual Indicators**: Progress bars and status badges
- **Checkpoint Status**: Pending, In Progress, Completed
- **Points Tracking**: Monitor earned vs. maximum points
- **Overdue Alerts**: Highlight late submissions

### CSV Export
Export comprehensive project data including:
- Class information
- Project details and due dates
- Student information and contact details
- Checkpoint status and due dates
- Submission status and points earned
- Timestamps for all activities

## Project Structure

```
06-student-project-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Dashboard overview
│   ├── classes.html     # Classes list
│   ├── create_class.html # Create new class form
│   ├── view_class.html  # Class details view
│   ├── students.html    # Students list
│   ├── create_student.html # Create new student form
│   ├── projects.html    # Projects list
│   ├── create_project.html # Create new project form
│   └── view_project.html # Project details and progress
└── student_tracker.db    # SQLite database (auto-created)
```

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (lightweight, file-based)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Charts**: Chart.js for data visualization
- **Icons**: Heroicons (SVG icons)

## Key Features Explained

### Dashboard Overview
- **Statistics Cards**: Quick view of classes, students, and projects
- **Recent Projects**: Latest project assignments
- **Students to Contact**: Overdue submissions requiring attention
- **Overdue Projects**: Projects past their due dates
- **Project Status Chart**: Visual representation of project status

### Student Contact Management
- **Email Integration**: Direct mailto links for student communication
- **Bulk Email**: Send emails to entire classes
- **Overdue Notifications**: Identify students needing follow-up

### Progress Tracking
- **Checkpoint System**: Break projects into manageable milestones
- **Status Updates**: Track completion of individual checkpoints
- **Points System**: Monitor earned vs. maximum points
- **Visual Progress**: Progress bars and status indicators

### CSV Export
- **Comprehensive Data**: Export all project and student information
- **Formatted Output**: Clean, organized data for external analysis
- **Date Stamping**: Automatic filename with current date
- **Excel Compatible**: CSV format works with spreadsheet applications

## Customization

### Adding New Fields
To add new fields to students, projects, or classes:
1. Modify the `init_db()` function in `app.py`
2. Update corresponding templates
3. Add form handling in routes

### Styling Changes
The application uses Tailwind CSS classes. Modify classes in HTML templates to change appearance.

### Checkpoint Logic
Customize checkpoint generation by modifying the `create_checkpoints()` function in `app.py`.

## Contributing

This is a learning project designed for teachers and students. Feel free to:
- Add new features
- Improve the UI/UX
- Fix bugs
- Add tests
- Enhance reporting capabilities

## License

This project is open source and available under the MIT License.

## Support

For questions or issues:
1. Check the documentation above
2. Review the code comments
3. Test with sample data first
4. Ensure all dependencies are installed

## Future Enhancements

Potential improvements could include:
- **Email Notifications**: Automated reminders for upcoming deadlines
- **Grade Calculation**: Automatic grade computation
- **Student Portal**: Student login to view their own progress
- **File Uploads**: Support for project file submissions
- **Advanced Reporting**: More detailed analytics and charts
- **Mobile App**: Native mobile application
- **API Integration**: Connect with other educational systems
