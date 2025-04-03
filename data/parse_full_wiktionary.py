import os
import re
import sqlite3
import time
from datetime import datetime

# Set paths for input file and output database
input_file = r"C:\Users\benau\wiktionary-db\data\enwiktionary-latest-pages-articles.xml"
template_dir = r"C:\Users\benau\wiktionary-db\data\Template"
module_dir = r"C:\Users\benau\wiktionary-db\data\Module"
output_dir = os.path.dirname(os.path.abspath(__file__))
output_db = os.path.join(output_dir, "wiktionary1.db")
max_words = 20  # Set to 0 for unlimited processing
log_file = os.path.join(output_dir, "parser_log.txt")

# Create a fresh log file
with open(log_file, "w", encoding="utf-8") as f:
    f.write("Wiktionary Parser Log - First 20 Pages\n")
    f.write("=====================================\n\n")
    f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

def log_message(message):
    """Log a message to the log file"""
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def create_database():
    """Create SQLite database with the required schema and performance optimizations"""
    try:
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        
        # Performance optimizations
        cursor.execute('PRAGMA page_size = 4096;')
        cursor.execute('PRAGMA cache_size = 10000;')
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        
        # Create words table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            total_senses INTEGER NOT NULL
        )
        ''')
        
        # Create definitions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS definitions (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            part_of_speech TEXT NOT NULL,
            raw_definition_text TEXT NOT NULL,
            processed_definition_text TEXT,
            sense_number INTEGER NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id)
        )
        ''')
        
        # Create index on word for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_word ON words(word)
        ''')
        
        # Create index on word_id and sense_number for faster pagination
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_word_sense ON definitions(word_id, sense_number)
        ''')
        
        conn.commit()
        log_message("Database created successfully")
        return conn
    except Exception as e:
        log_message(f"Error creating database: {str(e)}")
        return None

def extract_definitions(xml_text, word):
    """
    Extract raw definitions from XML text.
    
    Args:
        xml_text (str): XML content for a Wiktionary page
        word (str): The word being processed
        
    Returns:
        list: List of tuples (part_of_speech, raw_definition_text)
    """
    try:
        entries = []
        # Find English definition blocks: {{en-noun}}, {{en-verb}}, etc.
        blocks = list(re.finditer(r"\{\{en-([a-z]+)[^}]*\}\}(.*?)(?=\n==|\Z)", xml_text, re.DOTALL))

        for block in blocks:
            part_of_speech = block.group(1).capitalize()
            block_text = block.group(2)

            for line in block_text.splitlines():
                # Process both main definitions "# " and sub-definitions "## "
                if line.startswith("# ") or line.startswith("## "):
                    # Skip lines that end with a colon (category headers)
                    if line.rstrip().endswith(":"):
                        continue
                    
                    # Remove the leading "# " or "## "
                    if line.startswith("# "):
                        raw_definition_text = line[2:]
                    else:  # "## "
                        raw_definition_text = line[3:]
                    
                    # Add to entries
                    entries.append((part_of_speech, raw_definition_text))

        return entries
    except Exception as e:
        log_message(f"Error extracting definitions for '{word}': {str(e)}")
        return []

def extract_definitions(xml_text, word):
    """
    Extract raw definitions from XML text.
    
    Args:
        xml_text (str): XML content for a Wiktionary page
        word (str): The word being processed
        
    Returns:
        list: List of tuples (part_of_speech, raw_definition_text)
    """
    try:
        entries = []
        # Find English definition blocks: {{en-noun}}, {{en-verb}}, etc.
        blocks = list(re.finditer(r"\{\{en-([a-z]+)[^}]*\}\}(.*?)(?=\n==|\Z)", xml_text, re.DOTALL))

        for block in blocks:
            part_of_speech = block.group(1).capitalize()
            block_text = block.group(2)

            for line in block_text.splitlines():
                # Process both main definitions "# " and sub-definitions "## "
                if line.startswith("# ") or line.startswith("## "):
                    # Skip lines that end with a colon (category headers)
                    if line.rstrip().endswith(":"):
                        continue
                    
                    # Remove the leading "# " or "## "
                    if line.startswith("# "):
                        raw_definition_text = line[2:]
                    else:  # "## "
                        raw_definition_text = line[3:]
                    
                    # Add to entries
                    entries.append((part_of_speech, raw_definition_text))

        return entries
    except Exception as e:
        log_message(f"Error extracting definitions for '{word}': {str(e)}")
        return []

