import sqlite3
import logging

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger('wiktionary_processor')
        
    def _get_connection(self):
        """Get a database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise
            
    def reset_processed_definitions(self):
        """Reset all processed_definition_text fields to NULL"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE definitions SET processed_definition_text = NULL")
            conn.commit()
            self.logger.info(f"Reset {cursor.rowcount} processed definition entries")
            conn.close()
        except sqlite3.Error as e:
            self.logger.error(f"Error resetting definitions: {e}")
            raise
            
    def get_total_definitions_count(self):
        """Get the total number of definitions"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM definitions")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except sqlite3.Error as e:
            self.logger.error(f"Error counting definitions: {e}")
            raise
            
    def get_definitions(self, limit=None):
        """Get all definitions to process"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("""
                    SELECT id, word_id, raw_definition_text 
                    FROM definitions 
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, word_id, raw_definition_text 
                    FROM definitions
                """)
                
            rows = cursor.fetchall()
            conn.close()
            return [(row['id'], row['word_id'], row['raw_definition_text']) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving definitions: {e}")
            raise
            
    def update_processed_definition(self, definition_id, processed_text):
        """Update a definition with its processed text"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE definitions 
                SET processed_definition_text = ? 
                WHERE id = ?
            """, (processed_text, definition_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.logger.error(f"Error updating definition {definition_id}: {e}")
            raise
