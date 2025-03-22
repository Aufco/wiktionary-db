import path from 'path';
import { fileURLToPath } from 'url';
import { setupDatabase } from './database/schema.js';
import { parseXmlFile } from './parsers/xml-parser.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('Wiktionary DB Parser Starting...');
  
  // Set up the database
  console.log('Setting up database...');
  setupDatabase();
  
  // Path to the sample XML file
  const sampleFilePath = path.join(__dirname, '../data/sample-1000-lines.xml');
  
  // Parse the sample file
  console.log(`Parsing sample file: ${sampleFilePath}`);
  try {
    const result = await parseXmlFile(sampleFilePath);
    console.log(`Processed ${result.pageCount} pages and found ${result.processedEntries} entries`);
    console.log('Sample processing complete.');
    
    // Once the sample processing works well, you can uncomment the following
    // to process the full file
    /*
    const fullFilePath = path.join(__dirname, '../data/enwiktionary-latest-pages-articles.xml');
    console.log(`\nParsing full Wiktionary file: ${fullFilePath}`);
    console.log('This may take several hours...');
    
    const fullResult = await parseXmlFile(fullFilePath);
    console.log(`Processed ${fullResult.pageCount} pages and found ${fullResult.processedEntries} entries`);
    console.log('Full processing complete.');
    */
  } catch (error) {
    console.error('Error during parsing:', error);
    process.exit(1);
  }
}

main().catch(console.error);