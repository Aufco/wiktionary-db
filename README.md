# Wiktionary Database Parser

This project parses Wiktionary XML dumps and stores the extracted data in a SQLite database.

## Project Structure

```
wiktionary-db/
├── data/                  # XML files
│   ├── sample-1000-lines.xml         # Sample for testing
│   └── enwiktionary-latest-pages-articles.xml  # Full dump
├── src/
│   ├── parsers/           # XML and wikitext parsing code
│   ├── database/          # Database schema and operations
│   ├── utils/             # Helper functions 
│   └── index.js           # Main entry point
├── package.json
└── sqlite.db              # The output database
```

## Setup

1. Make sure you have Node.js installed (v14+ recommended)
2. Install dependencies:
   ```
   npm install
   ```

## Usage

1. First test the parser with the sample file:
   ```
   npm run test
   ```

2. Process the sample file:
   ```
   npm start
   ```

3. To process the full file, edit `src/index.js` and uncomment the section for processing the full file, then run:
   ```
   npm start
   ```

## Database Schema

The SQLite database includes the following tables:

- `languages`: Stores language codes and names
- `entries`: Stores dictionary words with their language
- `parts_of_speech`: Stores part of speech categories
- `definitions`: Stores definitions with references to entries and parts of speech
- `examples`: Stores example sentences for definitions

## Notes for Processing Full Dataset

- The full Wiktionary XML file is very large (~10GB), so processing it will take several hours
- The parser is designed to handle the file incrementally, so it doesn't load the entire file into memory
- For the full file processing, consider monitoring memory usage and adding more robust error handling

## Extending the Parser

To support more complex wikitext parsing:

1. Enhance the `wikitext-parser.js` file to handle additional templates and markup
2. Add more language codes to the language mapping
3. Add support for additional features like etymology parsing, translations, etc.

## Limitations

The current implementation has some limitations:

- Limited handling of complex wikitext templates
- Simplified part-of-speech detection
- Basic example extraction
- Limited language detection

These can be improved by enhancing the wikitext parser as needed.