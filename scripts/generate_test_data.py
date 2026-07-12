import sqlite3
from datetime import datetime, timedelta, date
import random
from faker import Faker
from app.db.connection import get_db_connection
from app.domain.status import RequestStatus
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


fake = Faker("ru_RU")

NUM_EMPLOYEES = 1000
NUM_REQUESTS = 1000000

def generate_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data (optional, for fresh runs)
    cursor.execute("DELETE FROM requests")
    cursor.execute("DELETE FROM employees")
    cursor.execute("DELETE FROM departments")
    cursor.execute("DELETE FROM positions")
    cursor.execute("DELETE FROM status_transitions")
    cursor.execute("DELETE FROM statuses")
    conn.commit()

    # Initialize statuses and transitions
    for status_enum in RequestStatus:
        cursor.execute(
            "INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)",
            (status_enum.code, status_enum.display_name)
        )
    conn.commit()

    # Get status IDs
    status_ids = {status.code: cursor.execute("SELECT id FROM statuses WHERE code = ?", (status.code,)).fetchone()[0] for status in RequestStatus}

    # Insert allowed transitions
    cursor.execute(
        "INSERT OR IGNORE INTO status_transitions (from_status_id, to_status_id) VALUES (?, ?)",
        (status_ids[RequestStatus.NEW.code], status_ids[RequestStatus.IN_PROGRESS.code])
    )
    cursor.execute(
        "INSERT OR IGNORE INTO status_transitions (from_status_id, to_status_id) VALUES (?, ?)",
        (status_ids[RequestStatus.IN_PROGRESS.code], status_ids[RequestStatus.DONE.code])
    )
    conn.commit()

    print("Generating departments...")
    departments = []
    for _ in range(50):
        dept_name = fake.company() + " " + fake.word()
        cursor.execute("INSERT INTO departments (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (dept_name,))
        departments.append(dept_name)
    conn.commit()
    departments_db = cursor.execute("SELECT id, name FROM departments").fetchall()
    department_ids = [d[0] for d in departments_db]

    print("Generating positions...")
    positions = []
    for _ in range(100):
        pos_name = fake.job()
        cursor.execute("INSERT INTO positions (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (pos_name,))
        positions.append(pos_name)
    conn.commit()
    positions_db = cursor.execute("SELECT id, name FROM positions").fetchall()
    position_ids = [p[0] for p in positions_db]

    print(f"Generating {NUM_EMPLOYEES} employees...")
    employees_data = []
    for i in range(NUM_EMPLOYEES):
        full_name = fake.name()
        department_id = random.choice(department_ids)
        position_id = random.choice(position_ids)
        employees_data.append((full_name, department_id, position_id))
    cursor.executemany("INSERT INTO employees (full_name, department_id, position_id) VALUES (?, ?, ?)", employees_data)
    conn.commit()
    employee_ids = [e[0] for e in cursor.execute("SELECT id FROM employees").fetchall()]

    print(f"Generating {NUM_REQUESTS} requests...")
    requests_data = []
    for i in range(NUM_REQUESTS):
        number = f"REQ-{i+1:07d}"
        created_at = datetime.now() - timedelta(days=random.randint(0, 365*2))
        author_id = random.choice(employee_ids)
        executor_id = random.choice(employee_ids)
        description = fake.sentence()
        due_date = created_at.date() + timedelta(days=random.randint(1, 60))
        
        # Randomly assign status, ensuring some are overdue and in progress
        status_choice = random.choices([RequestStatus.NEW, RequestStatus.IN_PROGRESS, RequestStatus.DONE], weights=[0.2, 0.5, 0.3], k=1)[0]
        status_id = status_ids[status_choice.code]

        requests_data.append((number, created_at.isoformat(), author_id, executor_id, description, due_date.isoformat(), status_id))
    
    cursor.executemany("INSERT INTO requests (number, created_at, author_id, executor_id, description, due_date, status_id) VALUES (?, ?, ?, ?, ?, ?, ?)", requests_data)
    conn.commit()

    conn.close()
    print("Data generation complete.")

if __name__ == "__main__":
    generate_data()
