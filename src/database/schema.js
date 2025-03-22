import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, '../../sqlite.db');

export function setupDatabase() {
  const db = new Database(dbPath);
  
  // Enable foreign keys
  db.pragma('foreign_keys = ON');
  
  // Create tables if they don't exist
  db.exec(`
    CREATE TABLE IF NOT EXISTS languages (
      id INTEGER PRIMARY KEY,
      code TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY,
      word TEXT NOT NULL,
      language_id INTEGER NOT NULL,
      FOREIGN KEY (language_id) REFERENCES languages(id),
      UNIQUE (word, language_id)
    );

    CREATE TABLE IF NOT EXISTS parts_of_speech (
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS definitions (
      id INTEGER PRIMARY KEY,
      entry_id INTEGER NOT NULL,
      pos_id INTEGER NOT NULL,
      definition TEXT NOT NULL,
      sense_id TEXT,
      etymology_number INTEGER,
      FOREIGN KEY (entry_id) REFERENCES entries(id),
      FOREIGN KEY (pos_id) REFERENCES parts_of_speech(id)
    );

    CREATE TABLE IF NOT EXISTS examples (
      id INTEGER PRIMARY KEY,
      definition_id INTEGER NOT NULL,
      example TEXT NOT NULL,
      FOREIGN KEY (definition_id) REFERENCES definitions(id)
    );
  `);

  // Populate initial parts of speech
  const initialPos = [
    'Noun', 'Verb', 'Adjective', 'Adverb', 'Pronoun', 'Preposition', 
    'Conjunction', 'Interjection', 'Determiner', 'Article', 'Numeral',
    'Particle', 'Contraction', 'Suffix', 'Prefix', 'Proper noun'
  ];

  const insertPosStmt = db.prepare('INSERT OR IGNORE INTO parts_of_speech (name) VALUES (?)');
  initialPos.forEach(pos => insertPosStmt.run(pos));

  // Populate initial languages
  const insertLangStmt = db.prepare('INSERT OR IGNORE INTO languages (code, name) VALUES (?, ?)');
  insertLangStmt.run('en', 'English');

  return db;
}

export function getDatabase() {
  return new Database(dbPath);
}