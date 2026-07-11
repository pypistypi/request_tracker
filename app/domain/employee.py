from app.domain.department import Department
from app.domain.position import Position

class Employee:
    def __init__(self, id: int, full_name: str, department: Department, position: Position):
        self.id = id
        self.full_name = full_name
        self.department = department
        self.position = position

    def __repr__(self):
        return f"Employee(id={self.id}, full_name=\"{self.full_name}\", department={self.department.name}, position={self.position.name})"
