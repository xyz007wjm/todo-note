#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python3" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv .venv
    echo "正在安装依赖..."
    .venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
fi

# Generate alert sound if missing
if [ ! -f "assets/alert.wav" ]; then
    echo "正在生成提示音..."
    .venv/bin/python3 -c "
import numpy as np, soundfile as sf, os
sr = 22050; t = np.linspace(0, 1, sr)
sig = 0.5 * np.sin(2 * np.pi * np.linspace(440, 880, sr) * t)
env = np.minimum(t * 10, 1.0) * np.minimum((1 - t) * 10, 1.0)
sig = np.tile(sig * env, 3)
os.makedirs('assets', exist_ok=True)
sf.write('assets/alert.wav', sig, sr)
"
fi

echo "启动待办应用..."
.venv/bin/python3 main.py
