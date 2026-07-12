import sqlite3
from datetime import datetime, timedelta
import random
import sys
import os

# Добавляем корневую директорию проекта в пути поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from faker import Faker
from app.db.connection import get_db_connection
from app.domain.status import RequestStatus

fake = Faker(\"ru_RU\")
NUM_EMPLOYEES = 1000
NUM_REQUESTS = 1000000

def generate_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Отключаем проверки для ускорения вставки
    cursor.execute(\"PRAGMA synchronous = OFF\")
    cursor.execute(\"PRAGMA journal_mode = MEMORY\")

    print(\"Инициализация статусов...\")
    for s in RequestStatus:
        cursor.execute(\"INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)\", (s.code, s.display_name))
    conn.commit()
    
    status_ids = {s.code: cursor.execute(\"SELECT id FROM statuses WHERE code = ?\", (s.code,)).fetchone()[0] for s in RequestStatus}

    print(\"Генерация отделов и должностей...\")
    depts = [fake.company() for _ in range(50)]
    for d in depts: cursor.execute(\"INSERT OR IGNORE INTO departments (name) VALUES (?)\", (d,))
    
    positions = [fake.job() for _ in range(100)]
    for p in positions: cursor.execute(\"INSERT OR IGNORE INTO positions (name) VALUES (?)\", (p,))
    conn.commit()

    dept_ids = [r[0] for r in cursor.execute(\"SELECT id FROM departments\").fetchall()]
    pos_ids = [r[0] for r in cursor.execute(\"SELECT id FROM positions\").fetchall()]

    print(f\"Генерация {NUM_EMPLOYEES} сотрудников...\")
    employees = [(fake.name(), random.choice(dept_ids), random.choice(pos_ids)) for _ in range(NUM_EMPLOYEES)]
    cursor.executemany(\"INSERT INTO employees (full_name, department_id, position_id) VALUES (?, ?, ?)\", employees)
    conn.commit()
    
    emp_ids = [r[0] for r in cursor.execute(\"SELECT id FROM employees\").fetchall()]

    print(f\"Генерация {NUM_REQUESTS} заявок (это займет время)... \")
    reqs = []
    for i in range(NUM_REQUESTS):
        created = datetime.now() - timedelta(days=random.randint(0, 700))
        due = created.date() + timedelta(days=random.randint(1, 30))
        status = random.choice(list(RequestStatus))
        reqs.append((
            f\"REQ-{i:07d}\", created.isoformat(), random.choice(emp_ids), 
            random.choice(emp_ids), fake.sentence(), due.isoformat(), status_ids[status.code]
        ))
        if len(reqs) >= 10000: # Вставляем пачками по 10к для экономии памяти
            cursor.executemany(\"INSERT INTO requests (number, created_at, author_id, executor_id, description, due_date, status_id) VALUES (?,?,?,?,?,?,?)\", reqs)
            reqs = []
    
    if reqs: cursor.executemany(\"INSERT INTO requests (number, created_at, author_id, executor_id, description, due_date, status_id) VALUES (?,?,?,?,?,?,?)\", reqs)
    
    conn.commit()
    conn.close()
    print(\"Готово!\")

if __name__ == \"__main__\":
    generate_data()
