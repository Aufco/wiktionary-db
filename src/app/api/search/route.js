import db from '../../../lib/db/schema';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const word = searchParams.get('word');
  const language = searchParams.get('language') || 'English';
  
  if (!word) {
    return new Response(JSON.stringify({ error: 'Word parameter is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  try {
    // Get language ID
    const langQuery = db.prepare('SELECT id FROM languages WHERE name = ? COLLATE NOCASE');
    const langResult = langQuery.get(language);
    
    if (!langResult) {
      return new Response(JSON.stringify({ error: 'Language not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Get word and definitions
    const wordQuery = db.prepare(`
      SELECT w.id, w.word
      FROM words w
      WHERE w.word = ? COLLATE NOCASE AND w.language_id = ?
    `);
    
    const wordResult = wordQuery.get(word, langResult.id);
    
    if (!wordResult) {
      return new Response(JSON.stringify({ error: 'Word not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Get all definitions
    const defQuery = db.prepare(`
      SELECT id, part_of_speech, definition, example
      FROM definitions
      WHERE word_id = ?
    `);
    
    const definitions = defQuery.all(wordResult.id);
    
    return new Response(JSON.stringify({
      word: wordResult.word,
      language,
      definitions
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Error querying database:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}