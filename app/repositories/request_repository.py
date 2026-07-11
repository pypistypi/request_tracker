from datetime import datetime, date
from app.db.connection import get_db_connection
from app.domain.request import Request
from app.domain.employee import Employee
from app.domain.department import Department
from app.domain.position import Position
from app.domain.status import RequestStatus

class RequestRepository:
    def _row_to_request(self, row) -> Request:
        if row is None:
            return None
        
        department_author = Department(id=row[10], name=row[11])
        position_author = Position(id=row[12], name=row[13])
        author = Employee(id=row[8], full_name=row[9], department=department_author, position=position_author)

        department_executor = Department(id=row[16], name=row[17])
        position_executor = Position(id=row[18], name=row[19])
        executor = Employee(id=row[14], full_name=row[15], department=department_executor, position=position_executor)

        status = RequestStatus.from_code(row[21])

        return Request(
            id=row[0],
            number=row[1],
            created_at=datetime.fromisoformat(row[2]),
            author=author,
            executor=executor,
            description=row[3],
            due_date=date.fromisoformat(row[4]),
            status=status
        )

    def get_by_id(self, request_id: int) -> Request | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                r.id, r.number, r.created_at, r.description, r.due_date, r.status_id,
                s.id, s.code, s.name, -- Status info
                ea.id, ea.full_name, da.id, da.name, pa.id, pa.name, -- Author info
                ee.id, ee.full_name, de.id, de.name, pe.id, pe.name  -- Executor info
            FROM
                requests r
            JOIN
                statuses s ON r.status_id = s.id
            JOIN
                employees ea ON r.author_id = ea.id
            JOIN
                departments da ON ea.department_id = da.id
            JOIN
                positions pa ON ea.position_id = pa.id
            JOIN
                employees ee ON r.executor_id = ee.id
            JOIN
                departments de ON ee.department_id = de.id
            JOIN
                positions pe ON ee.position_id = pe.id
            WHERE
                r.id = ?
            """,
            (request_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return self._row_to_request(row)

    def add(self, number: str, author_id: int, executor_id: int, description: str, due_date: date, status_id: int) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO requests (number, author_id, executor_id, description, due_date, status_id) VALUES (?, ?, ?, ?, ?, ?)",
            (number, author_id, executor_id, description, due_date.isoformat(), status_id)
        )
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        return request_id

    def update_status(self, request_id: int, new_status_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET status_id = ? WHERE id = ?",
            (new_status_id, request_id)
        )
        conn.commit()
        conn.close()

    def update_executor(self, request_id: int, new_executor_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET executor_id = ? WHERE id = ?",
            (new_executor_id, request_id)
        )
        conn.commit()
        conn.close()

    def get_all_statuses(self) -> list[tuple[int, str, str]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, code, name FROM statuses")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_status_id_by_code(self, code: str) -> int | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM statuses WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def list_requests(
        self, 
        status_id: int | None = None, 
        executor_id: int | None = None, 
        department_id: int | None = None, 
        only_overdue: bool = False
    ) -> list[Request]:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                r.id, r.number, r.created_at, r.description, r.due_date, r.status_id,
                s.id, s.code, s.name, -- Status info
                ea.id, ea.full_name, da.id, da.name, pa.id, pa.name, -- Author info
                ee.id, ee.full_name, de.id, de.name, pe.id, pe.name  -- Executor info
            FROM
                requests r
            JOIN
                statuses s ON r.status_id = s.id
            JOIN
                employees ea ON r.author_id = ea.id
            JOIN
                departments da ON ea.department_id = da.id
            JOIN
                positions pa ON ea.position_id = pa.id
            JOIN
                employees ee ON r.executor_id = ee.id
            JOIN
                departments de ON ee.department_id = de.id
            JOIN
                positions pe ON ee.position_id = pe.id
            WHERE 1=1
        """
        params = []

        if status_id:
            query += " AND r.status_id = ?"
            params.append(status_id)
        if executor_id:
            query += " AND r.executor_id = ?"
            params.append(executor_id)
        if department_id:
            query += " AND ee.department_id = ?"
            params.append(department_id)
        if only_overdue:
            # Get ID for 'DONE' status
            done_status_id = self.get_status_id_by_code(RequestStatus.DONE.code)
            if done_status_id is None:
                raise ValueError("Status 'DONE' not found in database.")
            query += " AND r.due_date < DATE('now') AND r.status_id != ?"
            params.append(done_status_id)
        
        query += " ORDER BY r.created_at DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_request(row) for row in rows]

    def get_status_transitions(self) -> list[tuple[int, int]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT from_status_id, to_status_id FROM status_transitions")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_status_transition(self, from_status_id: int, to_status_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO status_transitions (from_status_id, to_status_id) VALUES (?, ?)",
                (from_status_id, to_status_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Transition already exists, or invalid FK
            pass
        finally:
            conn.close()

    def initialize_statuses_and_transitions(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert statuses if they don't exist
        for status_enum in RequestStatus:
            cursor.execute(
                "INSERT OR IGNORE INTO statuses (code, name) VALUES (?, ?)",
                (status_enum.code, status_enum.display_name)
            )
        conn.commit()

        # Get status IDs
        status_ids = {status.code: self.get_status_id_by_code(status.code) for status in RequestStatus}

        # Insert allowed transitions
        if status_ids[RequestStatus.NEW.code] and status_ids[RequestStatus.IN_PROGRESS.code]:
            self.add_status_transition(status_ids[RequestStatus.NEW.code], status_ids[RequestStatus.IN_PROGRESS.code])
        if status_ids[RequestStatus.IN_PROGRESS.code] and status_ids[RequestStatus.DONE.code]:
            self.add_status_transition(status_ids[RequestStatus.IN_PROGRESS.code], status_ids[RequestStatus.DONE.code])

        conn.close()
