Wiktionary Database Project
A Next.js application that creates and serves a searchable database of Wiktionary data, including words, languages, and definitions.
Project Overview
This project downloads and processes Wiktionary data dumps to create a SQLite database with the following structure:

Words from various languages
Multiple definitions per word
Part of speech information

Setup Instructions

Clone the repository:

bashCopygit clone https://github.com/Aufco/wiktionary-db.git
cd wiktionary-db

Download the required Wiktionary data files:

powershellCopy.\scripts\download-data.ps1

Extract the compressed files:

powershellCopynode .\scripts\extract-files.js

Process the data and build the database:

powershellCopynode .\scripts\process-data.js

Start the Next.js application:

powershellCopycd src
npm install
npm run dev

Access the application at http://localhost:3000

File Structure
C:\Users\benau\wiktionary-db\
├── .gitignore                    # Git ignore rules for large data files
├── data\                         # Data directory
│   ├── enwiktionary-latest-pages-articles.xml\  # Extraction directory
│   │   └── enwiktionary-latest-pages-articles.xml  # Main Wiktionary XML data (~10GB)
│   └── sample-2000-lines.xml     # Sample file with 2000 lines of XML for analysis
├── scripts\
│   ├── download-data.ps1         # PowerShell script to download Wiktionary files
│   ├── extract-files.js          # Extracts compressed data files
│   ├── extract-sample.js         # Creates sample file from large XML
│   ├── parse-wiktionary.js       # Parses XML data into database
│   └── process-data.js           # Main data processing script
└── src\                          # Next.js application
    ├── .gitignore                # Next.js gitignore
    ├── README.md                 # Next.js README
    ├── app\
    │   └── api\
    │       └── search\
    │           └── route.js      # API endpoint for word lookups
    ├── lib\
    │   └── db\
    │       └── schema.js         # SQLite database schema
    ├── package.json              # Dependencies and scripts
    ├── public\                   # Static assets
    └── src\
        └── app\                  # Next.js app directory
            ├── globals.css       # Global styles
            ├── layout.tsx        # App layout component
            └── page.tsx          # Main page component