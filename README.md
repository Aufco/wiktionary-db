# Wiktionary Definition Processor

A system for processing Wiktionary definition entries with wiki markup into clean text definitions using MediaWiki + Scribunto in a Docker environment.

## Project Structure

```
C:\Users\benau\wiktionary-db\
├── .gitignore                     # Excludes data directory and archive from git
├── docker/                        # Docker configuration files
│   ├── docker-compose.yml         # Container orchestration for MediaWiki and MariaDB
│   └── mediawiki/                 # MediaWiki configuration
│       └── LocalSettings.php      # MediaWiki settings for Wiktionary processing
├── src/                           # Python processing system
│   ├── main.py                    # Entry point for the application
│   ├── database.py                # Database operations for SQLite
│   ├── wiki_processor.py          # Processes definitions using MediaWiki API
│   ├── template_manager.py        # Downloads templates and modules from Wiktionary
│   └── logger.py                  # Logging setup for the application
├── cache/                         # Template and module cache
│   ├── Template/                  # Cached Wiktionary templates
│   └── Module/                    # Cached Wiktionary modules
├── logs/                          # Processing logs output
├── tests/                         # Test scripts
│   └── test_processor.py          # Tests with sample definitions
└── run.ps1                        # Single command launcher script
```

## Quick Start

Run the system with a single command:

```powershell
.\run.ps1
```

For testing with a limited number of entries:

```powershell
.\run.ps1 -test -limit 10
```

## Project Description

This system processes over 1 million Wiktionary definition entries with wiki markup and transforms them into clean text definitions by leveraging Wiktionary's own templates and modules.

The workflow:
1. Sets up a Docker container with MediaWiki + Scribunto
2. Reads definition entries from a SQLite database (wiktionary1.db)
3. Processes each definition through MediaWiki
4. Downloads missing templates/modules from Wiktionary when needed
5. Stores processed definitions back in the database

## Database Structure

The SQLite database (wiktionary1.db) has the following structure:

- `words` table:
  - `id` (INTEGER)
  - `word` (TEXT)
  - `total_senses` (INTEGER)

- `definitions` table:
  - `id` (INTEGER)
  - `word_id` (INTEGER)
  - `part_of_speech` (TEXT)
  - `raw_definition_text` (TEXT)
  - `processed_definition_text` (TEXT)
  - `sense_number` (INTEGER)