import sqlite3
import os


def drop_is_warning_column():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Verify this path matches your database location
    db_path = r"C:\Users\nazar\Desktop\pet projects\linguistic-error-analyzer\data\database.db"

    print(f"Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Replace 'parsed_errors' with your exact table name if different
        cursor.execute("ALTER TABLE parsed_errors DROP COLUMN is_warning;")
        print("Column 'is_warning' successfully dropped.")
    except sqlite3.OperationalError as e:
        print(f"Error removing 'is_warning': {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    drop_is_warning_column()