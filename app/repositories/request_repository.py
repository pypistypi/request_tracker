from datetime import datetime, date
from app.db.connection import get_db_connection
from app.domain.request import Request
from app.domain.employee import Employee
from app.domain.department import Department
from app.domain.position import Position
from app.domain.status import RequestStatus
import sqlite3

class RequestRepository:
    def _row_to_request(self, row) -> Request:
        if row is None:
            return None
        
        # Корректный маппинг индексов согласно SELECT запросу
        department_author = Department(id=row[11], name=row[12])
        position_author = Position(id=row[13], name=row[14])
        author = Employee(id=row[9], full_name=row[10], department=department_author, position=position_author)

        department_executor = Department(id=row[17], name=row[18])
        position_executor = Position(id=row[19], name=row[20])
        executor = Employee(id=row[15], full_name=row[16], department=department_executor, position=position_executor)

        status = RequestStatus.from_code(row[7])

        created_at = row[2]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        due_date = row[4]
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)

        return Request(
            id=row[0], number=row[1], created_at=created_at, author=author,
            executor=executor, description=row[3], due_date=due_date, status=status
        )

    def get_by_id(self, request_id: int) -> Request | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(\"\"\"
            SELECT r.id, r.number, r.created_at, r.description, r.due_date, r.status_id,
                   s.id, s.code, s.name,
                   ea.id, ea.full_name, da.id, da.name, pa.id, pa.name,
                   ee.id, ee.full_name, de.id, de.name, pe.id, pe.name
            FROM requests r
            JOIN statuses s ON r.status_id = s.id
            JOIN employees ea ON r.author_id = ea.id
            JOIN departments da ON ea.department_id = da.id
            JOIN positions pa ON ea.position_id = pa.id
            JOIN employees ee ON r.executor_id = ee.id
            JOIN departments de ON ee.department_id = de.id
            JOIN positions pe ON ee.position_id = pe.id
            WHERE r.id = ?
        \"\"\", (request_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_request(row)

    def list_requests(self, status_id=None, executor_id=None, department_id=None, only_overdue=False) -> list[Request]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = \"\"\"
            SELECT r.id, r.number, r.created_at, r.description, r.due_date, r.status_id,
                   s.id, s.code, s.name,
                   ea.id, ea.full_name, da.id, da.name, pa.id, pa.name,
                   ee.id, ee.full_name, de.id, de.name, pe.id, pe.name
            FROM requests r
            JOIN statuses s ON r.status_id = s.id
            JOIN employees ea ON r.author_id = ea.id
            JOIN departments da ON ea.department_id = da.id
            JOIN positions pa ON ea.position_id = pa.id
            JOIN employees ee ON r.executor_id = ee.id
            JOIN departments de ON ee.department_id = de.id
            JOIN positions pe ON ee.position_id = pe.id
            WHERE 1=1
        \"\"\"
        params = []
        if status_id:
            query += \" AND r.status_id = ?\"; params.append(status_id)
        if executor_id:
            query += \" AND r.executor_id = ?\"; params.append(executor_id)
        if department_id:
            query += \" AND ee.department_id = ?\"; params.append(department_id)
        if only_overdue:
            done_id = self.get_status_id_by_code(RequestStatus.DONE.code)
            query += \" AND r.due_date < DATE('now') AND r.status_id != ?\"; params.append(done_id)
        
        query += \" ORDER BY r.created_at DESC\"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_request(row) for row in rows]

    # Остальные методы (add, update_status и т.д.) остаются без изменений
    def add(self, number, author_id, executor_id, description, due_date, status_id):
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute(\"INSERT INTO requests (number, author_id, executor_id, description, due_date, status_id) VALUES (?, ?, ?, ?, ?, ?)\",
                       (number, author_id, executor_id, description, due_date.isoformat(), status_id))
        conn.commit(); rid = cursor.lastrowid; conn.close(); return rid

    def update_status(self, request_id, new_status_id):
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute(\"UPDATE requests SET status_id = ? WHERE id = ?\", (new_status_id, request_id))
        conn.commit(); conn.close()

    def update_executor(self, request_id, new_executor_id):
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute(\"UPDATE requests SET executor_id = ? WHERE id = ?\", (new_executor_id, request_id))
        conn.commit(); conn.close()

    def get_status_id_by_code(self, code):
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute(\"SELECT id FROM statuses WHERE code = ?\", (code,))
        row = cursor.fetchone(); conn.close(); return row[0] if row else None

    def get_all_statuses(self):
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute(\"SELECT id, code, name FROM statuses\")
        rows = cursor.fetchall(); conn.close(); return rows

    def initialize_statuses_and_transitions(self):
        conn = get_db_connection(); cursor = conn.cursor()
        for s in RequestStatus:
            cursor.execute(\"INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)\", (s.code, s.display_name))
        conn.commit()
        s_ids = {s.code: self.get_status_id_by_code(s.code) for s in RequestStatus}
        trans = [(s_ids['NEW'], s_ids['IN_PROGRESS']), (s_ids['IN_PROGRESS'], s_ids['DONE'])]
        for f, t in trans:
            if f and t: cursor.execute(\"INSERT OR IGNORE INTO status_transitions (from_status_id, to_status_id) VALUES (?, ?)\", (f, t))
        conn.commit(); conn.close()
