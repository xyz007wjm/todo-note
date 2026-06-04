from PySide6.QtCore import QTimer, QObject, Signal

from .database import get_due_alarms, mark_alarmed


class AlarmScheduler(QObject):
    alarm_triggered = Signal(dict)  # emits todo dict

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_alarms)

    def start(self, interval_ms=1000):
        self.timer.start(interval_ms)

    def stop(self):
        self.timer.stop()

    def check_alarms(self):
        due = get_due_alarms()
        for todo in due:
            mark_alarmed(todo["id"])
            self.alarm_triggered.emit(todo)
