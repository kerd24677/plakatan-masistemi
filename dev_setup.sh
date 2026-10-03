#!/usr/bin/env bash
# Linux geliştirme ortamı kurulumu (yalnızca kod yazma/test için).
# ÜRETİM DAĞITIMI WINDOWS ÜZERİNDE build.bat İLE YAPILIR.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-build.txt

echo "Kurulum tamamlandı. Testleri çalıştırmak için:"
echo "  source .venv/bin/activate && pytest -q"
echo "Uygulamayı (Linux'ta, geliştirme amaçlı) başlatmak için:"
echo "  source .venv/bin/activate && python main.py"
