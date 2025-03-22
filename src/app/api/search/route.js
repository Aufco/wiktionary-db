import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Get database path
const dbPath = path.join(process.cwd(), 'db', 'wiktionary-db.json');

// Initialize database
let database = null;

/**
 * Load database from JSON file
 */
async function loadDatabase() {
  try {
    if (!database) {
      const data = await fs.promises.readFile(dbPath, 'utf8');
      database = JSON.parse(data);
      
      // Create indexes if they don't exist
      if (!database.indexes) {
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
        await fs.promises.writeFile(dbPath, JSON.stringify(database, null, 2));
      }
    }
    return true;
  } catch (error) {
    console.error('Error loading database:', error.message);
    return false;
  }
}

/**
 * Search for a word by name and language
 */
export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const word = searchParams.get('word');
  const language = searchParams.get('language') || 'English';
  
  // Validate input
  if (!word) {
    return NextResponse.json({ error: 'Word parameter is required' }, { status: 400 });
  }
  
  try {
    // Load database
    const loaded = await loadDatabase();
    if (!loaded) {
      return NextResponse.json({ error: 'Database not available' }, { status: 500 });
    }
    
    // Find language
    const lang = database.indexes.languageByName[language.toLowerCase()];
    
    if (!lang) {
      return NextResponse.json({ error: 'Language not found' }, { status: 404 });
    }
    
    // Find word
    const words = database.indexes.wordsByLanguageId[lang.id] || [];
    const wordObj = words.find(w => w.word.toLowerCase() === word.toLowerCase());
    
    if (!wordObj) {
      return NextResponse.json({ error: 'Word not found' }, { status: 404 });
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
    
    // Group definitions by part of speech
    const definitionsByPos = {};
    
    for (const def of definitions) {
      const pos = def.part_of_speech || 'Unknown';
      
      if (!definitionsByPos[pos]) {
        definitionsByPos[pos] = [];
      }
      
      definitionsByPos[pos].push({
        id: def.id,
        definition: def.definition,
        example: def.example
      });
    }
    
    // Format response
    const response = {
      word: wordObj.word,
      language,
      partsOfSpeech: Object.keys(definitionsByPos).map(pos => ({
        type: pos,
        definitions: definitionsByPos[pos]
      }))
    };
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error querying database:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

/**
 * Search for words that match a pattern
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const { pattern, language = 'English', limit = 20 } = body;
    
    // Validate input
    if (!pattern) {
      return NextResponse.json({ error: 'Pattern parameter is required' }, { status: 400 });
    }
    
    // Load database
    const loaded = await loadDatabase();
    if (!loaded) {
      return NextResponse.json({ error: 'Database not available' }, { status: 500 });
    }
    
    // Find language
    const lang = database.indexes.languageByName[language.toLowerCase()];
    
    if (!lang) {
      return NextResponse.json({ error: 'Language not found' }, { status: 404 });
    }
    
    // Search for words matching pattern
    const words = database.indexes.wordsByLanguageId[lang.id] || [];
    const patternLower = pattern.toLowerCase();
    
    const matchingWords = words
      .filter(word => word.word.toLowerCase().includes(patternLower))
      .map(word => {
        const definitionCount = (database.indexes.definitionsByWordId[word.id] || []).length;
        return {
          id: word.id,
          word: word.word,
          definition_count: definitionCount
        };
      })
      .sort((a, b) => a.word.localeCompare(b.word))
      .slice(0, limit);
    
    return NextResponse.json({
      language,
      pattern,
      count: matchingWords.length,
      words: matchingWords
    });
  } catch (error) {
    console.error('Error searching words:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

/**
 * List available languages
 */
export async function OPTIONS(request) {
  try {
    // Load database
    const loaded = await loadDatabase();
    if (!loaded) {
      return NextResponse.json({ error: 'Database not available' }, { status: 500 });
    }
    
    // Get all languages
    const languages = Object.values(database.languages).map(lang => {
      const words = database.indexes.wordsByLanguageId[lang.id] || [];
      return {
        id: lang.id,
        code: lang.code,
        name: lang.name,
        word_count: words.length
      };
    }).sort((a, b) => a.name.localeCompare(b.name));
    
    return NextResponse.json({ languages });
  } catch (error) {
    console.error('Error listing languages:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}