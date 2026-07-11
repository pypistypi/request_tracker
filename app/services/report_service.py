from app.db.connection import get_db_connection
from app.domain.status import RequestStatus

class ReportService:
    def __init__(self):
        pass

    def count_requests_by_status(self) -> dict[str, int]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                s.name, COUNT(r.id)
            FROM
                requests r
            JOIN
                statuses s ON r.status_id = s.id
            GROUP BY
                s.name
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def count_overdue_requests(self) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get ID for DONE status
        cursor.execute("SELECT id FROM statuses WHERE code = ?", (RequestStatus.DONE.code,))
        done_status_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                COUNT(id)
            FROM
                requests
            WHERE
                due_date < DATE('now') AND status_id != ?
            """,
            (done_status_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def count_completed_by_executor(self) -> dict[str, int]:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get ID for DONE status
        cursor.execute("SELECT id FROM statuses WHERE code = ?", (RequestStatus.DONE.code,))
        done_status_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                e.full_name, COUNT(r.id)
            FROM
                requests r
            JOIN
                employees e ON r.executor_id = e.id
            WHERE
                r.status_id = ?
            GROUP BY
                e.full_name
            ORDER BY
                COUNT(r.id) DESC
            """,
            (done_status_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
