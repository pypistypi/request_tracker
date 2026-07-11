from datetime import date
from app.domain.request import Request
from app.domain.status import RequestStatus, StatusTransitionRules
from app.domain.employee import Employee
from app.repositories.request_repository import RequestRepository
from app.repositories.employee_repository import EmployeeRepository

class RequestService:
    def __init__(self):
        self.request_repo = RequestRepository()
        self.employee_repo = EmployeeRepository()
        self.request_repo.initialize_statuses_and_transitions() # Ensure statuses and transitions are in DB

    def create_request(self, number: str, author_id: int, executor_id: int, description: str, due_date: date) -> Request:
        author = self.employee_repo.get_by_id(author_id)
        executor = self.employee_repo.get_by_id(executor_id)
        if not author or not executor:
            raise ValueError("Автор или исполнитель не найдены.")
        
        new_status_id = self.request_repo.get_status_id_by_code(RequestStatus.NEW.code)
        if new_status_id is None:
            raise ValueError("Статус 'Новая' не найден в базе данных.")

        request_id = self.request_repo.add(number, author_id, executor_id, description, due_date, new_status_id)
        return self.request_repo.get_by_id(request_id)

    def change_status(self, request_id: int, new_status_code: str) -> Request:
        request = self.request_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка с ID {request_id} не найдена.")

        new_status = RequestStatus.from_code(new_status_code)
        
        # Use domain logic for status transition validation
        if not StatusTransitionRules.is_allowed(request.status, new_status):
            raise ValueError(f"Недопустимый переход статуса из {request.status.display_name} в {new_status.display_name}")

        new_status_id = self.request_repo.get_status_id_by_code(new_status_code)
        if new_status_id is None:
            raise ValueError(f"Статус '{new_status_code}' не найден в базе данных.")

        self.request_repo.update_status(request_id, new_status_id)
        return self.request_repo.get_by_id(request_id)

    def reassign_request(self, request_id: int, new_executor_id: int) -> Request:
        request = self.request_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка с ID {request_id} не найдена.")
        
        new_executor = self.employee_repo.get_by_id(new_executor_id)
        if not new_executor:
            raise ValueError(f"Новый исполнитель с ID {new_executor_id} не найден.")

        # Use domain logic for reassign validation
        request.reassign(new_executor) # This will raise ValueError if status is DONE

        self.request_repo.update_executor(request_id, new_executor_id)
        return self.request_repo.get_by_id(request_id)

    def list_requests(
        self, 
        status_code: str | None = None, 
        executor_id: int | None = None, 
        department_id: int | None = None, 
        only_overdue: bool = False
    ) -> list[Request]:
        status_id = None
        if status_code:
            status_id = self.request_repo.get_status_id_by_code(status_code)
            if status_id is None:
                raise ValueError(f"Статус '{status_code}' не найден.")

        return self.request_repo.list_requests(status_id, executor_id, department_id, only_overdue)

    def get_request_by_id(self, request_id: int) -> Request | None:
        return self.request_repo.get_by_id(request_id)

    def get_all_employees(self) -> list[Employee]:
        return self.employee_repo.get_all()

    def get_all_departments(self) -> list[Department]:
        return self.employee_repo.get_all_departments()

    def get_all_statuses(self) -> list[tuple[int, str, str]]:
        return self.request_repo.get_all_statuses()
