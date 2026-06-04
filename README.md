# 待办记事本 (Todo Note)

一款简洁高效的桌面待办事项管理工具，仿钉钉待办风格。

## 功能特点

- ✅ **待办管理** — 添加、编辑、完成、删除待办事项
- 📅 **日期选择** — 支持设置到期日期
- ⏰ **闹钟提醒** — 到点弹出提醒 + macOS 系统通知
- 🔢 **任务计数** — 自动统计待办和已完成数量
- 🔍 **分类筛选** — 全部 / 今天 / 已完成
- 🎨 **深色模式** — 自动跟随 macOS 深色/浅色主题切换
- 🔌 **AI 助手** — 支持 DeepSeek API 智能处理
- 🔔 **单实例** — 只允许运行一个窗口
- 🪟 **窗口记忆** — 自动保存窗口位置和大小
- 🏷️ **序号标记** — 待办列表自动编号
- ⏳ **过期高亮** — 超期未完成的待办自动标红

## 安装

### macOS

```bash
# 1. 克隆仓库
git clone https://github.com/xyz007wjm/todo-note.git
cd todo-note

# 2. 运行启动脚本（自动安装依赖）
bash run.sh
```

### 手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python3 main.py
```

### Windows

```bash
# 1. 克隆仓库
git clone https://github.com/xyz007wjm/todo-note.git
cd todo-note

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行
python main.py
```

> **注意**: Windows 上闹钟提示音需要 WAV 播放支持，默认使用系统播放器。

## 打包为独立应用

### macOS (.app / .dmg)

```bash
# 安装 py2app
pip install py2app

# 生成 setup.py
py2applet --make-setup main.py

# 构建 .app
python setup.py py2app --packages=PySide6

# 创建 .dmg (安装 create-dmg)
brew install create-dmg
create-dmg --volname "待办记事本" --window-pos 200 120 --window-size 600 400 --icon-size 100 --app-drop-link 380 205 "TodoNote.dmg" "dist/待办记事本.app"
```

### Windows (.exe)

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --windowed --onefile --name "待办记事本" --icon icon.ico main.py
```

## 技术栈

- **语言**: Python 3.10+
- **GUI**: PySide6 (Qt6)
- **数据库**: SQLite
- **API**: httpx (DeepSeek 集成)

## 项目结构

```
待办记事本/
├── main.py                  # 入口文件
├── run.sh                   # macOS 启动脚本
├── requirements.txt         # Python 依赖
├── .gitignore
├── README.md
├── assets/
│   └── alert.wav            # 闹钟提示音
└── app/
    ├── __init__.py
    ├── database.py           # 数据库操作
    ├── main_window.py        # 主窗口
    ├── scheduler.py          # 闹钟调度器
    ├── api_client.py         # DeepSeek API
    └── widgets/
        ├── __init__.py
        ├── todo_widget.py    # 待办列表组件
        └── alarm_dialog.py   # 闹钟提醒弹窗
```

## 软件制作人

**jackwang**

- 网站: [https://wangjinming.com](https://wangjinming.com)
- 年份: 2026

## License

MIT License
