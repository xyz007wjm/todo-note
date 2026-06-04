from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QTimeEdit, QMessageBox, QFrame, QCheckBox,
    QDialog, QCalendarWidget,
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QFont, QPalette

from ..database import (
    add_task, get_all_tasks, toggle_task, delete_task, update_task,
)

# Detect dark mode from system palette
def _is_dark_mode():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        bg = app.palette().color(QPalette.ColorRole.Window)
        return bg.lightness() < 128
    return False

DARK = _is_dark_mode()

ACCENT = "#1677FF"
LIGHT_BG = "#2A2A2A" if DARK else "#F5F5F5"
CARD_BG = "#1E1E1E" if DARK else "#FFFFFF"
BORDER = "#333333" if DARK else "#E8E8E8"
TEXT_PRIMARY = "#FFFFFF" if DARK else "#333333"
TEXT_SECONDARY = "#AAAAAA" if DARK else "#999999"
DONE_COLOR = "#52C41A"


class TaskCard(QFrame):
    toggled = Signal(int)
    clicked = Signal(int)
    deleted = Signal(int)

    def __init__(self, task_data, index=0):
        super().__init__()
        self.task = task_data
        self.index = index

        # Check if overdue
        is_overdue = False
        if not task_data.get("is_completed") and task_data.get("due_date"):
            try:
                from datetime import date
                d = date.fromisoformat(task_data["due_date"])
                is_overdue = d < date.today()
            except:
                pass

        border_color = "#FF4D4F" if is_overdue else BORDER
        hover_color = "#FF4D4F" if is_overdue else ACCENT

        self.setStyleSheet(f"""
            TaskCard {{
                background: {CARD_BG};
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
            TaskCard:hover {{
                border: 1px solid {hover_color};
            }}
        """)
        self.setMinimumHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def mousePressEvent(self, event):
        self.clicked.emit(self.task["id"])
        super().mousePressEvent(event)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Number indicator (only for incomplete tasks in "all" view)
        if not self.task["is_completed"] and self.index > 0:
            num = QLabel(str(self.index))
            num.setFixedSize(22, 22)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:11px;border:none;font-weight:bold;")
            layout.addWidget(num)

        cb = QCheckBox()
        cb.setChecked(bool(self.task["is_completed"]))
        cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border-radius: 10px;
                border: 2px solid {DONE_COLOR if self.task['is_completed'] else BORDER};
                background: {DONE_COLOR if self.task['is_completed'] else CARD_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {DONE_COLOR};
                border: 2px solid {DONE_COLOR};
            }}
        """)
        cb.stateChanged.connect(lambda: self.toggled.emit(self.task["id"]))
        layout.addWidget(cb)

        # Content
        cl = QVBoxLayout()
        cl.setSpacing(2)

        display_text = self.task["content"] or "(无内容)"
        if self.task["is_completed"]:
            display_text = f"<s>{display_text}</s>"
        lbl = QLabel(display_text)
        lbl.setWordWrap(True)
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl.setStyleSheet(f"color:{TEXT_PRIMARY};font-size:14px;border:none;")
        lbl.mousePressEvent = lambda e: self.clicked.emit(self.task["id"])
        cl.addWidget(lbl)

        meta_parts = []
        if self.task.get("due_date"):
            meta_parts.append(f"📅 {self.task['due_date']}")
        if self.task.get("alarm_time"):
            meta_parts.append(f"⏰ {self.task['alarm_time']}")
        if meta_parts:
            ml = QLabel("  ".join(meta_parts))
            ml.setCursor(Qt.CursorShape.PointingHandCursor)
            ml.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:11px;border:none;")
            ml.mousePressEvent = lambda e: self.clicked.emit(self.task["id"])
            cl.addWidget(ml)

        layout.addLayout(cl, 1)

        # Delete (only for incomplete tasks)
        if not self.task["is_completed"]:
            btn_del = QPushButton("×")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{TEXT_SECONDARY};border:none;font-size:18px;}}QPushButton:hover{{color:#FF4D4F;}}")
            btn_del.clicked.connect(lambda: self.deleted.emit(self.task["id"]))
            layout.addWidget(btn_del)


class TodoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_filter = "all"
        self._editing_id = None
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet(f"background:{CARD_BG};border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 16, 8)

        title = QLabel("待办")
        title.setFont(QFont("", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{TEXT_PRIMARY};border:none;")
        hl.addWidget(title)
        hl.addStretch()

        self.tab_s = f"QPushButton{{background:transparent;color:{TEXT_SECONDARY};border:none;font-size:13px;padding:6px 14px;border-radius:14px;}}QPushButton:hover{{background:{LIGHT_BG};}}"
        self.tab_a = f"QPushButton{{background:{ACCENT};color:white;border:none;font-size:13px;padding:6px 14px;border-radius:14px;}}"

        self.btn_all = QPushButton("全部")
        self.btn_all.setStyleSheet(self.tab_a)
        self.btn_all.clicked.connect(lambda: self._set_filter("all"))
        hl.addWidget(self.btn_all)

        self.btn_today = QPushButton("今天")
        self.btn_today.setStyleSheet(self.tab_s)
        self.btn_today.clicked.connect(lambda: self._set_filter("today"))
        hl.addWidget(self.btn_today)

        self.btn_done = QPushButton("已完成")
        self.btn_done.setStyleSheet(self.tab_s)
        self.btn_done.clicked.connect(lambda: self._set_filter("completed"))
        hl.addWidget(self.btn_done)


        layout.addWidget(header)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet(f"""
            QListWidget {{ background:{LIGHT_BG}; border:none; outline:none; padding:8px; }}
            QListWidget::item {{ background:transparent; border:none; padding:4px 0px; }}
            QScrollBar:vertical {{ width:6px; background:{LIGHT_BG}; }}
            QScrollBar::handle:vertical {{ background:{BORDER}; border-radius:3px; min-height:20px; }}
        """)
        self.task_list.setSpacing(6)
        self.task_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.task_list, 1)

        bottom = QWidget()
        bottom.setStyleSheet(f"background:{CARD_BG};border-top:1px solid {BORDER};")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(12, 8, 12, 8)

        self.edit_input = QLineEdit()
        self.edit_input.setPlaceholderText("输入待办内容...")
        self.edit_input.setStyleSheet(f"QLineEdit{{border:1px solid {BORDER};border-radius:18px;padding:8px 14px;font-size:14px;background:{LIGHT_BG};color:{TEXT_PRIMARY};}}QLineEdit:focus{{border:1px solid {ACCENT};background:{CARD_BG};color:{TEXT_PRIMARY};}}")
        self.edit_input.returnPressed.connect(self._add_task)
        bl.addWidget(self.edit_input, 1)

        self.btn_date = QPushButton("📅")
        self.btn_date.setFixedSize(36, 36)
        self.btn_date.setStyleSheet(f"QPushButton{{background:{LIGHT_BG};border-radius:18px;border:none;font-size:16px;}}QPushButton:hover{{background:{BORDER};}}")
        self.btn_date.clicked.connect(self._pick_date)
        bl.addWidget(self.btn_date)

        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        self.time_picker.setTime(QTime(18, 0))
        self.time_picker.setFixedWidth(80)
        self.time_picker.setStyleSheet(f"QTimeEdit{{border:1px solid {BORDER};border-radius:14px;padding:4px 8px;font-size:13px;background:{LIGHT_BG};color:{TEXT_PRIMARY};}}")
        bl.addWidget(self.time_picker)

        self.btn_add = QPushButton("＋")
        self.btn_add.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;border-radius:18px;border:none;font-size:20px;min-width:36px;min-height:36px;padding:0 8px;}}QPushButton:hover{{background:#4096FF;}}")
        self.btn_add.clicked.connect(self._add_task)
        bl.addWidget(self.btn_add)

        layout.addWidget(bottom)

        # Copyright footer
        footer = QLabel(
            '<span style="color:%s;">软件制作人：jackwang</span> | '
            '<a href="https://wangjinming.com" style="color:%s;text-decoration:none;">wangjinming.com</a> | '
            '<span style="color:%s;">2026</span>'
            % (TEXT_SECONDARY, ACCENT, TEXT_SECONDARY)
        )
        footer.setTextFormat(Qt.TextFormat.RichText)
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"background:{CARD_BG};border:none;padding:4px 0;")
        layout.addWidget(footer)

        self.picked_date = None

    def _set_filter(self, f):
        self.current_filter = f
        for btn, cond in [(self.btn_all, f == "all"), (self.btn_today, f == "today"), (self.btn_done, f == "completed")]:
            btn.setStyleSheet(self.tab_a if cond else self.tab_s)
        self.refresh()

    def _on_item_clicked(self, task_id):
        if task_id:
            self._load_task_for_edit(task_id)

    def refresh(self):
        # Update counts
        from ..database import get_task_counts
        counts = get_task_counts()
        self.btn_all.setText(f"全部")
        self.btn_today.setText(f"今天 ({counts['today']})" if counts['today'] else "今天")
        self.btn_done.setText(f"已完成 ({counts['completed']})" if counts['completed'] else "已完成")

        self.task_list.blockSignals(True)
        self.task_list.clear()
        tasks = get_all_tasks(
            filter_date=self.current_filter if self.current_filter not in ("all", "completed") else None,
            show_completed=(self.current_filter == "completed"),
        )
        if self.current_filter == "completed":
            tasks = [t for t in tasks if t["is_completed"]]
        else:
            tasks = [t for t in tasks if not t["is_completed"]]

        for i, task in enumerate(tasks):
            card = TaskCard(task, index=i+1)
            card.toggled.connect(self._on_toggled)
            card.clicked.connect(self._on_item_clicked)
            card.deleted.connect(self._on_deleted)
            item = QListWidgetItem(self.task_list)
            item.setSizeHint(card.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, task["id"])
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, card)

        if not tasks:
            empty = QLabel("暂无待办事项\n点击底部 ＋ 创建")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{TEXT_SECONDARY};font-size:14px;border:none;padding:40px;")
            item = QListWidgetItem(self.task_list)
            item.setSizeHint(empty.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, 0)
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, empty)
        self.task_list.blockSignals(False)

    def _on_toggled(self, task_id):
        toggle_task(task_id)
        self.refresh()

    def _show_edit_dialog(self, task_id):
        from ..database import get_task, update_task
        task = get_task(task_id)
        if not task:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("编辑待办")
        dialog.setFixedSize(380, 220)
        vl = QVBoxLayout(dialog)

        edit_content = QLineEdit(task["content"])
        edit_content.setStyleSheet(f"QLineEdit{{border:1px solid {BORDER};border-radius:8px;padding:8px;font-size:14px;background:{LIGHT_BG};color:{TEXT_PRIMARY};}}")
        vl.addWidget(QLabel("内容:"))
        vl.addWidget(edit_content)

        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        if task.get("due_date"):
            date_edit.setDate(QDate.fromString(task["due_date"], "yyyy-MM-dd"))
        vl.addWidget(QLabel("日期:"))
        vl.addWidget(date_edit)

        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        if task.get("alarm_time"):
            parts = task["alarm_time"].split(" ")
            if len(parts) >= 2:
                time_edit.setTime(QTime.fromString(parts[1], "HH:mm"))
        vl.addWidget(QLabel("时间:"))
        vl.addWidget(time_edit)

        bl = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;border-radius:6px;padding:6px 20px;}}")
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(f"QPushButton{{background:{LIGHT_BG};color:{TEXT_PRIMARY};border-radius:6px;padding:6px 20px;border:1px solid {BORDER};}}")
        bl.addWidget(btn_cancel)
        bl.addWidget(btn_save)
        vl.addLayout(bl)

        btn_save.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            content = edit_content.text().strip()
            due = date_edit.date().toString("yyyy-MM-dd")
            alarm = f"{due} {time_edit.time().toString('HH:mm')}"
            update_task(task_id, content=content, due_date=due, alarm_time=alarm)
            self.refresh()
        dialog.deleteLater()

    def _on_deleted(self, task_id):
        delete_task(task_id)
        self.refresh()

    def _load_task_for_edit(self, task_id):
        from ..database import get_task
        task = get_task(task_id)
        if not task:
            return
        self._editing_id = task_id
        self.edit_input.setText(task["content"])
        if task.get("due_date"):
            self.picked_date = task["due_date"]
            parts = task.get("alarm_time", "").split(" ")
            time_str = parts[1] if len(parts) >= 2 else "18:00"
            self.time_picker.setTime(QTime.fromString(time_str, "HH:mm"))
            self.edit_input.setPlaceholderText(f"编辑: {task['due_date']}")
        else:
            self.picked_date = None
            self.edit_input.setPlaceholderText("编辑待办...")
        self.btn_add.setText("更新")
        self.btn_add.setStyleSheet(f"QPushButton{{background:{DONE_COLOR};color:white;border-radius:18px;border:none;font-size:14px;min-width:60px;min-height:36px;padding:0 12px;}}QPushButton:hover{{background:#73D13D;}}")
        self.edit_input.setFocus()

    def _add_task(self):
        content = self.edit_input.text().strip()
        if not content:
            return

        if self._editing_id:
            from ..database import update_task
            due = self.picked_date
            alarm = f"{due} {self.time_picker.time().toString('HH:mm')}" if due else None
            update_task(self._editing_id, content=content, due_date=due, alarm_time=alarm)
            self._editing_id = None
        else:
            due = self.picked_date
            alarm = f"{due} {self.time_picker.time().toString('HH:mm')}" if due else None
            add_task(content=content, due_date=due, alarm_time=alarm)

        self.edit_input.clear()
        self.time_picker.setTime(QTime(18, 0))
        self.picked_date = None
        self.edit_input.setPlaceholderText("输入待办内容...")
        self.btn_add.setText("＋")
        self.btn_add.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;border-radius:18px;border:none;font-size:20px;}}QPushButton:hover{{background:#4096FF;}}")
        self.refresh()

    def _pick_date(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择日期")
        dialog.setFixedSize(300, 260)
        vl = QVBoxLayout(dialog)
        cal = QCalendarWidget()
        cal.setGridVisible(True)
        cal.setStyleSheet(f"QCalendarWidget{{background:{CARD_BG};color:{TEXT_PRIMARY};}}")
        vl.addWidget(cal)
        bl = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;border-radius:6px;padding:6px 20px;}}")
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(f"QPushButton{{background:{LIGHT_BG};color:{TEXT_PRIMARY};border-radius:6px;padding:6px 20px;border:1px solid {BORDER};}}")
        bl.addWidget(btn_cancel)
        bl.addWidget(btn_ok)
        vl.addLayout(bl)
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.picked_date = cal.selectedDate().toString("yyyy-MM-dd")
            self.edit_input.setPlaceholderText(f"输入待办内容... ({self.picked_date})")
        dialog.deleteLater()


