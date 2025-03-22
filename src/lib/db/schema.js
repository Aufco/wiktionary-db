const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// Ensure the db directory exists
const dbDir = path.join(process.cwd(), 'db');
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize the database
const db = new Database(path.join(dbDir, 'wiktionary.db'));

// Enable foreign keys
db.pragma('foreign_keys = ON');

// Create database schema
function initializeDatabase() {
  // Create languages table
  db.exec(`
    CREATE TABLE IF NOT EXISTS languages (
      id INTEGER PRIMARY KEY,
      code TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL
    )
  `);

  // Create words table
  db.exec(`
    CREATE TABLE IF NOT EXISTS words (
      id INTEGER PRIMARY KEY,
      word TEXT NOT NULL,
      language_id INTEGER NOT NULL,
      FOREIGN KEY (language_id) REFERENCES languages(id),
      UNIQUE (word, language_id)
    )
  `);

  // Create definitions table with support for multiple definitions per word
  db.exec(`
    CREATE TABLE IF NOT EXISTS definitions (
      id INTEGER PRIMARY KEY,
      word_id INTEGER NOT NULL,
      part_of_speech TEXT,
      definition TEXT NOT NULL,
      example TEXT,
      FOREIGN KEY (word_id) REFERENCES words(id)
    )
  `);

  // Create index for faster lookups
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_word ON words(word);
    CREATE INDEX IF NOT EXISTS idx_word_language ON words(word, language_id);
  `);

  console.log('Database schema initialized successfully');
}

// Initialize the database
initializeDatabase();

// Export the database connection
module.exports = db;