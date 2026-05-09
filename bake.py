import sqlite3
import os

def bake_folder_to_sqlite(folder_name='kb', db_name='kb.sqlite3'):
    # Determine the script's current directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(base_dir, folder_name)
    db_path = os.path.join(base_dir, db_name)

    # Check if the kb folder exists
    if not os.path.exists(kb_path):
        print(f"Error: Folder '{folder_name}' not found in {base_dir}")
        return

    # Initialize SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table for files
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            content BLOB NOT NULL,
            path TEXT NOT NULL
        )
    ''')

    # Walk through the folder (including subfolders)
    for root, dirs, files in os.walk(kb_path):
        for filename in files:
            # Ignore hidden files like .DS_Store
            if filename.startswith('.'):
                continue
                
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, kb_path)
            
            try:
                with open(file_path, 'rb') as f:
                    blob_data = f.read()
                    cursor.execute(
                        'INSERT INTO files (filename, content, path) VALUES (?, ?, ?)', 
                        (filename, blob_data, relative_path)
                    )
                print(f"Baked: {relative_path}")
            except Exception as e:
                print(f"Failed to bake {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"\nSuccess! Database created at: {db_path}")

if __name__ == "__main__":
    bake_folder_to_sqlite()
