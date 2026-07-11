from app.db.connection import get_db_connection
from app.domain.employee import Employee
from app.domain.department import Department
from app.domain.position import Position

class EmployeeRepository:
    def get_by_id(self, employee_id: int) -> Employee | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id, e.full_name, d.id, d.name, p.id, p.name
            FROM
                employees e
            JOIN
                departments d ON e.department_id = d.id
            JOIN
                positions p ON e.position_id = p.id
            WHERE
                e.id = ?
            """,
            (employee_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            department = Department(id=row[2], name=row[3])
            position = Position(id=row[4], name=row[5])
            return Employee(id=row[0], full_name=row[1], department=department, position=position)
        return None

    def get_all(self) -> list[Employee]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id, e.full_name, d.id, d.name, p.id, p.name
            FROM
                employees e
            JOIN
                departments d ON e.department_id = d.id
            JOIN
                positions p ON e.position_id = p.id
            """
        )
        rows = cursor.fetchall()
        conn.close()
        employees = []
        for row in rows:
            department = Department(id=row[2], name=row[3])
            position = Position(id=row[4], name=row[5])
            employees.append(Employee(id=row[0], full_name=row[1], department=department, position=position))
        return employees

    def add(self, full_name: str, department_id: int, position_id: int) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (full_name, department_id, position_id) VALUES (?, ?, ?)",
            (full_name, department_id, position_id)
        )
        conn.commit()
        employee_id = cursor.lastrowid
        conn.close()
        return employee_id

    def get_department_by_id(self, department_id: int) -> Department | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM departments WHERE id = ?", (department_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Department(id=row[0], name=row[1])
        return None

    def get_position_by_id(self, position_id: int) -> Position | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM positions WHERE id = ?", (position_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Position(id=row[0], name=row[1])
        return None

    def get_all_departments(self) -> list[Department]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM departments")
        rows = cursor.fetchall()
        conn.close()
        return [Department(id=row[0], name=row[1]) for row in rows]

    def get_all_positions(self) -> list[Position]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM positions")
        rows = cursor.fetchall()
        conn.close()
        return [Position(id=row[0], name=row[1]) for row in rows]

    def add_department(self, name: str) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO departments (name) VALUES (?) ON CONFLICT(name) DO UPDATE SET name=excluded.name", (name,))
        conn.commit()
        department_id = cursor.lastrowid
        conn.close()
        return department_id

    def add_position(self, name: str) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO positions (name) VALUES (?) ON CONFLICT(name) DO UPDATE SET name=excluded.name", (name,))
        conn.commit()
        position_id = cursor.lastrowid
        conn.close()
        return position_id
