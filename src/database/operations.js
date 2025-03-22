import { getDatabase } from './schema.js';

export function getOrCreateLanguage(code, name) {
  const db = getDatabase();
  const existingLang = db.prepare('SELECT id FROM languages WHERE code = ?').get(code);
  
  if (existingLang) {
    return existingLang.id;
  }
  
  const result = db.prepare('INSERT INTO languages (code, name) VALUES (?, ?)').run(code, name);
  return result.lastInsertRowid;
}

export function getOrCreatePartOfSpeech(posName) {
  const db = getDatabase();
  const normalizedPos = posName.charAt(0).toUpperCase() + posName.slice(1).toLowerCase();
  
  const existingPos = db.prepare('SELECT id FROM parts_of_speech WHERE name = ?').get(normalizedPos);
  
  if (existingPos) {
    return existingPos.id;
  }
  
  const result = db.prepare('INSERT INTO parts_of_speech (name) VALUES (?)').run(normalizedPos);
  return result.lastInsertRowid;
}

export function createEntry(word, languageId) {
  const db = getDatabase();
  try {
    const result = db.prepare('INSERT OR IGNORE INTO entries (word, language_id) VALUES (?, ?)').run(word, languageId);
    if (result.changes > 0) {
      return result.lastInsertRowid;
    } else {
      // Entry already exists, get its ID
      const existingEntry = db.prepare('SELECT id FROM entries WHERE word = ? AND language_id = ?').get(word, languageId);
      return existingEntry.id;
    }
  } catch (error) {
    console.error(`Error creating entry for word: ${word}`, error);
    throw error;
  }
}

export function createDefinition(entryId, posId, definition, senseId = null, etymologyNumber = null) {
  const db = getDatabase();
  try {
    const result = db.prepare(
      'INSERT INTO definitions (entry_id, pos_id, definition, sense_id, etymology_number) VALUES (?, ?, ?, ?, ?)'
    ).run(entryId, posId, definition, senseId, etymologyNumber);
    
    return result.lastInsertRowid;
  } catch (error) {
    console.error(`Error creating definition for entry ID: ${entryId}`, error);
    throw error;
  }
}

export function createExample(definitionId, example) {
  const db = getDatabase();
  try {
    const result = db.prepare(
      'INSERT INTO examples (definition_id, example) VALUES (?, ?)'
    ).run(definitionId, example);
    
    return result.lastInsertRowid;
  } catch (error) {
    console.error(`Error creating example for definition ID: ${definitionId}`, error);
    throw error;
  }
}

export function beginTransaction() {
  const db = getDatabase();
  db.prepare('BEGIN TRANSACTION').run();
}

export function commitTransaction() {
  const db = getDatabase();
  db.prepare('COMMIT').run();
}

export function rollbackTransaction() {
  const db = getDatabase();
  db.prepare('ROLLBACK').run();
}