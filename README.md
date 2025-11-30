# Flask Learning Projects for 9th Grade Students

A collection of Flask web applications designed to teach students web development fundamentals through hands-on projects. The projects are templates designed to be modified for real-world problems.

##  Learning Objectives

Students will learn:
- **Flask Framework**: Routing, request handling, and response generation
- **Jinja2 Templating**: Dynamic HTML generation and template inheritance
- **SQLite Databases**: CRUD operations and data relationships
- **User Authentication**: Login systems and session management
- **Modern Web Development**: HTML forms, CSS styling, and JavaScript interactivity
- **Database Schema Management**: Safe database updates and migrations
- **Form Handling**: Text inputs, textareas, and dropdown selections

## Project Structure

```
25-26-9th-grade/
├── 01-basic-crud-app/           # Basic CRUD operations
├── 02-helpdesk-system/          # Help desk ticket management
├── 03-blog-system/              # Blog with user posts and file uploads
├── 04-school-store/             # Point of sale system with inventory
├── 05-todo-system/              # Task management application
├── 06-student-project-tracker/  # Track student projects and classes
├── 07-threaded-discussion/      # Forum-style discussion system
├── solution_template_project_one/ # Complete template with all features
└── README.md                    # This file
```

## 🎓 Solution Template Project

**Start Here!** The `solution_template_project_one/` folder contains a complete Flask application with all the features students will learn:

### 🚀 Quick Start
```bash
cd solution_template_project_one
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5000/ in your browser

### ✨ New Features Added

#### 📝 Form Demo with Dropdown Lists
Learn how different form elements work:
- **Text inputs** - Single line text entry
- **Textareas** - Multi-line text entry  
- **Dropdown/Select lists** - Choose from preset options

Visit `/form_demo` to see how form data flows from HTML → Flask → Results page.

#### 🗄️ Safe Database Schema Updates
New tools to help you modify your database safely:
- **`update_database.py`** - Validates and applies schema changes
- **Automatic backups** - Keeps your data safe
- **Clear error messages** - Helps you fix problems
- **No command line arguments needed** - Just run `python3 update_database.py`

See `HOWTO Update Database Schema` for complete instructions.

## 📚 Individual Learning Projects

### Project 1: Basic CRUD Application
**Difficulty**: Beginner | **Focus**: Core Flask concepts
- Create, read, update, delete operations
- Basic form handling
- SQLite database operations

### Project 2: Help Desk System  
**Difficulty**: Beginner-Intermediate | **Focus**: User workflows
- Ticket creation and tracking
- Status management
- User authentication

### Project 3: Blog System
**Difficulty**: Intermediate | **Focus**: File uploads & content
- User posts and profiles
- File upload handling
- Content management

### Project 4: School Store
**Difficulty**: Intermediate | **Focus**: Business logic
- Point of sale system
- Inventory management
- Sales analytics

### Project 5: Todo System
**Difficulty**: Beginner | **Focus**: Task management
- Personal task tracking
- Priority and status management
- Simple, focused interface

### Project 6: Student Project Tracker
**Difficulty**: Intermediate-Advanced | **Focus**: Relationships
- Multi-table relationships
- Complex data structures
- Class and project management

### Project 7: Threaded Discussion
**Difficulty**: Advanced | **Focus**: Complex interactions
- Forum-style discussions
- Threaded conversations
- Advanced user interactions

### Setup Instructions (for any project)
```bash
cd [project-folder-name]
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```



## 🔧 Technical Stack

### Backend
- **Flask**: Python web framework
- **SQLite**: Lightweight database
- **Python**: Core programming language

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **Alpine.js**: Lightweight JavaScript framework
- **Jinja2**: Template engine

### Development Tools
- **Git**: Version control
- **GitHub**: Code hosting and collaboration
- **Virtual Environments**: Python dependency management


### Daily Development Workflow
```bash
# Activate virtual environment
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Make your changes to the code, save your changes
# Test your application
python3 app.py

# Update database schema (when needed)
python3 update_database.py
```

## 📖 Code Organization

### Flask Application Structure
```
project-name/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # Jinja HTML templates
│   ├── base.html      # Base template with navigation
│   ├── index.html     # Home page
│   ├── create.html    # Create form
│   ├── edit.html      # Edit form
│   └── ...
└── static/            # CSS, JavaScript, images
```

### Template Inheritance
- **base.html**: Contains common layout, navigation, and styling
- **Child templates**: Extend base.html and fill in content blocks
- **Includes**: Reusable components like navigation menus

### Database Design
- **SQLite tables**: Simple, file-based database
- **CRUD operations**: Create, Read, Update, Delete
- **Relationships**: Foreign keys between related tables

## 🎓 Student Resources

### Documentation
- **Flask Official Docs**: https://flask.palletsprojects.com/
- **Jinja2 Template Engine**: https://jinja.palletsprojects.com/
- **SQLite Tutorial**: https://www.sqlitetutorial.net/
- **Tailwind CSS**: https://tailwindcss.com/
- **HTML Forms**: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form

### Learning Path
1. **Start with Solution Template**: Explore all features in `solution_template_project_one/`
2. **Try the Form Demo**: Visit `/form_demo` to understand form handling
3. **Practice Schema Changes**: Use `update_database.py` to modify the database
4. **Pick a Project**: Choose one of the numbered projects to build
5. **Experiment**: Try adding new features
6. **Build Your Own**: Create a project that interests you

### New Learning Tools
- **Form Demo** (`/form_demo`): Interactive tutorial on form elements
- **Database Updater** (`update_database.py`): Safe schema modification tool
- **HOWTO Guides**: Step-by-step instructions for common tasks

### Common Challenges & Solutions
- **Template errors**: Check Jinja syntax and block structure
- **Database issues**: Verify table creation and SQL syntax
- **Routing problems**: Ensure route functions return proper responses
- **Styling issues**: Check Tailwind CSS class names

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new features
- Improve existing code
- Fix bugs
- Suggest improvements
- Share your own projects

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Getting Help

If you get stuck:
1. **Check the code comments** - they explain how everything works
2. **Look at the error messages** - they often tell you what's wrong
3. **Ask your teacher** - they're here to help!
4. **Search online** - many developers have solved similar problems

## 🎉 Success Tips

- **Start small**: Don't try to build everything at once
- **Test often**: Run your app after each change
- **Read the comments**: They explain the "why" behind the code
- **Experiment**: Try changing things to see what happens
- **Have fun**: Web development is creative and rewarding!


