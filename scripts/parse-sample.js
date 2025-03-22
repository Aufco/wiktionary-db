const fs = require('fs');
const path = require('path');
const xml2js = require('xml2js');

// Paths
const dataDir = path.join(__dirname, '..', 'data');
const dbDir = path.join(__dirname, '..', 'src', 'db');
const sampleFile = path.join(dataDir, 'sample-2000-lines.xml');
const jsonDbFile = path.join(dbDir, 'wiktionary-db.json');

// Regular expressions to extract information
const languageHeaderRegex = /^==\s*([a-zA-Z]+)\s*==$/m;
const posHeaderRegex = /^===\s*([a-zA-Z ]+)\s*===$/m;
const definitionRegex = /^#\s*(.+)$/m;

// Ensure database directory exists
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Initialize database
let database = {
  languages: {},
  words: {},
  definitions: [],
  nextIds: {
    language: 1,
    word: 1,
    definition: 1
  }
};

// Check if database already exists
if (fs.existsSync(jsonDbFile)) {
  try {
    database = JSON.parse(fs.readFileSync(jsonDbFile, 'utf8'));
    console.log('Loaded existing database');
  } catch (err) {
    console.error('Error loading database:', err);
    // Continue with empty database
  }
}

// Add English as a default language if not exists
if (!database.languages['English']) {
  database.languages['English'] = {
    id: database.nextIds.language++,
    code: 'en',
    name: 'English'
  };
}

// Transaction function - modified to use in-memory database
function insertWordWithDefinitions(title, languageName, partOfSpeech, definitions) {
  // Skip non-word entries or templates/categories
  if (title.includes(':') || !languageName) {
    return;
  }
  
  // Get or insert language
  let languageId;
  if (!database.languages[languageName]) {
    languageId = database.nextIds.language++;
    database.languages[languageName] = {
      id: languageId,
      code: languageName.toLowerCase().substring(0, 2),
      name: languageName
    };
  } else {
    languageId = database.languages[languageName].id;
  }
  
  // Create a unique key for word + language
  const wordKey = `${title}|${languageId}`;
  
  // Get or insert word
  let wordId;
  if (!database.words[wordKey]) {
    wordId = database.nextIds.word++;
    database.words[wordKey] = {
      id: wordId,
      word: title,
      language_id: languageId
    };
  } else {
    wordId = database.words[wordKey].id;
  }
  
  // Insert definitions
  for (const def of definitions) {
    const definitionId = database.nextIds.definition++;
    database.definitions.push({
      id: definitionId,
      word_id: wordId,
      part_of_speech: partOfSpeech,
      definition: def,
      example: null
    });
  }
}

// Process Wiktionary XML
async function processXML() {
  console.log('Reading XML file...');
  const xmlData = fs.readFileSync(sampleFile, 'utf8');
  
  console.log('Parsing XML...');
  const parser = new xml2js.Parser({ explicitArray: false });
  
  try {
    const result = await parser.parseStringPromise(xmlData);
    
    if (!result || !result.mediawiki || !result.mediawiki.page) {
      console.error('XML format not as expected');
      return;
    }
    
    const pages = Array.isArray(result.mediawiki.page) 
      ? result.mediawiki.page 
      : [result.mediawiki.page];
    
    console.log(`Found ${pages.length} pages`);
    
    let wordCount = 0;
    let definitionCount = 0;
    
    // Process each page
    for (const page of pages) {
      if (!page.title || !page.revision || !page.revision.text || !page.revision.text._ || page.ns !== '0') {
        continue; // Skip non-article pages or problematic entries
      }
      
      const title = page.title;
      const content = page.revision.text._;
      
      // Skip non-word entries or templates/categories
      if (title.includes(':')) {
        continue;
      }
      
      // Extract language sections
      const languageMatches = content.match(new RegExp(languageHeaderRegex, 'g'));
      if (!languageMatches) {
        continue;
      }
      
      // Split content into language sections
      const sections = content.split(/^==\s*[a-zA-Z]+\s*==$/m);
      
      if (sections.length <= 1 || languageMatches.length + 1 !== sections.length) {
        continue;
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
            wordCount++;
            definitionCount += definitions.length;
          }
        }
      }
    }
    
    console.log(`Processed ${wordCount} words with ${definitionCount} definitions`);
    
    // Save database to file
    fs.writeFileSync(jsonDbFile, JSON.stringify(database, null, 2));
    console.log(`Database saved to ${jsonDbFile}`);
    
  } catch (err) {
    console.error('Error parsing XML:', err);
  }
}

// Main execution
async function main() {
  console.log('Initializing database...');
  console.log('Database initialized');
  
  console.log('Processing XML file...');
  await processXML();
  
  console.log('Done!');
}

main().catch(err => {
  console.error('Error:', err);
});