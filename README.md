# Wiktionary Definition Processor

This project processes raw definition text from Wiktionary using Wiktionary's own templates and modules to produce clean, formatted definition text.

## Requirements

- Python 3.8 or higher
- SQLite3
- PowerShell
- Windows 11 ARM

## Setup

1. Clone this repository to `C:\Users\benau\wiktionary-db`
2. Ensure the SQLite database is at `C:\Users\benau\wiktionary-db\data\wiktionary1.db`
3. Install the required dependencies:

```powershell
pip install -r requirements.txt