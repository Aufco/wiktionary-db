# src/db.py
def update_processed_definition_by_word(self, word: str, raw_text: str, processed_text: str) -> bool:
    """Update a definition by word and raw text."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE definitions
            SET processed_definition_text = ?
            WHERE id IN (
                SELECT d.id
                FROM definitions d
                JOIN words w ON d.word_id = w.id
                WHERE w.word = ? AND d.raw_definition_text = ?
            )
            """,
            (processed_text, word, raw_text)
        )
        conn.commit()
        return cursor.rowcount > 0