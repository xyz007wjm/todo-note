"""
Setup script for building macOS .app bundle with py2app.
"""
import sys
import os
from setuptools import setup

APP = ['main.py']
APP_NAME = "待办记事本"

DATA_FILES = [('assets', ['assets/alert.wav'])]

OPTIONS = {
    'argv_emulation': False,
    'packages': ['PySide6', 'httpx'],
    'includes': ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    'excludes': ['tkinter', 'matplotlib', 'PIL'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': 'com.jackwang.todonote',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': APP_NAME,
        'NSHumanReadableCopyright': 'Copyright 2026 jackwang',
        'NSMicrophoneUsageDescription': '用于语音输入功能',
    },
    'iconfile': None,
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
