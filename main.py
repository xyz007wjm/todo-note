#!/usr/bin/env python3
"""待办记事本 - 入口文件"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QSharedMemory, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap, QIcon, QBrush, QPen

from app.main_window import MainWindow
from app.database import init_db


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("待办记事本")
    app.setApplicationDisplayName("待办记事本")

    # App icon
    sz = 512
    pix = QPixmap(sz, sz)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#1677FF")))
    p.setPen(QPen(QColor("#1677FF"), 0))
    p.drawRoundedRect(20, 20, sz-40, sz-40, 80, 80)
    p.setPen(QColor("white"))
    ft = QFont("Helvetica Neue", 140, QFont.Weight.Bold)
    p.setFont(ft)
    p.drawText(QRect(0, 0, sz, sz), Qt.AlignmentFlag.AlignCenter, "TODO")
    p.end()
    app.setWindowIcon(QIcon(pix))

    # Single instance check
    shared_mem = QSharedMemory("TodoNoteApp_SingleInstance")
    if shared_mem.attach():
        QMessageBox.warning(None, "提示", "待办记事本已在运行中\n请关闭后再重新打开")
        sys.exit(0)
    shared_mem.create(1)

    init_db()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
