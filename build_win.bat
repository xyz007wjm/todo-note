@echo off
chcp 65001 >nul
echo 待办记事本 - Windows 安装包构建
echo =================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未安装 Python，请先安装 Python 3.10+
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

pip install pyinstaller

REM 生成图标
echo [2/3] 生成图标...
python -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGBA', (256, 256), (0,0,0,0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([20,20,236,236], radius=40, fill='#1677FF')
try:
    f = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 80)
except:
    f = ImageFont.load_default()
bbox = d.textbbox((0,0), 'TODO', font=f)
x = (256-(bbox[2]-bbox[0]))//2
y = (256-(bbox[3]-bbox[1]))//2
d.text((x,y), 'TODO', fill='white', font=f)
img.save('icon.ico', format='ICO', sizes=[(256,256)])
"

REM 打包
echo [3/3] 打包中...
pyinstaller --windowed --onefile --name "待办记事本" --icon icon.ico --add-data "assets/alert.wav;assets" main.py

echo.
echo ✅ 构建完成！
echo 安装包位置: dist\待办记事本.exe
pause
