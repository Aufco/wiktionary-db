import sqlite3

db_path = r"C:\Users\benau\wiktionary-db\data\wiktionary1.db"

def print_table_columns(conn, table_name):
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        rows = cursor.fetchall()
        if not rows:
            print(f"⚠️ No columns found in '{table_name}'.")
        else:
            print(f"\n📋 Columns in '{table_name}':")
            for row in rows:
                col_id, name, col_type, notnull, default, pk = row
                print(f"- {name} ({col_type})")
    except sqlite3.Error as e:
        print(f"❌ Error accessing table '{table_name}': {e}")

with sqlite3.connect(db_path) as conn:
    print_table_columns(conn, "words")
    print_table_columns(conn, "definitions")
