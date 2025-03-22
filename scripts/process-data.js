const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const Database = require('better-sqlite3');
const saxStream = require('sax').createStream(true, { trim: true });

// Paths
const dataDir = path.join(__dirname, '..', 'data');
const dbDir = path.join(__dirname, '..', 'src', 'db');
const xmlFile = path.join(dataDir, 'enwiktionary-latest-pages-articles.xml');
const dbFile = path.join(dbDir, 'wiktionary.db');

// Ensure directories exist
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize database
const db = new Database(dbFile);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

// Initialize schema (if not already done)
function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS languages (
      id INTEGER PRIMARY KEY,
      code TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS words (
      id INTEGER PRIMARY KEY,
      word TEXT NOT NULL,
      language_id INTEGER NOT NULL,
      FOREIGN KEY (language_id) REFERENCES languages(id),
      UNIQUE (word, language_id)
    );

    CREATE TABLE IF NOT EXISTS definitions (
      id INTEGER PRIMARY KEY,
      word_id INTEGER NOT NULL,
      part_of_speech TEXT,
      definition TEXT NOT NULL,
      example TEXT,
      FOREIGN KEY (word_id) REFERENCES words(id)
    );

    CREATE INDEX IF NOT EXISTS idx_word ON words(word);
    CREATE INDEX IF NOT EXISTS idx_word_language ON words(word, language_id);
  `);
  
  // Add English as a default language
  const insertLanguage = db.prepare('INSERT OR IGNORE INTO languages (code, name) VALUES (?, ?)');
  insertLanguage.run('en', 'English');
  
  console.log('Database schema initialized');
}

// Prepare SQL statements
const insertLanguage = db.prepare('INSERT OR IGNORE INTO languages (code, name) VALUES (?, ?)');
const getLanguageId = db.prepare('SELECT id FROM languages WHERE name = ?');
const insertWord = db.prepare('INSERT OR IGNORE INTO words (word, language_id) VALUES (?, ?)');
const getWordId = db.prepare('SELECT id FROM words WHERE word = ? AND language_id = ?');
const insertDefinition = db.prepare('INSERT INTO definitions (word_id, part_of_speech, definition, example) VALUES (?, ?, ?, ?)');

// Begin transaction for better performance
let wordCount = 0;
const processWord = db.transaction((title, content) => {
  // This is a simplified parser - a real one would need to handle the complexities
  // of MediaWiki markup and the specific structure of Wiktionary entries
  
  // Extract language sections (simplified)
  const languageSections = content.split(/^==([^=]+)==$/m);
  
  if (languageSections.length <= 1) return;
  
  for (let i = 1; i < languageSections.length; i += 2) {
    const language = languageSections[i].trim();
    const section = languageSections[i + 1] || '';
    
    // Skip non-language sections
    if (['Etymology', 'Pronunciation', 'References'].includes(language)) continue;
    
    // Get language ID (insert if doesn't exist)
    insertLanguage.run(language.toLowerCase(), language);
    const langResult = getLanguageId.get(language);
    if (!langResult) continue;
    
    const languageId = langResult.id;
    
    // Insert word
    insertWord.run(title, languageId);
    const wordResult = getWordId.get(title, languageId);
    if (!wordResult) continue;
    
    const wordId = wordResult.id;
    
    // Find definitions
    const posRegex = /^===([^=]+)===$/gm;
    const defRegex = /^# (.+)$/gm;
    
    let posMatch;
    let currentPos = null;
    
    while ((posMatch = posRegex.exec(section)) !== null) {
      currentPos = posMatch[1].trim();
      const posContent = section.slice(posMatch.index + posMatch[0].length);
      
      let defMatch;
      const defEndRegex = /^[=#]/m;
      const defEndMatch = defEndRegex.exec(posContent);
      const defSection = defEndMatch 
        ? posContent.slice(0, defEndMatch.index) 
        : posContent;
      
      while ((defMatch = defRegex.exec(defSection)) !== null) {
        const definition = defMatch[1].trim();
        if (definition) {
          insertDefinition.run(wordId, currentPos, definition, null);
        }
      }
    }
  }
  
  wordCount++;
  if (wordCount % 1000 === 0) {
    console.log(`Processed ${wordCount} words`);
  }
});

// Process XML file (simplified - real implementation would need to be more robust)
function processXML() {
  console.log('Starting XML processing...');
  
  // In a real implementation, you would need to stream the XML
  // This is just a placeholder
  console.log('XML processing would happen here');
  console.log('This is a simplified example - actual processing would require streaming the XML');
  
  console.log('Processing complete');
}

// Main execution
initSchema();
// Uncomment when ready to process
// processXML();

console.log('Script completed');