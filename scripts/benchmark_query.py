import time
import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.connection import get_db_connection

def benchmark():
    conn = get_db_connection(); cursor = conn.cursor()
    # Сброс индексов для чистоты эксперимента
    cursor.execute(\"DROP INDEX IF EXISTS idx_requests_perf\")
    conn.commit()

    query = \"\"\"
        SELECT r.number, r.due_date, e.full_name
        FROM requests r
        JOIN employees e ON r.executor_id = e.id
        JOIN statuses s ON r.status_id = s.id
        WHERE r.executor_id = 1 AND s.code = 'IN_PROGRESS' AND r.due_date < DATE('now')
        ORDER BY r.due_date ASC
    \"\"\"
    
    print(\"--- Замер БЕЗ индексов ---\")
    start = time.perf_counter()
    cursor.execute(query); cursor.fetchall()
    time_before = time.perf_counter() - start
    print(f\"Время: {time_before:.6f} сек.\")

    print(\"\\n--- Оптимизация: Создание индекса ---\")
    cursor.execute(\"CREATE INDEX idx_requests_perf ON requests(executor_id, status_id, due_date)\")
    conn.commit(); cursor.execute(\"ANALYZE\"); conn.commit()

    print(\"--- Замер С индексом ---\")
    start = time.perf_counter()
    cursor.execute(query); cursor.fetchall()
    time_after = time.perf_counter() - start
    print(f\"Время: {time_after:.6f} сек.\")
    print(f\"Ускорение: {time_before / time_after:.2f} раз.\")
    conn.close()

if __name__ == \"__main__\": benchmark()
   