import sqlite3
from app.db.connection import get_db_connection
from app.cli.menu import CLIMenu
from app.repositories.request_repository import RequestRepository

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

    request_repo = RequestRepository()
    request_repo.initialize_statuses_and_transitions()

if __name__ == "__main__":
    initialize_database()
    menu = CLIMenu()
    menu.run()
