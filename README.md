# Wiktionary Database Project

A Next.js application that creates and serves a searchable database of Wiktionary data, including words, languages, and definitions.

## Project Overview

This project downloads and processes Wiktionary data dumps to create a SQLite database with the following structure:

- Words from various languages
- Multiple definitions per word
- Part of speech information

## Features

- Extract and parse Wiktionary XML dump files
- Store data in a SQLite database
- REST API to query the dictionary
- Next.js web interface for searching

## Prerequisites

- Node.js (v18 or later)
- PowerShell
- 7-Zip (for extracting compressed files)
- At least 15GB of free disk space for full dataset processing

## Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/yourusername/wiktionary-db.git
cd wiktionary-db
```

2. Install dependencies:

```bash
npm install
cd src
npm install
cd ..
```

3. Download the required Wiktionary data files:

```bash
npm run download
```

4. Extract the compressed files:

```bash
npm run extract
```

5. Extract a sample file for testing (optional):

```bash
npm run extract-sample
```

6. Process the sample data to test database creation:

```bash
npm run parse-sample
```

7. Process the full data to build the complete database (this will take a long time):

```bash
npm run parse-full
```

8. Start the Next.js application:

```bash
npm run dev
```

9. Access the application at http://localhost:3000

## Scripts

- `npm run download` - Downloads Wiktionary data files
- `npm run extract` - Extracts compressed data files
- `npm run extract-sample` - Creates a sample file from the large XML
- `npm run parse-sample` - Parses the sample file into the database
- `npm run parse-full` - Parses the full XML into the database
- `npm run query` - Command-line tool to query the database
- `npm run dev` - Starts the development server
- `npm run build` - Builds the application for production
- `npm run start` - Starts the production server

## Querying the Database

You can use the included query tool to search the database from the command line:

```bash
# Search for a word
npm run query search dictionary English

# List words in a language
npm run query list English 20

# List all languages
npm run query languages

# Show database statistics
npm run query stats
```

## API Routes

The application provides the following API endpoints:

- `GET /api/search?word=<word>&language=<language>` - Search for a word
- `POST /api/search` with body `{"pattern": "<pattern>", "language": "<language>", "limit": <number>}` - Search for words matching a pattern
- `OPTIONS /api/search` - List all available languages

## File Structure

```
C:\Users\benau\wiktionary-db\
├── .gitignore                    # Git ignore rules for large data files
├── README.md                     # This file
├── package.json                  # Project dependencies and scripts
├── data\                         # Data directory
│   ├── enwiktionary-latest-pages-articles.xml\  # Extraction directory
│   │   └── enwiktionary-latest-pages-articles.xml  # Main Wiktionary XML data (~10GB)
│   └── sample-2000-lines.xml     # Sample file with 2000 lines of XML for analysis
├── scripts\
│   ├── download-data.ps1         # PowerShell script to download Wiktionary files
│   ├── extract-files.js          # Extracts compressed data files
│   ├── extract-sample.js         # Creates sample file from large XML
│   ├── parse-sample.js           # Parses sample XML data into database
│   ├── parse-wiktionary-full.js  # Parses full XML data into database
│   └── query-db.js               # Command-line tool to query the database
└── src\                          # Next.js application
    ├── .gitignore                # Next.js gitignore
    ├── README.md                 # Next.js README
    ├── app\
    │   ├── api\
    │   │   └── search\
    │   │       └── route.js      # API endpoint for word lookups
    │   ├── globals.css           # Global styles
    │   ├── layout.tsx            # App layout component
    │   └── page.tsx              # Main page component
    ├── lib\
    │   └── db\
    │       └── schema.js         # SQLite database schema
    ├── package.json              # Dependencies and scripts
    ├── public\                   # Static assets
    └── db\                       # Database directory
        └── wiktionary.db         # SQLite database (created by scripts)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Wiktionary for providing the open data used in this project
- Contributors to the open-source libraries used in this project
