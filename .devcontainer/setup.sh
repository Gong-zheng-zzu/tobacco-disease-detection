#!/usr/bin/env bash
# Codespaces 环境初始化：装依赖 -> 建数据库 -> 生成演示数据
# 本脚本在容器创建时执行一次（onCreateCommand）
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/烟草/前后端/drf_test002"
FRONTEND_DIR="$REPO_ROOT/烟草/前后端/tobacco"

echo "=============================================="
echo " 烟草病害识别系统 - 环境初始化"
echo "=============================================="

# ---------- 1. Python 依赖 ----------
echo ""
echo "[1/5] 安装 Python 依赖（torch CPU 版约 200MB，需要几分钟）..."
python -m pip install --upgrade pip --quiet
python -m pip install -r "$BACKEND_DIR/requirements.txt"

# ---------- 2. 校验模型权重 ----------
echo ""
echo "[2/5] 检查模型权重..."
WEIGHTS="$BACKEND_DIR/model_weights/yolo_unified_6class_best.pt"
if [ -f "$WEIGHTS" ]; then
    echo "      OK: $(du -h "$WEIGHTS" | cut -f1) $WEIGHTS"
else
    # 回退：仓库内另一份同内容权重
    FALLBACK="$REPO_ROOT/烟草/models/yolo_unified_6class_best.pt"
    if [ -f "$FALLBACK" ]; then
        mkdir -p "$BACKEND_DIR/model_weights"
        cp "$FALLBACK" "$WEIGHTS"
        echo "      已从 models/ 复制权重"
    else
        echo "      !! 警告：找不到模型权重，检测功能将返回 503"
    fi
fi

# ---------- 3. 前端依赖 ----------
echo ""
echo "[3/5] 安装前端依赖..."
cd "$FRONTEND_DIR"
npm install --no-audit --no-fund

# ---------- 4. 数据库迁移 ----------
echo ""
echo "[4/5] 初始化 SQLite 数据库..."
cd "$BACKEND_DIR"
python manage.py migrate --noinput

# ---------- 5. 演示数据 ----------
echo ""
echo "[5/5] 生成演示数据（账号 admin / 123456）..."
python manage.py generate_sample_data

echo ""
echo "=============================================="
echo " 初始化完成"
echo " 服务将自动启动，请打开 PORTS 面板中的 5173 端口"
echo " 登录账号: admin   密码: 123456"
echo "=============================================="
