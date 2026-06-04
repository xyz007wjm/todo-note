from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AlarmDialog(QDialog):
    def __init__(self, todo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ 提醒")
        self.setFixedSize(400, 200)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog
        )
        self._setup_ui(todo)

    def _setup_ui(self, todo):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⏰")
        icon.setFont(QFont("", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(f"提醒: {todo['content']}")
        msg.setFont(QFont("", 14))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        btn = QPushButton("知道了")
        btn.setFixedWidth(120)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
