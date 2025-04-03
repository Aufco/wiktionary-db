WIKTIONARY DATABASE PROJECT

This repository contains tools for processing and analyzing data from Wiktionary (the free dictionary project from Wikimedia). The scripts extract definitions, templates, and other linguistic information from the Wiktionary XML dump and store them in structured SQLite databases for easier access and analysis.

CONTENTS

Data Files:
- enwiktionary-latest-pages-articles.xml - The raw XML dump from Wiktionary containing all articles and definitions
- wiktionary.db - SQLite database with processed definitions (cleaned and normalized text)
- wiktionary1.db - SQLite database with unprocessed/raw definitions (preserves original markup)
- unique_template_names.txt - List of template names extracted from Wiktionary pages

Script Files:
- extract_templates.py - Extracts template names from the Wiktionary XML dump
- download_templates_and_modules.py - Downloads template content and Lua modules from Wiktionary API
- parse_full_wiktionary.py - Parses XML dump and stores raw definitions in wiktionary1.db
- parse_full_wiktionary1.py - Parses XML dump with advanced processing for cleaned definitions in wiktionary.db
- print_table_headers.py - Utility script to print database table structures
- parser_log.txt - Log output from the parsing process showing first 20 words and statistics

DATABASE STRUCTURE

The SQLite databases contain two main tables:

words:
- id - Primary key
- word - The word or term
- total_senses - Number of definitions for this word

definitions:
- id - Primary key
- word_id - Foreign key to words table
- part_of_speech - Grammatical category (Noun, Verb, Adjective, etc.)
- definition_text - The processed definition text (in wiktionary.db)
- raw_definition_text - The unprocessed definition text (in wiktionary1.db)
- sense_number - The sequence number of this definition

USAGE

1. Extracting templates:
   python extract_templates.py
   This processes the XML dump and creates a list of template names used in definitions.

2. Downloading templates and modules:
   python download_templates_and_modules.py
   Fetches the actual template content and module code from Wiktionary API.

3. Parsing definitions:
   python parse_full_wiktionary.py  # For raw definitions
   python parse_full_wiktionary1.py  # For processed definitions
   Processes the XML dump and populates the SQLite databases.

4. Viewing database structure:
   python print_table_headers.py
   Shows the table structure of the databases.

PROCESSING DETAILS

The parsing scripts perform several operations:
- Extract English definitions from Wiktionary pages
- Parse various templates and markup ({{en-noun}}, {{lb|en|...}}, etc.)
- Clean up and normalize definition text (in parse_full_wiktionary1.py)
- Store structured data in SQLite databases

The processed database (wiktionary.db) contains definitions with templates expanded and markup removed, while the unprocessed database (wiktionary1.db) preserves the original Wiktionary markup.

STATISTICS

Based on the parser log, the processing handled:
- Over 787,000 words
- Processing rate of about 4,000 words per second
- Total processing time of about 3 minutes (192 seconds)

EXAMPLE WORDS

The first processed words include: dictionary, free, thesaurus, encyclopedia, portmanteau, encyclopaedia, cat, gratis, word, livre, book, pound, GDP, rain cats and dogs, pond, nonsense, pie, A, crow, and raven.