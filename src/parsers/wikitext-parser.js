import { 
    getOrCreatePartOfSpeech, 
    createDefinition, 
    createExample 
  } from '../database/operations.js';
  
  // Language codes and names mapping
  const LANGUAGE_MAP = {
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'it': 'Italian',
    // Add more as needed
  };
  
  // Class to represent a parsed entry in a specific language
  class ParsedEntry {
    constructor(word, language) {
      this.word = word;
      this.language = language;
      this.sections = []; // Array of PosSection objects
    }
  
    addSection(posSection) {
      this.sections.push(posSection);
    }
  
    saveToDatabase(entryId) {
      for (const section of this.sections) {
        section.saveToDatabase(entryId);
      }
    }
  }
  
  // Class to represent a part-of-speech section
  class PosSection {
    constructor(pos, etymologyNumber = null) {
      this.pos = pos;
      this.etymologyNumber = etymologyNumber;
      this.definitions = [];
    }
  
    addDefinition(definition, senseId = null) {
      this.definitions.push({ text: definition, senseId, examples: [] });
    }
  
    addExample(definitionIndex, example) {
      if (definitionIndex >= 0 && definitionIndex < this.definitions.length) {
        this.definitions[definitionIndex].examples.push(example);
      }
    }
  
    saveToDatabase(entryId) {
      const posId = getOrCreatePartOfSpeech(this.pos);
      
      for (const def of this.definitions) {
        const definitionId = createDefinition(
          entryId, 
          posId, 
          def.text, 
          def.senseId, 
          this.etymologyNumber
        );
        
        // Save examples
        for (const example of def.examples) {
          createExample(definitionId, example);
        }
      }
    }
  }
  
  // Main function to parse wikitext content
  export function parseWikitext(title, wikitext) {
    const entries = [];
    let currentLanguage = null;
    let currentEntry = null;
    let currentPos = null;
    let currentEtymology = null;
    let lastDefinitionIndex = -1;
  
    // Split content into lines and process each
    const lines = wikitext.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check for language headers (==English==, ==French==, etc.)
      const languageMatch = line.match(/^==\s*([^=]+)\s*==$/);
      if (languageMatch) {
        const langName = languageMatch[1].trim();
        // Find language code based on name (simplified mapping here)
        const langCode = Object.keys(LANGUAGE_MAP).find(
          code => LANGUAGE_MAP[code].toLowerCase() === langName.toLowerCase()
        ) || 'unknown';
        
        currentLanguage = { code: langCode, name: langName };
        currentEntry = new ParsedEntry(title, currentLanguage);
        entries.push(currentEntry);
        currentPos = null;
        currentEtymology = null;
        continue;
      }
      
      // If no language is detected yet, skip this line
      if (!currentEntry) continue;
      
      // Check for etymology sections (===Etymology===, ===Etymology 1===, etc.)
      const etymologyMatch = line.match(/^===\s*Etymology(\s+(\d+))?\s*===$/);
      if (etymologyMatch) {
        currentEtymology = etymologyMatch[2] ? parseInt(etymologyMatch[2]) : 1;
        continue;
      }
      
      // Check for part of speech headers (===Noun===, ===Verb===, etc.)
      const posMatch = line.match(/^===\s*([^=]+)\s*===$/);
      if (posMatch && !line.includes('Etymology')) {
        const pos = posMatch[1].trim();
        currentPos = new PosSection(pos, currentEtymology);
        currentEntry.addSection(currentPos);
        lastDefinitionIndex = -1;
        continue;
      }
      
      // If no POS is detected yet, skip this line
      if (!currentPos) continue;
      
      // Check for definitions (# This is a definition)
      const defMatch = line.match(/^#\s*(.+)$/);
      if (defMatch) {
        // Check if it's a sub-definition (#:, ##, etc.) or example
        if (line.startsWith('#:') || line.includes('{{ux|')) {
          // It's an example, add it to the last definition
          if (lastDefinitionIndex >= 0) {
            const exampleText = defMatch[1].replace(/{{ux\|[^}]+}}/g, '').trim();
            currentPos.addExample(lastDefinitionIndex, exampleText);
          }
        } else {
          // It's a definition, extract sense ID if present
          const senseIdMatch = line.match(/{{senseid\|[^|]+\|([^}]+)}}/);
          const senseId = senseIdMatch ? senseIdMatch[1] : null;
          
          // Clean up the definition text
          let defText = defMatch[1]
            .replace(/{{senseid\|[^}]+}}/g, '')  // Remove senseid templates
            .replace(/{{[^}]+}}/g, '')           // Remove other templates
            .replace(/\[\[[^]]+\|([^]]+)\]\]/g, '$1') // Replace [[link|text]] with text
            .replace(/\[\[([^]]+)\]\]/g, '$1')   // Replace [[link]] with link
            .replace(/''/g, '')                  // Remove formatting
            .trim();
          
          currentPos.addDefinition(defText, senseId);
          lastDefinitionIndex++;
        }
      }
    }
    
    return entries;
  }