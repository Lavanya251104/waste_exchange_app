-- Drop old tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS waste;
DROP TABLE IF EXISTS requests;

-- Users table with new column 'waste_types'
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('buyer','seller')) NOT NULL,
    waste_types TEXT  -- new column to store comma-separated waste types
);

-- Waste table
CREATE TABLE waste (
    waste_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    description TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Requests table
CREATE TABLE requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER NOT NULL,
    waste_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY(buyer_id) REFERENCES users(user_id),
    FOREIGN KEY(waste_id) REFERENCES waste(waste_id)
);