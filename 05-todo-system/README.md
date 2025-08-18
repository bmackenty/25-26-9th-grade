# Todo Manager

A simple, elegant todo-list application built with Flask and SQLite, featuring task management with categories, tags, priorities, and due dates.

## Features

- ✅ **Create, Read, Update, Delete** todos
- 🏷️ **Tag and categorize** todos for better organization
- 📅 **Due date tracking** with overdue indicators
- 🚨 **Priority levels** (High, Medium, Low) with color coding
- 🔍 **Advanced filtering** by category, tag, and priority
- 📊 **Multiple sorting options** (due date, priority, creation date, title)
- ✨ **Clean, modern interface** using Tailwind CSS
- 📱 **Responsive design** for all devices

## Screenshots

The application features a clean, intuitive interface with:
- Filter and sort controls at the top
- Beautiful todo cards with priority badges
- Easy-to-use forms for creating and editing
- Detailed view pages for each todo

## Installation & Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd 05-todo-system
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

## Database

The application automatically creates a SQLite database (`todos.db`) with the following structure:

```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'General',
    tags TEXT,
    due_date DATE,
    priority TEXT DEFAULT 'Medium',
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage

### Creating Todos
1. Click "Add Todo" from the navigation
2. Fill in the title (required)
3. Add optional description, category, tags, due date, and priority
4. Click "Create Todo"

### Managing Todos
- **View**: Click the eye icon to see full details
- **Edit**: Click the pencil icon to modify
- **Complete**: Click the checkbox to mark as done
- **Delete**: Click the trash icon (with confirmation)

### Filtering & Sorting
- **Category**: Filter by predefined categories
- **Tags**: Filter by specific tags
- **Priority**: Filter by priority level
- **Sort**: Order by due date, priority, creation date, or title

### Categories
Pre-defined categories include:
- General, Work, Personal, School
- Health, Finance, Shopping, Home

### Tags
Add multiple tags separated by commas:
- Example: `urgent, project, meeting`
- Tags are automatically extracted and available for filtering

## Project Structure

```
05-todo-system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Main todo list page
│   ├── create.html      # Create new todo form
│   ├── edit.html        # Edit existing todo form
│   ├── view.html        # View todo details
│   └── navbar.html      # Navigation component
└── todos.db             # SQLite database (auto-created)
```

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (lightweight, file-based)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Icons**: Heroicons (SVG icons)

## Customization

### Adding New Categories
Edit the `create.html` and `edit.html` templates to add new category options.

### Styling
The application uses Tailwind CSS classes. Modify the classes in the HTML templates to change the appearance.

### Database Schema
To add new fields, modify the `init_db()` function in `app.py` and update the corresponding templates.

## Contributing

This is a learning project designed for students. Feel free to:
- Add new features
- Improve the UI/UX
- Fix bugs
- Add tests

## License

This project is open source and available under the MIT License.