def process_large_dump_file():
    """
    Process the Wiktionary XML dump file and store definitions in a SQLite database.
    No limit on number of words processed, but logs the first 20.
    """
    # Create/connect to the database
    conn = create_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            page_buffer = []
            inside_page = False
            processed_words = 0
            logged_words = 0
            start_time = time.time()
            
            for line in file:
                if "<page>" in line:
                    inside_page = True
                    page_buffer = [line]
                elif "</page>" in line and inside_page:
                    page_buffer.append(line)
                    inside_page = False
                    full_page = "".join(page_buffer)

                    title_match = re.search(r"<title>(.*?)</title>", full_page)
                    if not title_match:
                        continue
                    
                    word = title_match.group(1).strip()
                    
                    try:
                        # Extract definitions
                        definition_entries = extract_definitions(full_page, word)
                        
                        if definition_entries:
                            # Insert the word into the words table
                            total_senses = len(definition_entries)
                            cursor.execute(
                                "INSERT OR IGNORE INTO words (word, total_senses) VALUES (?, ?)",
                                (word, total_senses)
                            )
                            
                            # Get the word_id (either newly inserted or pre-existing)
                            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
                            word_id = cursor.fetchone()[0]
                            
                            # Insert each definition
                            for i, (part_of_speech, raw_definition_text) in enumerate(definition_entries, 1):
                                cursor.execute(
                                    "INSERT INTO definitions (word_id, part_of_speech, raw_definition_text, processed_definition_text, sense_number) VALUES (?, ?, ?, NULL, ?)",
                                    (word_id, part_of_speech, raw_definition_text, i)
                                )
                            
                            # Only log the first 20 words
                            if logged_words < 20:
                                log_message(f"\nWord {logged_words+1}: {word}")
                                log_message(f"Total senses: {total_senses}")
                                
                                # Log each definition
                                for i, (part_of_speech, raw_definition_text) in enumerate(definition_entries, 1):
                                    log_message(f"  {i}. {part_of_speech} - Raw: {raw_definition_text}")
                                
                                logged_words += 1
                                
                                if logged_words == 20:
                                    log_message("\nReached 20 logged words. Continuing processing without logging...")
                            
                            processed_words += 1
                            
                            # Commit every 1000 words
                            if processed_words % 1000 == 0:
                                conn.commit()
                                log_message(f"Processed {processed_words} words...")
                                
                    except Exception as e:
                        log_message(f"Error processing word '{word}': {str(e)}")
                        # Continue with next word
                elif inside_page:
                    page_buffer.append(line)
            
            # Final commit
            conn.commit()
            
            # Log final stats
            elapsed = time.time() - start_time
            log_message(f"\nProcessing complete.")
            log_message(f"Total words processed: {processed_words}")
            log_message(f"Total time: {elapsed:.2f} seconds")
            if elapsed > 0:
                log_message(f"Processing rate: {processed_words / elapsed:.2f} words/second")
            log_message(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
    except Exception as e:
        log_message(f"Error processing file: {str(e)}")
    
    finally:
        # Close the database connection
        if conn:
            conn.close()

def main():
    """Main function to run the script"""
    start_time = time.time()
    log_message(f"Starting Wiktionary parser, output will be stored in {output_db}")
    log_message(f"Processing file: {input_file}")
    log_message(f"Template directories (for future processing): {template_dir}")
    log_message(f"Module directories (for future processing): {module_dir}")
    
    # Process the dump file
    process_large_dump_file()
    
    elapsed = time.time() - start_time
    log_message(f"Total script execution time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()