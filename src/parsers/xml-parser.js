import fs from 'fs';
import XmlStream from 'xml-stream';
import { parseWikitext } from './wikitext-parser.js';
import { 
  getOrCreateLanguage, 
  createEntry, 
  beginTransaction, 
  commitTransaction, 
  rollbackTransaction 
} from '../database/operations.js';

// Parse the XML file and process each page
export async function parseXmlFile(filePath) {
  return new Promise((resolve, reject) => {
    const stream = fs.createReadStream(filePath);
    const xml = new XmlStream(stream);
    
    let pageCount = 0;
    let processedEntries = 0;
    
    // Process each page element
    xml.on('updateElement: page', async (page) => {
      pageCount++;
      
      try {
        const title = page.title;
        const namespaceId = parseInt(page.ns);
        
        // We're only interested in main namespace entries (ns=0)
        if (namespaceId === 0) {
          const text = page.revision.text.$text || '';
          
          // Skip redirects and special pages
          if (!text.startsWith('#REDIRECT') && !title.includes(':')) {
            console.log(`Processing entry: ${title}`);
            
            // Begin transaction for this entry
            beginTransaction();
            
            // Parse the wikitext content
            const parsedEntries = parseWikitext(title, text);
            
            // Save each language's entry to the database
            for (const entry of parsedEntries) {
              const languageId = getOrCreateLanguage(entry.language.code, entry.language.name);
              const entryId = createEntry(title, languageId);
              
              // Save all definitions for this entry
              entry.saveToDatabase(entryId);
            }
            
            // Commit the transaction
            commitTransaction();
            processedEntries++;
          }
        }
      } catch (error) {
        // Rollback on error
        rollbackTransaction();
        console.error(`Error processing page: ${page.title}`, error);
      }
      
      // Log progress periodically
      if (pageCount % 100 === 0) {
        console.log(`Processed ${pageCount} pages, found ${processedEntries} dictionary entries`);
      }
    });
    
    xml.on('error', (err) => {
      console.error('Error parsing XML:', err);
      reject(err);
    });
    
    xml.on('end', () => {
      console.log(`Finished processing ${pageCount} pages, found ${processedEntries} dictionary entries`);
      resolve({ pageCount, processedEntries });
    });
  });
}