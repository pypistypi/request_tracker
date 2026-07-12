import sqlite3
import time
from datetime import date
from app.db.connection import get_db_connection
from app.domain.status import RequestStatus
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def benchmark_query():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure statuses are in DB and get IN_PROGRESS status_id
    cursor.execute("INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)", (RequestStatus.NEW.code, RequestStatus.NEW.display_name))
    cursor.execute("INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)", (RequestStatus.IN_PROGRESS.code, RequestStatus.IN_PROGRESS.display_name))
    cursor.execute("INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)", (RequestStatus.DONE.code, RequestStatus.DONE.display_name))
    conn.commit()
    
    cursor.execute("SELECT id FROM statuses WHERE code = ?", (RequestStatus.IN_PROGRESS.code,))
    in_progress_status_id = cursor.fetchone()[0]

    # Find an executor with requests in IN_PROGRESS status
    cursor.execute(
        "SELECT executor_id FROM requests WHERE status_id = ? GROUP BY executor_id LIMIT 1",
        (in_progress_status_id,)
    )
    result = cursor.fetchone()
    if not result:
        print("Не найден исполнитель с заявками в статусе 'В работе'. Пожалуйста, сгенерируйте данные сначала.")
        conn.close()
        return
    
    target_executor_id = result[0]

    print(f"Целевой исполнитель для бенчмарка: ID {target_executor_id}")

    query = """
    SELECT
        r.id, r.number, r.created_at, r.description, r.due_date, s.name, e.full_name
    FROM
        requests r
    JOIN
        statuses s ON r.status_id = s.id
    JOIN
        employees e ON r.executor_id = e.id
    WHERE
        r.executor_id = ? AND r.status_id = ? AND r.due_date < DATE('now')
    ORDER BY
        r.due_date ASC;
    """
    params = (target_executor_id, in_progress_status_id)

    print("\n--- План запроса ДО оптимизации ---")
    cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
    print("\n".join([str(row) for row in cursor.fetchall()]))

    print("\n--- Замер времени ДО оптимизации ---")
    start_time = time.perf_counter()
    cursor.execute(query, params)
    rows_before = cursor.fetchall()
    end_time = time.perf_counter()
    time_before = end_time - start_time
    print(f"Время выполнения: {time_before:.6f} секунд. Найдено записей: {len(rows_before)}")

    print("\n--- Создание составного индекса ---")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_executor_status_due_date ON requests(executor_id, status_id, due_date);")
    conn.commit()
    print("Индекс создан.")

    print("\n--- Обновление статистики (ANALYZE) ---")
    cursor.execute("ANALYZE;")
    conn.commit()
    print("Статистика обновлена.")

    print("\n--- План запроса ПОСЛЕ оптимизации ---")
    cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
    print("\n".join([str(row) for row in cursor.fetchall()]))

    print("\n--- Замер времени ПОСЛЕ оптимизации ---")
    start_time = time.perf_counter()
    cursor.execute(query, params)
    rows_after = cursor.fetchall()
    end_time = time.perf_counter()
    time_after = end_time - start_time
    print(f"Время выполнения: {time_after:.6f} секунд. Найдено записей: {len(rows_after)}")

    print("\n--- Результаты ---")
    print(f"Время до оптимизации: {time_before:.6f} с")
    print(f"Время после оптимизации: {time_after:.6f} с")
    if time_after > 0:
        print(f"Ускорение в: {time_before / time_after:.2f} раз")
    else:
        print("Время после оптимизации слишком мало для расчета ускорения.")

    conn.close()

if __name__ == "__main__":
    benchmark_query()
