/**
 * Utility functions for processing wikitext
 */

// Clean a definition string by removing templates, formatting, etc.
export function cleanDefinitionText(text) {
    return text
      // Remove senseid templates
      .replace(/{{senseid\|[^}]+}}/g, '')
      
      // Remove {{lb|en|...}} language/context templates
      .replace(/{{lb\|[^}]+}}/g, '')
      
      // Remove {{...}} templates but keep their displayed content if possible
      .replace(/{{(ux|syn|ant|cot)\|[^|]+\|([^}]+)}}/g, '$2')
      .replace(/{{[^}]+}}/g, '')
      
      // Convert [[word|display]] wiki links to just the display text
      .replace(/\[\[[^]|]+\|([^]]+)\]\]/g, '$1')
      
      // Convert [[word]] wiki links to just the word
      .replace(/\[\[([^]]+)\]\]/g, '$1')
      
      // Remove formatting marks
      .replace(/'''/g, '')
      .replace(/''/g, '')
      
      // Remove HTML tags
      .replace(/<[^>]+>/g, '')
      
      // Remove footnotes/references
      .replace(/\{\{ref\|[^}]+\}\}/g, '')
      
      // Remove multiple spaces and trim
      .replace(/\s+/g, ' ')
      .trim();
  }
  
  // Extract a language code from a language name
  export function getLanguageCode(languageName) {
    // Common language mappings
    const languageMap = {
      'english': 'en',
      'french': 'fr',
      'german': 'de',
      'spanish': 'es',
      'italian': 'it',
      'portuguese': 'pt',
      'russian': 'ru',
      'japanese': 'ja',
      'chinese': 'zh',
      'arabic': 'ar',
      'hindi': 'hi',
      'korean': 'ko',
      'latin': 'la',
      'greek': 'el',
      'swedish': 'sv',
      'dutch': 'nl',
      'finnish': 'fi',
      'danish': 'da',
      'norwegian': 'no',
      'polish': 'pl',
      'turkish': 'tr',
      'thai': 'th',
      'czech': 'cs',
      'hungarian': 'hu',
      'hebrew': 'he'
    };
    
    const normalizedName = languageName.toLowerCase();
    return languageMap[normalizedName] || 'unknown';
  }
  
  // Extract examples from a definition line
  export function extractExamples(line) {
    const examples = [];
    
    // Extract ":#: Example text" format
    const exampleMatches = line.match(/^#:\s*(.+)$/gm);
    if (exampleMatches) {
      exampleMatches.forEach(match => {
        const exampleText = match.replace(/^#:\s*/, '');
        examples.push(cleanDefinitionText(exampleText));
      });
    }
    
    // Extract {{ux|en|Example text}} format
    const uxMatches = line.match(/{{ux\|[^|]+\|([^}]+)}}/g);
    if (uxMatches) {
      uxMatches.forEach(match => {
        const exampleText = match.replace(/{{ux\|[^|]+\|([^}]+)}}/, '$1');
        examples.push(cleanDefinitionText(exampleText));
      });
    }
    
    return examples;
  }
  
  // Extract sense ID from a definition line
  export function extractSenseId(line) {
    const senseIdMatch = line.match(/{{senseid\|[^|]+\|([^}]+)}}/);
    return senseIdMatch ? senseIdMatch[1] : null;
  }