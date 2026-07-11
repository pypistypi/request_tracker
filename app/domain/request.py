from datetime import datetime, date
from app.domain.employee import Employee
from app.domain.status import RequestStatus, StatusTransitionRules

class Request:
    def __init__(
        self, 
        id: int, 
        number: str, 
        created_at: datetime, 
        author: Employee, 
        executor: Employee, 
        description: str, 
        due_date: date, 
        status: RequestStatus
    ):
        self.id = id
        self.number = number
        self.created_at = created_at
        self.author = author
        self.executor = executor
        self.description = description
        self.due_date = due_date
        self.status = status

    def change_status(self, new_status: RequestStatus):
        if not StatusTransitionRules.is_allowed(self.status, new_status):
            raise ValueError(f"Недопустимый переход статуса из {self.status.display_name} в {new_status.display_name}")
        self.status = new_status

    def reassign(self, new_executor: Employee):
        if self.status == RequestStatus.DONE:
            raise ValueError("Невозможно переназначить исполнителя для выполненной заявки.")
        self.executor = new_executor

    def is_overdue(self) -> bool:
        return self.due_date < date.today() and self.status != RequestStatus.DONE

    def __repr__(self):
        return (
            f"Request(id={self.id}, number=\"{self.number}\", status={self.status.display_name}, "
            f"executor={self.executor.full_name}, due_date={self.due_date})"
        )
