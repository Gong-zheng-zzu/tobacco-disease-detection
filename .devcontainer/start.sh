#!/usr/bin/env bash
# 启动 Django 后端 + Vite 前端（postAttachCommand，每次连接容器时执行）
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/烟草/前后端/drf_test002"
FRONTEND_DIR="$REPO_ROOT/烟草/前后端/tobacco"
LOG_DIR="/tmp/tobacco-logs"

mkdir -p "$LOG_DIR"

# 幂等：已在监听的端口不重复启动（避免重连容器时起两份）
port_busy() {
    # 优先用 ss，缺失时退回 python 探测，不依赖 lsof
    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | grep -q ":$1 "
    else
        python -c "
import socket, sys
s = socket.socket()
try:
    s.connect(('127.0.0.1', $1)); sys.exit(0)
except Exception:
    sys.exit(1)
finally:
    s.close()
" 2>/dev/null
    fi
}

echo "=============================================="
echo " 启动烟草病害识别系统"
echo "=============================================="

# ---------- Django 后端 ----------
if port_busy 8000; then
    echo "[后端] 8000 端口已在运行，跳过"
else
    echo "[后端] 启动 Django (0.0.0.0:8000)..."
    cd "$BACKEND_DIR"
    nohup python manage.py runserver 0.0.0.0:8000 --noreload \
        > "$LOG_DIR/django.log" 2>&1 &
    sleep 3
fi

# ---------- Vite 前端 ----------
if port_busy 5173; then
    echo "[前端] 5173 端口已在运行，跳过"
else
    echo "[前端] 启动 Vite (0.0.0.0:5173)..."
    cd "$FRONTEND_DIR"
    CODESPACES="${CODESPACES:-true}" nohup npm run dev -- --host 0.0.0.0 \
        > "$LOG_DIR/vite.log" 2>&1 &
    sleep 4
fi

echo ""
echo "=============================================="
echo " 服务已启动"
echo ""
echo " 访问方式：打开下方 PORTS（端口）面板，"
echo "           点击 5173 端口的地球图标"
echo ""
echo " 登录账号：admin"
echo " 登录密码：123456"
echo ""
echo " 测试图片：烟草/demo_images/  （6类各3张）"
echo ""
echo " 日志位置：$LOG_DIR/{django,vite}.log"
echo "=============================================="
