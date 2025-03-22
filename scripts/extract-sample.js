const fs = require('fs');
const readline = require('readline');
const path = require('path');

// Updated path to point to the nested file
const xmlFilePath = path.join(
  __dirname, 
  '..', 
  'data', 
  'enwiktionary-latest-pages-articles.xml', 
  'enwiktionary-latest-pages-articles.xml'
);
const sampleFilePath = path.join(__dirname, '..', 'data', 'sample-2000-lines.xml');

async function extractSample() {
  console.log(`Extracting sample from: ${xmlFilePath}`);
  console.log(`Writing to: ${sampleFilePath}`);
  
  try {
    // Check if the source file exists
    if (!fs.existsSync(xmlFilePath)) {
      console.error(`ERROR: Source file not found at ${xmlFilePath}`);
      return;
    }
    
    const fileStream = fs.createReadStream(xmlFilePath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });

    const writeStream = fs.createWriteStream(sampleFilePath);
    let lineCount = 0;
    
    for await (const line of rl) {
      writeStream.write(line + '\n');
      lineCount++;
      
      if (lineCount % 500 === 0) {
        console.log(`Processed ${lineCount} lines`);
      }
      
      if (lineCount >= 2000) {
        break;
      }
    }
    
    writeStream.end();
    console.log(`Successfully extracted ${lineCount} lines to ${sampleFilePath}`);
  } catch (error) {
    console.error('Error during extraction:', error);
    console.error('Error message:', error.message);
  }
}

extractSample();