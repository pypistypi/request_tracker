from enum import Enum

class RequestStatus(Enum):
    NEW = ("NEW", "Новая")
    IN_PROGRESS = ("IN_PROGRESS", "В работе")
    DONE = ("DONE", "Выполнена")

    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name

    @staticmethod
    def from_code(code: str):
        for status in RequestStatus:
            if status.code == code:
                return status
        raise ValueError(f"Unknown status code: {code}")

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f"<RequestStatus.{self.name}>"


class StatusTransitionRules:
    _transitions = {
        RequestStatus.NEW: [RequestStatus.IN_PROGRESS],
        RequestStatus.IN_PROGRESS: [RequestStatus.DONE],
        RequestStatus.DONE: [], # No transitions from DONE
    }

    @staticmethod
    def is_allowed(current_status: RequestStatus, target_status: RequestStatus) -> bool:
        if current_status == target_status:
            return False # No self-transitions
        return target_status in StatusTransitionRules._transitions.get(current_status, [])
