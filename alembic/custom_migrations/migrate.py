import sqlite3
import os


def cleanup_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Твій перевірений шлях до бази
    db_path = os.path.join(project_root, "data", "database.db")

    print(f"Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_drop = ["show_advanced_errors", "target_level"]

    for col in columns_to_drop:
        try:
            # Спроба видалити колонку напряму (працює в SQLite 3.35.0+)
            cursor.execute(f"ALTER TABLE users DROP COLUMN {col};")
            print(f"✅ Column '{col}' successfully dropped.")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower():
                print(f"⏩ Column '{col}' already removed or doesn't exist.")
            else:
                print(f"❌ Error removing '{col}': {e}")
                print("Your SQLite version might be too old for DROP COLUMN.")

    conn.commit()
    conn.close()
    print("Cleanup finished!")


if __name__ == "__main__":
    cleanup_db()