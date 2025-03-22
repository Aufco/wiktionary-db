const fs = require('fs');
const path = require('path');
const sax = require('sax');
const Database = require('better-sqlite3');

// Paths
const dataDir = path.join(__dirname, '..', 'data');
const dbDir = path.join(__dirname, '..', 'src', 'db');
const xmlFile = path.join(dataDir, 'enwiktionary-latest-pages-articles.xml', 'enwiktionary-latest-pages-articles.xml');
const dbFile = path.join(dbDir, 'wiktionary.db');

// Regular expressions to extract information
const languageHeaderRegex = /^==\s*([a-zA-Z]+)\s*==$/m;
const posHeaderRegex = /^===\s*([a-zA-Z ]+)\s*===$/m;
const definitionRegex = /^#\s*(.+)$/m;

// Ensure database directory exists
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize database
const db = new Database(dbFile);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.pragma('cache_size = -10000'); // Use 10MB of cache
db.pragma('synchronous = NORMAL'); // Less safety, more speed

// Initialize schema
function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS languages (
      id INTEGER PRIMARY KEY,
      code TEXT,
      name TEXT NOT NULL UNIQUE
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

// Transaction for better performance
const insertWordWithDefinitions = db.transaction((title, languageName, partOfSpeech, definitions) => {
  // Skip non-word entries or templates/categories
  if (title.includes(':') || !languageName) {
    return;
  }
  
  // Get or insert language
  let languageId;
  try {
    insertLanguage.run(languageName.toLowerCase(), languageName);
    const languageResult = getLanguageId.get(languageName);
    if (!languageResult) {
      return;
    }
    languageId = languageResult.id;
  } catch (err) {
    return;
  }
  
  // Insert word
  try {
    insertWord.run(title, languageId);
    const wordResult = getWordId.get(title, languageId);
    if (!wordResult) {
      return;
    }
    const wordId = wordResult.id;
    
    // Insert definitions
    for (const def of definitions) {
      try {
        insertDefinition.run(wordId, partOfSpeech, def, null);
      } catch (err) {
        // Ignore definition errors
      }
    }
  } catch (err) {
    // Ignore word errors
  }
});

// Process text content of a page
function processPageContent(title, content) {
  // Skip non-word entries or templates/categories
  if (title.includes(':')) {
    return;
  }
  
  // Extract language sections
  const languageMatches = content.match(new RegExp(languageHeaderRegex, 'g'));
  if (!languageMatches) {
    return;
  }
  
  // Split content into language sections
  const sections = content.split(/^==\s*[a-zA-Z]+\s*==$/m);
  
  if (sections.length <= 1 || languageMatches.length + 1 !== sections.length) {
    return;
  }
  
  // Process each language section
  for (let i = 0; i < languageMatches.length; i++) {
    const languageHeader = languageMatches[i];
    const languageMatch = languageHeader.match(languageHeaderRegex);
    
    if (!languageMatch || !languageMatch[1]) {
      continue;
    }
    
    const language = languageMatch[1];
    const section = sections[i + 1];
    
    // Extract part of speech sections
    const posMatches = section.match(new RegExp(posHeaderRegex, 'g'));
    if (!posMatches) {
      continue;
    }
    
    // Split section into POS sections
    const posSections = section.split(/^===\s*[a-zA-Z ]+\s*===$/m);
    
    if (posSections.length <= 1 || posMatches.length + 1 !== posSections.length) {
      continue;
    }
    
    // Process each POS section
    for (let j = 0; j < posMatches.length; j++) {
      const posHeader = posMatches[j];
      const posMatch = posHeader.match(posHeaderRegex);
      
      if (!posMatch || !posMatch[1]) {
        continue;
      }
      
      const pos = posMatch[1];
      const posSection = posSections[j + 1];
      
      // Extract definitions
      const definitionMatches = posSection.match(new RegExp(definitionRegex, 'g'));
      if (!definitionMatches) {
        continue;
      }
      
      const definitions = definitionMatches.map(defMatch => {
        const match = defMatch.match(definitionRegex);
        return match && match[1] ? match[1].trim() : null;
      }).filter(Boolean);
      
      if (definitions.length > 0) {
        insertWordWithDefinitions(title, language, pos, definitions);
      }
    }
  }
}

// Process XML file using SAX parser for streaming
function processXMLStream() {
  return new Promise((resolve, reject) => {
    const saxStream = sax.createStream(true, { trim: true });
    
    let inPage = false;
    let inTitle = false;
    let inText = false;
    let inNs = false;
    let currentTitle = '';
    let currentText = '';
    let currentNs = '';
    let pageCount = 0;
    let wordCount = 0;
    
    // Track progress
    const startTime = Date.now();
    let lastReportTime = startTime;
    
    // Begin database transaction
    const transaction = db.transaction(() => {
      // Process in batches for better performance
      const batchSize = 100;
      let batch = [];
      
      saxStream.on('opentag', node => {
        if (node.name === 'page') {
          inPage = true;
          currentTitle = '';
          currentText = '';
          currentNs = '';
        } else if (inPage && node.name === 'title') {
          inTitle = true;
        } else if (inPage && node.name === 'text') {
          inText = true;
        } else if (inPage && node.name === 'ns') {
          inNs = true;
        }
      });
      
      saxStream.on('closetag', nodeName => {
        if (nodeName === 'page') {
          inPage = false;
          pageCount++;
          
          // Only process main namespace (ns=0)
          if (currentNs === '0') {
            batch.push({ title: currentTitle, text: currentText });
            wordCount++;
            
            // Process batch if it reaches batch size
            if (batch.length >= batchSize) {
              processBatch(batch);
              batch = [];
              
              // Report progress every 5 seconds
              const now = Date.now();
              if (now - lastReportTime > 5000) {
                const elapsedSeconds = Math.floor((now - startTime) / 1000);
                const pagesPerSecond = Math.floor(pageCount / (elapsedSeconds || 1));
                console.log(`Processed ${pageCount} pages (${wordCount} words) in ${elapsedSeconds}s (${pagesPerSecond} pages/s)`);
                lastReportTime = now;
              }
            }
          }
        } else if (nodeName === 'title') {
          inTitle = false;
        } else if (nodeName === 'text') {
          inText = false;
        } else if (nodeName === 'ns') {
          inNs = false;
        }
      });
      
      saxStream.on('text', text => {
        if (inTitle) {
          currentTitle += text;
        } else if (inText) {
          currentText += text;
        } else if (inNs) {
          currentNs += text;
        }
      });
      
      saxStream.on('error', err => {
        console.error('XML parsing error:', err);
        reject(err);
      });
      
      saxStream.on('end', () => {
        // Process any remaining items in the batch
        if (batch.length > 0) {
          processBatch(batch);
        }
        
        const totalTime = Math.floor((Date.now() - startTime) / 1000);
        console.log(`Completed processing ${pageCount} pages (${wordCount} words) in ${totalTime}s`);
        resolve();
      });
      
      // Helper function to process a batch of pages
      function processBatch(pages) {
        pages.forEach(page => {
          try {
            processPageContent(page.title, page.text);
          } catch (err) {
            console.error(`Error processing page ${page.title}:`, err.message);
          }
        });
      }
      
      // Start reading the file
      fs.createReadStream(xmlFile)
        .pipe(saxStream);
    });
    
    // Execute transaction
    transaction();
  });
}

// Main execution
async function main() {
  console.time('Total execution time');
  
  console.log('Initializing database...');
  initSchema();
  
  console.log(`Processing XML file: ${xmlFile}`);
  console.log('This may take a while for the full dataset...');
  
  try {
    await processXMLStream();
    console.log('XML processing complete!');
  } catch (err) {
    console.error('Error during XML processing:', err);
  }
  
  // Create the remaining indexes after all data is loaded
  console.log('Creating indexes...');
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_word_id ON definitions(word_id);
    CREATE INDEX IF NOT EXISTS idx_pos ON definitions(part_of_speech);
  `);
  
  console.log('Optimizing database...');
  db.pragma('optimize');
  
  console.timeEnd('Total execution time');
  db.close();
}

main().catch(err => {
  console.error('Fatal error:', err);
  db.close();
  process.exit(1);
});