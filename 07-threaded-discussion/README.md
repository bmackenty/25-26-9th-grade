# Threaded Discussion Board

A full-featured threaded discussion board application built with Flask, featuring Reddit-style voting, file uploads, and comprehensive admin/moderator tools.

## Features

### Core Discussion Features
- **Thread Creation**: Create new discussion threads with titles, content, and categories
- **Threaded Replies**: Reply to threads and other posts with nested conversations
- **Categories**: Organize discussions into logical categories (General, Technology, Help & Support, Announcements)
- **Search & Filtering**: Search threads by content and filter by category
- **Sorting Options**: Sort threads by latest, oldest, most viewed, most replied, or most voted

### Voting & Engagement System
- **Upvote/Downvote**: Reddit-style voting system for both threads and posts
- **Vote Scoring**: Real-time calculation and display of vote scores
- **Like System**: Additional like functionality for threads and posts
- **Reputation System**: Track user reputation based on voting activity

### File Management
- **File Attachments**: Upload files to threads and posts
- **Supported Formats**: TXT, PDF, PNG, JPG, JPEG, GIF, DOC, DOCX
- **Secure Storage**: Files are stored with timestamped names for security
- **Download Links**: Easy access to uploaded files

### Admin & Moderation Tools
- **Admin Dashboard**: Comprehensive overview of board statistics and activity
- **Thread Management**: Pin/unpin important threads, lock/unlock discussions
- **Content Moderation**: Delete inappropriate threads and posts
- **User Management**: Monitor user activity and reputation
- **Data Export**: Export all discussion data to CSV format

### User Experience
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **Real-time Updates**: Dynamic voting and liking without page refreshes
- **Intuitive Navigation**: Clean, organized interface for easy browsing
- **Status Indicators**: Visual indicators for pinned and locked threads

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd 07-threaded-discussion
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your web browser and navigate to `http://localhost:5000`
   - The application will automatically create the database and default categories

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password (for future authentication)
- `role`: User role (user, moderator, admin)
- `reputation`: User reputation score
- `created_at`: Account creation timestamp
- `last_seen`: Last activity timestamp

### Categories Table
- `id`: Primary key
- `name`: Category name
- `description`: Category description
- `created_at`: Creation timestamp

### Threads Table
- `id`: Primary key
- `title`: Thread title
- `content`: Thread content
- `user_id`: Foreign key to users table
- `category_id`: Foreign key to categories table
- `is_pinned`: Boolean for pinned status
- `is_locked`: Boolean for locked status
- `view_count`: Number of views
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Posts Table (Replies)
- `id`: Primary key
- `content`: Post content
- `user_id`: Foreign key to users table
- `thread_id`: Foreign key to threads table
- `parent_post_id`: Foreign key for nested replies
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Votes Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `thread_id`: Foreign key to threads table (nullable)
- `post_id`: Foreign key to posts table (nullable)
- `vote_type`: Type of vote (upvote/downvote)
- `created_at`: Vote timestamp

### Likes Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `thread_id`: Foreign key to threads table (nullable)
- `post_id`: Foreign key to posts table (nullable)
- `created_at`: Like timestamp

### Attachments Table
- `id`: Primary key
- `filename`: Stored filename
- `original_filename`: Original filename
- `file_path`: File system path
- `file_size`: File size in bytes
- `mime_type`: File MIME type
- `user_id`: Foreign key to users table
- `thread_id`: Foreign key to threads table (nullable)
- `post_id`: Foreign key to posts table (nullable)
- `created_at`: Upload timestamp

## Usage

### Creating Threads
1. Click "New Thread" in the navigation
2. Fill in the title, select a category, and write your content
3. Optionally attach files
4. Click "Create Thread"

### Replying to Threads
1. Navigate to a thread
2. Scroll to the bottom to find the reply form
3. Write your reply and optionally attach files
4. Click "Post Reply"

### Voting and Liking
- Use the up/down arrows to vote on threads and posts
- Click the heart icon to like content
- Vote scores are calculated in real-time

