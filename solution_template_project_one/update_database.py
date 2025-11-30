#!/usr/bin/env python3
"""
===============================================================================
DATABASE SCHEMA UPDATER FOR STUDENTS
===============================================================================

This script helps students safely update their database schema when they 
modify schema.sql. It will:

1. ✅ Check if schema.sql has valid syntax
2. 💾 Backup existing data (if any)
3. 🔄 Apply the new schema
4. 📊 Show what happened

HOW TO USE:
Just run this file! No command line arguments needed.

    python3 update_database.py

The script will guide you through the process and tell you exactly what it's doing.

===============================================================================
"""

import os
import sqlite3
import shutil
from datetime import datetime


# =====================================================
# CONFIGURATION
# These paths match your Flask app structure
# =====================================================

# Get the directory where this script is located
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database paths
DB_DIR = os.path.join(BASE_DIR, 'db')
DB_PATH = os.path.join(DB_DIR, 'app.db')
BACKUP_DIR = os.path.join(DB_DIR, 'backups')

# Schema file path
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

# Required tables (from your Flask app)
REQUIRED_TABLES = {"users", "categories", "tags", "items", "item_tags"}


def print_header(message):
    """Print a nice header to make output easy to read."""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def print_step(step_number, message):
    """Print a numbered step."""
    print(f"\n{step_number}. {message}")


def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")


def print_info(message):
    """Print an info message."""
    print(f"📋 {message}")


def check_schema_file():
    """
    Check if schema.sql exists and can be read.
    Returns True if valid, False otherwise.
    """
    print_step(1, "Checking schema.sql file...")
    
    if not os.path.exists(SCHEMA_PATH):
        print_error(f"schema.sql not found at: {SCHEMA_PATH}")
        return False
    
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_content = f.read().strip()
        
        if not schema_content:
            print_error("schema.sql is empty!")
            return False
            
        print_success(f"Found schema.sql ({len(schema_content)} characters)")
        return True
        
    except Exception as e:
        print_error(f"Could not read schema.sql: {e}")
        return False


def validate_schema_syntax():
    """
    Test the schema.sql syntax by trying to apply it to a temporary database.
    Returns True if syntax is valid, False otherwise.
    """
    print_step(2, "Validating schema.sql syntax...")
    
    # Create a temporary database to test the schema
    temp_db_path = os.path.join(DB_DIR, 'temp_test.db')
    
    try:
        # Make sure db directory exists
        os.makedirs(DB_DIR, exist_ok=True)
        
        # Remove temp file if it exists
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        # Read the schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Try to execute the schema on a temporary database
        conn = sqlite3.connect(temp_db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()
        
        # Check if required tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        created_tables = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        
        # Clean up temp file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        # Verify all required tables exist
        missing_tables = REQUIRED_TABLES - created_tables
        if missing_tables:
            print_error(f"Schema is missing required tables: {', '.join(missing_tables)}")
            print_info("Your schema.sql must create these tables: " + ", ".join(REQUIRED_TABLES))
            return False
        
        print_success("Schema syntax is valid! ✨")
        print_info(f"Found tables: {', '.join(sorted(created_tables))}")
        return True
        
    except sqlite3.Error as e:
        print_error(f"Schema has SQL syntax errors: {e}")
        print_info("Check your schema.sql for typos, missing semicolons, or syntax errors.")
        return False
    except Exception as e:
        print_error(f"Unexpected error validating schema: {e}")
        return False


def backup_existing_database():
    """
    Create a backup of the existing database if it exists.
    Returns the backup path if successful, None otherwise.
    """
    print_step(3, "Checking for existing database...")
    
    if not os.path.exists(DB_PATH):
        print_info("No existing database found. Starting fresh! 🆕")
        return None
    
    # Check if database has any data
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        
        if not tables:
            print_info("Database exists but is empty. No backup needed.")
            conn.close()
            return None
        
        # Count total records across all tables
        total_records = 0
        for table in tables:
            table_name = table[0]
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                total_records += count
            except sqlite3.Error:
                # Skip tables we can't count (like system tables)
                pass
        
        conn.close()
        
        if total_records == 0:
            print_info("Database exists but has no data. No backup needed.")
            return None
        
        # Create backup
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"app_backup_{timestamp}.db")
        
        shutil.copy2(DB_PATH, backup_path)
        print_success(f"Database backed up to: {os.path.basename(backup_path)}")
        print_info(f"Backup contains {total_records} records across {len(tables)} tables")
        return backup_path
        
    except Exception as e:
        print_error(f"Could not backup database: {e}")
        return None


def apply_new_schema():
    """
    Apply the new schema to the database.
    Returns True if successful, False otherwise.
    """
    print_step(4, "Applying new schema to database...")
    
    try:
        # Make sure db directory exists
        os.makedirs(DB_DIR, exist_ok=True)
        
        # Remove existing database
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        
        # Read and apply new schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        created_tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        print_success("New schema applied successfully! 🎉")
        print_info(f"Created tables: {', '.join(sorted(created_tables))}")
        return True
        
    except Exception as e:
        print_error(f"Failed to apply schema: {e}")
        return False


def show_summary(backup_path):
    """Show a summary of what happened."""
    print_header("SUMMARY")
    
    print("✅ Schema validation: PASSED")
    print("✅ Database update: COMPLETED")
    
    if backup_path:
        print(f"💾 Backup created: {os.path.basename(backup_path)}")
        print("   (Your old data is safe!)")
    
    print("\n🚀 Your Flask app is ready to use the new schema!")
    print("   You can now run: python3 app.py")


def main():
    """Main function that orchestrates the schema update process."""
    print_header("DATABASE SCHEMA UPDATER")
    print("This tool will help you safely update your database schema.")
    print("Make sure you have edited schema.sql with your desired changes.")
    
    # Ask user to confirm
    print("\n🤔 Ready to update your database?")
    response = input("Type 'yes' to continue, anything else to cancel: ").strip().lower()
    
    if response != 'yes':
        print("\n👋 Cancelled. No changes were made.")
        return
    
    # Step 1: Check schema file exists
    if not check_schema_file():
        return
    
    # Step 2: Validate schema syntax
    if not validate_schema_syntax():
        print("\n💡 TIP: Fix the errors in schema.sql and run this script again.")
        return
    
    # Step 3: Backup existing database (if needed)
    backup_path = backup_existing_database()
    
    # Step 4: Apply new schema
    if not apply_new_schema():
        print("\n😞 Something went wrong applying the schema.")
        if backup_path:
            print(f"Your data is safe in: {backup_path}")
        return
    
    # Show summary
    show_summary(backup_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user. No changes were made.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your schema.sql and try again.")