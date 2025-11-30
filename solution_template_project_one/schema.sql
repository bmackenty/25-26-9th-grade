-- ===============================================================
-- schema.sql
-- This file defines all the tables (and some sample data) 
-- for our Flask + SQLite starter app.
-- ===============================================================

-- ---------------------------------------------------------------
-- CLEAN SLATE: Drop existing tables if they exist.
-- This is helpful during development when we want to "reset" 
-- the database without errors.
-- (The order matters: drop the join table first, then dependent tables.)
-- ---------------------------------------------------------------
DROP TABLE IF EXISTS item_tags;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- ---------------------------------------------------------------
-- USERS TABLE
-- Stores accounts for people who can log in.
-- Fields:
--   id            → unique identifier for each user
--   username      → must be unique, required
--   password_hash → the password, but encrypted (hashed)
--   created_at    → when the account was created (auto-filled)
--   status        → user account status: 'active' or 'inactive'
-- ---------------------------------------------------------------
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('active','inactive')) DEFAULT 'active' NOT NULL
);

-- ---------------------------------------------------------------
-- CATEGORIES TABLE
-- A category is like a "folder" or "group" that an item belongs to.
-- Example: "School", "Home", "Work".
-- Fields:
--   id   → unique ID
--   name → unique category name
-- ---------------------------------------------------------------
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- ---------------------------------------------------------------
-- TAGS TABLE
-- Tags are "labels" you can attach to items.
-- Unlike categories, items can have MANY tags.
-- Example: "urgent", "fun", "optional".
-- Fields:
--   id   → unique ID
--   name → unique tag name
-- ---------------------------------------------------------------
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- ---------------------------------------------------------------
-- ITEMS TABLE
-- The main table that stores all the "things" users create.
-- Fields:
--   id          → unique ID
--   name        → short title of the item
--   description → longer text
--   status      → must be either 'active' or 'archived'
--   category_id → points to which category this item belongs to
--   owner_id    → points to which user created the item
--   created_at  → when the item was created
--   updated_at  → last update timestamp
-- 
-- FOREIGN KEYS:
--   category_id references categories(id)
--   owner_id references users(id)
-- ---------------------------------------------------------------
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('active','archived')) DEFAULT 'active',
    category_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- ITEM_TAGS TABLE
-- This is a "join table" for the many-to-many relationship 
-- between items and tags.
-- An item can have multiple tags, and a tag can apply to many items.
-- Fields:
--   item_id → references items.id
--   tag_id  → references tags.id
-- Together, (item_id, tag_id) is the PRIMARY KEY (must be unique).
-- ---------------------------------------------------------------
CREATE TABLE item_tags (
    item_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, tag_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- SAMPLE DATA
-- Insert some starter categories and tags so students have 
-- something to work with right away.
-- ---------------------------------------------------------------
INSERT INTO categories (name) VALUES ('General'), ('School'), ('Home'), ('Work');
INSERT INTO tags (name) VALUES ('urgent'), ('optional'), ('fun'), ('long-term');