### Admin Functions
1. Access the admin dashboard at `/admin`
2. View board statistics and recent activity
3. Manage threads (pin, lock, delete)
4. Export data to CSV format

## API Endpoints

### Public Endpoints
- `GET /`: Main page with thread listing
- `GET /thread/<id>`: View specific thread
- `GET /thread/create`: Create new thread form
- `POST /thread/create`: Submit new thread
- `POST /thread/<id>/reply`: Reply to thread
- `POST /vote/<type>/<id>`: Vote on thread or post
- `POST /like/<type>/<id>`: Like thread or post

### Admin Endpoints
- `GET /admin`: Admin dashboard
- `GET /admin/threads`: Thread management
- `POST /admin/thread/<id>/toggle_pin`: Pin/unpin thread
- `POST /admin/thread/<id>/toggle_lock`: Lock/unlock thread
- `POST /admin/thread/<id>/delete`: Delete thread
- `GET /export/csv`: Export data to CSV

## Project Structure

```
07-threaded-discussion/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── discussion.db         # SQLite database (created automatically)
├── static/
│   └── uploads/         # File upload directory
└── templates/
    ├── base.html         # Base template with common layout
    ├── navbar.html       # Navigation component
    ├── index.html        # Main page with thread listing
    ├── create_thread.html # Thread creation form
    ├── view_thread.html  # Individual thread view
    ├── admin_dashboard.html # Admin overview
    └── admin_threads.html # Thread management interface
```

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy-style queries
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **File Handling**: Werkzeug for secure file uploads
- **Data Export**: CSV generation and download

## Customization

### Adding New Categories
Edit the `init_db()` function in `app.py` to add new categories:

```python
cursor.execute('''
    INSERT OR IGNORE INTO categories (name, description) VALUES 
    ('Your Category', 'Category description')
''')
```

### Modifying File Types
Update the `ALLOWED_EXTENSIONS` set in `app.py`:

```python
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
```

### Changing Default Admin User
Modify the default admin user in `init_db()`:

```python
cursor.execute('''
    INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES 
    ('your_admin', 'admin@yourdomain.com', 'your_password_hash', 'admin')
''')
```

## Security Features

- **File Upload Security**: Secure filename handling and file type validation
- **SQL Injection Protection**: Parameterized queries throughout
- **XSS Prevention**: Content is properly escaped in templates
- **CSRF Protection**: Form tokens for state-changing operations (can be enhanced)

## Future Enhancements

### Authentication System
- User registration and login
- Password hashing and security
- Session management
- Role-based access control

### Advanced Moderation
- Content filtering and spam detection
- User banning and suspension
- Report system for inappropriate content
- Automated moderation tools

### Enhanced Features
- Rich text editor for posts
- Image embedding and galleries
- User profiles and avatars
- Notification system
- Mobile app support

### Performance Improvements
- Database indexing optimization
- Caching layer (Redis)
- Pagination for large datasets
- API rate limiting

## Troubleshooting

### Common Issues

1. **Database Errors**
   - Delete `discussion.db` and restart the application
   - Check file permissions in the project directory

2. **File Upload Issues**
   - Ensure the `static/uploads` directory exists
   - Check file size limits and supported formats
   - Verify write permissions

3. **Template Errors**
   - Ensure all template files are in the `templates/` directory
   - Check for syntax errors in Jinja2 templates

4. **Port Already in Use**
   - Change the port in `app.py`: `app.run(debug=True, port=5001)`
   - Or kill the process using the current port

### Debug Mode
The application runs in debug mode by default. For production:
- Set `debug=False` in `app.py`
- Use a production WSGI server (Gunicorn, uWSGI)
- Configure proper logging and error handling

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For support or questions:
1. Check the troubleshooting section above
2. Review the Flask documentation
3. Open an issue in the project repository

---

**Note**: This is a demonstration application. For production use, implement proper authentication, security measures, and error handling.
