#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

npm --prefix frontend ci
npm --prefix frontend run build
python3 -m venv .desktop-venv
.desktop-venv/bin/python -m pip install -r desktop-requirements.txt
.desktop-venv/bin/python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name Webmark \
  --paths . \
  --add-data "frontend/dist:frontend_dist" \
  --collect-all trafilatura \
  --collect-all courlan \
  --collect-all htmldate \
  --collect-all justext \
  --collect-all webview \
  desktop_launcher.py

echo "Built: $PROJECT_DIR/dist/Webmark.app"
