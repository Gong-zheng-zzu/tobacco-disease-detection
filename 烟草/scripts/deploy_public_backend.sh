#!/usr/bin/env bash
set -euo pipefail

# Usage: bash deploy_public_backend.sh /opt/tobacco/drf_test002 PUBLIC_IP
# Run as root on Alibaba Cloud Linux 3 after copying the backend directory.
PROJECT_DIR="${1:?Pass the absolute Django project directory}"
PUBLIC_IP="${2:?Pass the server public IP}"
cd "$PROJECT_DIR"
test -f manage.py
test -f model_weights/yolo_unified_6class_best.pt

PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt gunicorn
"$VENV_PYTHON" manage.py migrate

# Seed only a fresh database; the command appends records each time it runs.
if [ ! -f .demo_data_seeded ]; then
  "$VENV_PYTHON" manage.py generate_sample_data
  touch .demo_data_seeded
fi

cat >/etc/systemd/system/tobacco-api.service <<EOF
[Unit]
Description=Tobacco Django API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
Environment=DJANGO_ALLOWED_HOSTS=$PUBLIC_IP
Environment=PYTHONUNBUFFERED=1
ExecStart=$PROJECT_DIR/.venv/bin/gunicorn drf_test002.wsgi:application --bind 0.0.0.0:8081 --workers 1 --threads 2 --timeout 180
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now tobacco-api
systemctl --no-pager --full status tobacco-api
curl --max-time 10 -sS -o /dev/null -w 'Local API HTTP %{http_code}\n' http://127.0.0.1:8081/api/login/
echo 'Also allow TCP 8081 in the Alibaba Cloud security group.'
