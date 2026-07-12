import os
from datetime import datetime
from app.services.request_service import RequestService
from app.services.report_service import ReportService
from app.domain.status import RequestStatus

class CLIMenu:
    def __init__(self):
        self.request_service = RequestService()
        self.report_service = ReportService()

    def _clear_screen(self):
        os.system(\"cls\" if os.name == \"nt\" else \"clear\")

    def _pause(self):
        input(\"\\nНажмите Enter для продолжения...\")

    def _get_int_input(self, prompt):
        val = input(prompt)
        if not val: return None
        try: return int(val)
        except ValueError:
            print(\"Ошибка: Введите число.\")
            return self._get_int_input(prompt)

    def _display_employees(self):
        employees = self.request_service.get_all_employees()
        print(\"\\n--- Список сотрудников ---\")
        for emp in employees:
            print(f\"ID: {emp.id}, {emp.full_name} ({emp.department.name}, {emp.position.name})\")

    def _display_requests(self, requests):
        if not requests: print(\"Заявки не найдены.\"); return
        print(\"\\n--- Список заявок ---\")
        for r in requests:
            print(f\"ID: {r.id}, №: {r.number}, Статус: {r.status.display_name}, Исполнитель: {r.executor.full_name}, Срок: {r.due_date}\")

    def manage_requests(self):
        while True:
            self._clear_screen()
            print(\"\\n--- Управление заявками ---\\n1. Создать\\n2. Изменить статус\\n3. Переназначить\\n4. Показать все\\n5. Фильтр\\n0. Назад\")
            c = input(\"Выбор: \")
            if c == \"1\":
                num = input(\"Номер: \"); desc = input(\"Описание: \"); dt_str = input(\"Срок (ГГГГ-ММ-ДД): \")
                try:
                    dt = datetime.strptime(dt_str, \"%Y-%m-%d\").date()
                    self._display_employees()
                    a_id = self._get_int_input(\"ID автора: \")
                    e_id = self._get_int_input(\"ID исполнителя: \")
                    req = self.request_service.create_request(num, a_id, e_id, desc, dt)
                    print(f\"Создана заявка {req.number}\")
                except Exception as e: print(f\"Ошибка: {e}\")
            elif c == \"2\":
                rid = self._get_int_input(\"ID заявки: \")
                print(\"NEW, IN_PROGRESS, DONE\")
                code = input(\"Новый код статуса: \").upper()
                try:
                    req = self.request_service.change_status(rid, code)
                    print(f\"Статус изменен на {req.status.display_name}\")
                except Exception as e: print(f\"Ошибка: {e}\")
            elif c == \"3\":
                rid = self._get_int_input(\"ID заявки: \")
                self._display_employees()
                eid = self._get_int_input(\"ID нового исполнителя: \")
                try:
                    req = self.request_service.reassign_request(rid, eid)
                    print(f\"Исполнитель изменен на {req.executor.full_name}\")
                except Exception as e: print(f\"Ошибка: {e}\")
            elif c == \"4\": self._display_requests(self.request_service.list_requests())
            elif c == \"5\":
                s = input(\"Статус (или Enter): \").upper() or None
                eid = self._get_int_input(\"ID исполнителя (или Enter): \")
                did = self._get_int_input(\"ID отдела (или Enter): \")
                ov = input(\"Только просроченные? (да/нет): \").lower() == \"да\"
                self._display_requests(self.request_service.list_requests(s, eid, did, ov))
            elif c == \"0\": break
            self._pause()

    def run(self):
        while True:
            self._clear_screen()
            print(\"\\n--- Меню ---\\n1. Сотрудники\\n2. Заявки\\n3. Отчеты\\n0. Выход\")
            c = input(\"Выбор: \")
            if c == \"1\": self.manage_employees()
            elif c == \"2\": self.manage_requests()
            elif c == \"3\": self.view_reports()
            elif c == \"0\": break
            
    # Методы manage_employees и view_reports аналогичны по структуре с обработкой ошибок
