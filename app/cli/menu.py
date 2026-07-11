import os
from datetime import datetime, date
from app.services.request_service import RequestService
from app.services.report_service import ReportService
from app.domain.status import RequestStatus

class CLIMenu:
    def __init__(self):
        self.request_service = RequestService()
        self.report_service = ReportService()

    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _pause(self):
        input("Нажмите Enter для продолжения...")

    def _display_employees(self):
        employees = self.request_service.get_all_employees()
        if not employees:
            print("Сотрудники не найдены.")
            return
        print("\n--- Список сотрудников ---")
        for emp in employees:
            print(f"ID: {emp.id}, ФИО: {emp.full_name}, Отдел: {emp.department.name}, Должность: {emp.position.name}")

    def _display_requests(self, requests):
        if not requests:
            print("Заявки не найдены.")
            return
        print("\n--- Список заявок ---")
        for req in requests:
            print(f"ID: {req.id}, Номер: {req.number}, Статус: {req.status.display_name}, Исполнитель: {req.executor.full_name}, Срок: {req.due_date.isoformat()}")

    def manage_employees(self):
        while True:
            self._clear_screen()
            print("\n--- Управление сотрудниками ---")
            print("1. Показать всех сотрудников")
            print("2. Добавить сотрудника")
            print("0. Назад")
            choice = input("Выберите действие: ")

            if choice == "1":
                self._display_employees()
            elif choice == "2":
                full_name = input("Введите ФИО сотрудника: ")
                departments = self.request_service.get_all_departments()
                if not departments:
                    print("Нет доступных отделов. Добавьте отдел сначала.")
                    self._pause()
                    continue
                print("Доступные отделы:")
                for dept in departments:
                    print(f"ID: {dept.id}, Название: {dept.name}")
                dept_id = int(input("Введите ID отдела: "))
                
                positions = self.request_service.employee_repo.get_all_positions()
                if not positions:
                    print("Нет доступных должностей. Добавьте должность сначала.")
                    self._pause()
                    continue
                print("Доступные должности:")
                for pos in positions:
                    print(f"ID: {pos.id}, Название: {pos.name}")
                pos_id = int(input("Введите ID должности: "))

                try:
                    employee_id = self.request_service.employee_repo.add(full_name, dept_id, pos_id)
                    print(f"Сотрудник {full_name} добавлен с ID: {employee_id}")
                except Exception as e:
                    print(f"Ошибка при добавлении сотрудника: {e}")
            elif choice == "0":
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            self._pause()

    def manage_requests(self):
        while True:
            self._clear_screen()
            print("\n--- Управление заявками ---")
            print("1. Создать заявку")
            print("2. Изменить статус заявки")
            print("3. Переназначить исполнителя заявки")
            print("4. Показать все заявки")
            print("5. Фильтровать заявки")
            print("0. Назад")
            choice = input("Выберите действие: ")

            if choice == "1":
                number = input("Введите номер заявки: ")
                description = input("Введите описание заявки: ")
                due_date_str = input("Введите срок выполнения (ГГГГ-ММ-ДД): ")
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print("Неверный формат даты.")
                    self._pause()
                    continue
                
                self._display_employees()
                author_id = int(input("Введите ID автора: "))
                executor_id = int(input("Введите ID исполнителя: "))

                try:
                    req = self.request_service.create_request(number, author_id, executor_id, description, due_date)
                    print(f"Заявка {req.number} создана.")
                except Exception as e:
                    print(f"Ошибка при создании заявки: {e}")

            elif choice == "2":
                request_id = int(input("Введите ID заявки: "))
                statuses = self.request_service.get_all_statuses()
                print("Доступные статусы:")
                for s_id, s_code, s_name in statuses:
                    print(f"ID: {s_id}, Код: {s_code}, Название: {s_name}")
                new_status_code = input("Введите код нового статуса (NEW, IN_PROGRESS, DONE): ").upper()
                try:
                    req = self.request_service.change_status(request_id, new_status_code)
                    print(f"Статус заявки {req.number} изменен на {req.status.display_name}.")
                except ValueError as e:
                    print(f"Ошибка: {e}")
                except Exception as e:
                    print(f"Неизвестная ошибка при изменении статуса: {e}")

            elif choice == "3":
                request_id = int(input("Введите ID заявки: "))
                self._display_employees()
                new_executor_id = int(input("Введите ID нового исполнителя: "))
                try:
                    req = self.request_service.reassign_request(request_id, new_executor_id)
                    print(f"Исполнитель заявки {req.number} переназначен на {req.executor.full_name}.")
                except ValueError as e:
                    print(f"Ошибка: {e}")
                except Exception as e:
                    print(f"Неизвестная ошибка при переназначении исполнителя: {e}")

            elif choice == "4":
                requests = self.request_service.list_requests()
                self._display_requests(requests)

            elif choice == "5":
                status_code = input("Фильтр по статусу (NEW, IN_PROGRESS, DONE, оставить пустым для всех): ").upper()
                executor_id_str = input("Фильтр по ID исполнителя (оставить пустым для всех): ")
                department_id_str = input("Фильтр по ID отдела исполнителя (оставить пустым для всех): ")
                only_overdue_str = input("Только просроченные (да/нет, оставить пустым для всех): ").lower()

                executor_id = int(executor_id_str) if executor_id_str else None
                department_id = int(department_id_str) if department_id_str else None
                only_overdue = only_overdue_str == "да"

                try:
                    requests = self.request_service.list_requests(
                        status_code=status_code if status_code else None,
                        executor_id=executor_id,
                        department_id=department_id,
                        only_overdue=only_overdue
                    )
                    self._display_requests(requests)
                except ValueError as e:
                    print(f"Ошибка фильтрации: {e}")
                except Exception as e:
                    print(f"Неизвестная ошибка при фильтрации: {e}")

            elif choice == "0":
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            self._pause()

    def view_reports(self):
        while True:
            self._clear_screen()
            print("\n--- Отчеты ---")
            print("1. Количество заявок по статусам")
            print("2. Количество просроченных заявок")
            print("3. Количество выполненных заявок по исполнителям")
            print("0. Назад")
            choice = input("Выберите действие: ")

            if choice == "1":
                report = self.report_service.count_requests_by_status()
                print("\n--- Количество заявок по статусам ---")
                for status, count in report.items():
                    print(f"{status}: {count}")
            elif choice == "2":
                count = self.report_service.count_overdue_requests()
                print("\n--- Количество просроченных заявок ---")
                print(f"Всего просроченных заявок: {count}")
            elif choice == "3":
                report = self.report_service.count_completed_by_executor()
                print("\n--- Количество выполненных заявок по исполнителям ---")
                for executor, count in report.items():
                    print(f"{executor}: {count}")
            elif choice == "0":
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            self._pause()

    def run(self):
        while True:
            self._clear_screen()
            print("\n--- Система учёта заявок сотрудников ---")
            print("1. Управление сотрудниками")
            print("2. Управление заявками")
            print("3. Просмотр отчетов")
            print("0. Выход")
            choice = input("Выберите действие: ")

            if choice == "1":
                self.manage_employees()
            elif choice == "2":
                self.manage_requests()
            elif choice == "3":
                self.view_reports()
            elif choice == "0":
                print("Выход из системы. До свидания!")
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            self._pause()

if __name__ == "__main__":
    menu = CLIMenu()
    menu.run()
