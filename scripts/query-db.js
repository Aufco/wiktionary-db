const fs = require('fs');
const path = require('path');

// Path to database
const dbFile = path.join(__dirname, '..', 'src', 'db', 'wiktionary-db.json');

// Load database
let database;
try {
  const data = fs.readFileSync(dbFile, 'utf8');
  database = JSON.parse(data);
  
  // Create indexes for faster lookups
  if (!database.indexes) {
    console.log('Creating indexes for faster lookups...');
    database.indexes = {
      languageById: {},
      languageByName: {},
      wordById: {},
      wordsByLanguageId: {},
      definitionsByWordId: {}
    };
    
    // Index languages
    Object.values(database.languages).forEach(lang => {
      database.indexes.languageById[lang.id] = lang;
      database.indexes.languageByName[lang.name.toLowerCase()] = lang;
    });
    
    // Index words
    Object.values(database.words).forEach(word => {
      database.indexes.wordById[word.id] = word;
      
      if (!database.indexes.wordsByLanguageId[word.language_id]) {
        database.indexes.wordsByLanguageId[word.language_id] = [];
      }
      database.indexes.wordsByLanguageId[word.language_id].push(word);
    });
    
    // Index definitions
    database.definitions.forEach(def => {
      if (!database.indexes.definitionsByWordId[def.word_id]) {
        database.indexes.definitionsByWordId[def.word_id] = [];
      }
      database.indexes.definitionsByWordId[def.word_id].push(def);
    });
    
    // Save indexed database
    fs.writeFileSync(dbFile, JSON.stringify(database, null, 2));
    console.log('Indexes created and saved');
  }
} catch (error) {
  console.error('Error loading database:', error.message);
  process.exit(1);
}

// Function to search for a word
function searchWord(word, language = 'English') {
  console.log(`Searching for "${word}" in language "${language}"...`);
  
  // Find language
  const lang = database.indexes.languageByName[language.toLowerCase()];
  
  if (!lang) {
    console.log(`Language "${language}" not found in database.`);
    return null;
  }
  
  // Find word
  const words = database.indexes.wordsByLanguageId[lang.id] || [];
  const wordObj = words.find(w => w.word.toLowerCase() === word.toLowerCase());
  
  if (!wordObj) {
    console.log(`Word "${word}" not found in ${language}.`);
    return null;
  }
  
  // Get all definitions
  const definitions = database.indexes.definitionsByWordId[wordObj.id] || [];
  
  // Sort definitions by part of speech and id
  definitions.sort((a, b) => {
    if (a.part_of_speech === b.part_of_speech) {
      return a.id - b.id;
    }
    return a.part_of_speech.localeCompare(b.part_of_speech);
  });
  
  return {
    word: wordObj.word,
    language,
    definitions
  };
}

// List all words in a language
function listWords(language = 'English', limit = 20) {
  console.log(`Listing words in language "${language}" (limit: ${limit})...`);
  
  // Find language
  const lang = database.indexes.languageByName[language.toLowerCase()];
  
  if (!lang) {
    console.log(`Language "${language}" not found in database.`);
    return [];
  }
  
  // Get words
  const words = database.indexes.wordsByLanguageId[lang.id] || [];
  
  // Sort words alphabetically
  words.sort((a, b) => a.word.localeCompare(b.word));
  
  return words.slice(0, limit);
}

// List all languages
function listLanguages() {
  console.log('Listing all languages...');
  
  // Get languages
  const languages = Object.values(database.languages).map(lang => {
    const words = database.indexes.wordsByLanguageId[lang.id] || [];
    return {
      ...lang,
      word_count: words.length
    };
  });
  
  // Sort languages by name
  languages.sort((a, b) => a.name.localeCompare(b.name));
  
  return languages;
}

// Get database statistics
function getStats() {
  console.log('Getting database statistics...');
  
  return {
    languages: Object.keys(database.languages).length,
    words: Object.keys(database.words).length,
    definitions: database.definitions.length
  };
}

// Process command line arguments
function processArguments() {
  const args = process.argv.slice(2);
  const command = args[0]?.toLowerCase();
  
  switch (command) {
    case 'search':
      const word = args[1];
      const searchLanguage = args[2] || 'English';
      
      if (!word) {
        console.log('Usage: node query-json-db.js search <word> [language]');
        break;
      }
      
      const result = searchWord(word, searchLanguage);
      
      if (result) {
        console.log(`\n"${result.word}" (${result.language}):`);
        
        // Group definitions by part of speech
        const byPos = {};
        result.definitions.forEach(def => {
          if (!byPos[def.part_of_speech]) {
            byPos[def.part_of_speech] = [];
          }
          byPos[def.part_of_speech].push(def);
        });
        
        // Display definitions
        Object.entries(byPos).forEach(([pos, defs]) => {
          console.log(`\n${pos}:`);
          defs.forEach((def, index) => {
            console.log(`  ${index + 1}. ${def.definition}`);
            if (def.example) {
              console.log(`     Example: ${def.example}`);
            }
          });
        });
      }
      break;
      
    case 'list':
      const listLanguage = args[1] || 'English';
      const limit = parseInt(args[2]) || 20;
      
      const words = listWords(listLanguage, limit);
      
      console.log(`\nWords in ${listLanguage} (showing ${words.length}):`);
      words.forEach((word, index) => {
        console.log(`${index + 1}. ${word.word}`);
      });
      break;
      
    case 'languages':
      const languages = listLanguages();
      
      console.log('\nLanguages in database:');
      languages.forEach((lang, index) => {
        console.log(`${index + 1}. ${lang.name} (${lang.code || 'no code'}) - ${lang.word_count} words`);
      });
      break;
      
    case 'stats':
      const stats = getStats();
      
      console.log('\nDatabase Statistics:');
      console.log(`Languages: ${stats.languages}`);
      console.log(`Words: ${stats.words}`);
      console.log(`Definitions: ${stats.definitions}`);
      break;
      
    default:
      console.log(`
Wiktionary Database Query Tool (JSON version)

Usage:
  node query-json-db.js search <word> [language]    - Search for a word
  node query-json-db.js list [language] [limit]     - List words in a language
  node query-json-db.js languages                   - List all languages
  node query-json-db.js stats                       - Show database statistics
      `);
  }
}

// Run the CLI
processArguments();