import os, subprocess

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QPushButton, QTextEdit, QLabel,
    QDialog, QLineEdit, QFormLayout,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QFont

from .database import init_db, get_api_key, save_api_key
from .widgets.todo_widget import TodoWidget
from .widgets.alarm_dialog import AlarmDialog
from .scheduler import AlarmScheduler
from .api_client import DeepSeekClient


class SettingsDialog(QDialog):
    def __init__(self, api_key="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(420, 180)
        layout = QVBoxLayout(self)

        # DeepSeek API
        form = QFormLayout()
        self.edit_key = QLineEdit(api_key)
        self.edit_key.setPlaceholderText("输入 DeepSeek API Key (用于 AI 处理)")
        self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("DeepSeek Key:", self.edit_key)

        show_btn = QPushButton("显示")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: self.edit_key.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        form.addRow("", show_btn)
        layout.addLayout(form)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_api_key(self):
        return self.edit_key.text().strip()


class AIResultDialog(QDialog):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 处理结果")
        self.setFixedSize(500, 400)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setPlainText(result)
        text.setReadOnly(True)
        layout.addWidget(text)
        btn = QPushButton("关闭")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("待办记事本")
        self.setMinimumSize(680, 520)

        # Restore window geometry
        self.settings = QSettings("TodoNoteApp", "待办记事本")
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(720, 560)

        init_db()

        self.scheduler = AlarmScheduler()
        self.api_client = DeepSeekClient()

        saved_key = get_api_key("deepseek")
        if saved_key:
            self.api_client.set_api_key(saved_key)

        self.statusBar().showMessage("就绪")

        # Setup UI
        self._setup_ui()
        self._setup_menu()

        # Connect signals
        self.scheduler.alarm_triggered.connect(self._on_alarm)
        self.api_client.response_ready.connect(self._on_api_response)
        self.api_client.error_occurred.connect(self._on_api_error)

        self.scheduler.start()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main todo widget
        self.todo_widget = TodoWidget()
        layout.addWidget(self.todo_widget, 1)

        self.statusBar().showMessage("就绪")

    def _setup_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("设置")

        api_action = QAction("API 设置", self)
        api_action.triggered.connect(self._show_settings)
        settings_menu.addAction(api_action)

        ai_action = QAction("AI 助手", self)
        ai_action.triggered.connect(self._show_ai_assistant)
        settings_menu.addAction(ai_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_settings(self):
        dialog = SettingsDialog(self.api_client.api_key, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key = dialog.get_api_key()
            if key:
                self.api_client.set_api_key(key)
                save_api_key("deepseek", key)
                self.statusBar().showMessage("API Key 已设置")
            else:
                self.statusBar().showMessage("API Key 已清空")

    def _show_ai_assistant(self):
        """Open AI assistant panel."""
        if not self.api_client.has_api_key():
            QMessageBox.warning(self, "提示", "请先在 设置 > API 设置 中配置 DeepSeek API Key")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("AI 助手")
        dialog.setFixedSize(500, 450)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("输入想要处理的内容或问题："))

        input_text = QTextEdit()
        input_text.setPlaceholderText("例如：帮我整理一下今天的待办...")
        input_text.setMaximumHeight(100)
        layout.addWidget(input_text)

        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_text.setPlaceholderText("AI 响应将显示在这里...")
        layout.addWidget(output_text, 1)

        btn = QPushButton("🚀 发送")
        btn.clicked.connect(lambda: self._send_ai(input_text.toPlainText(), output_text))
        layout.addWidget(btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _send_ai(self, text, output_widget):
        if not text.strip():
            QMessageBox.warning(self, "提示", "请输入内容")
            return
        output_widget.setPlainText("正在处理...")
        self._ai_output = output_widget
        self.api_client.chat(text)

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "语音待办记事本 v2.0\n\n"
            "功能：\n"
            "- 待办事项管理\n"
            "- 闹钟提醒\n"
            "- AI 处理 (DeepSeek)",
        )

    def _on_alarm(self, todo):
        alert = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "alert.wav")
        if os.path.exists(alert):
            subprocess.Popen(["afplay", alert], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # macOS notification
        content = (todo.get("content") or "").replace('"', '\\"')
        subprocess.Popen(["osascript", "-e",
            f'display notification "{content}" with title "待办提醒" sound name "default"'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dialog = AlarmDialog(todo, self)
        dialog.exec()
        self.todo_widget.refresh()

    def _on_api_response(self, response):
        if hasattr(self, "_ai_output"):
            self._ai_output.setPlainText(response)
            self.statusBar().showMessage("AI 处理完成")

    def _on_api_error(self, error):
        if hasattr(self, "_ai_output"):
            self._ai_output.setPlainText(f"错误: {error}")
            self.statusBar().showMessage("AI 处理失败")

    def closeEvent(self, event):
        self.scheduler.stop()
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
