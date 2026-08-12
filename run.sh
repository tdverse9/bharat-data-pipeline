set -e

echo "=== Installing Dependencies ==="
pip install -r requirements.txt
python -m spacy download en_core_web_sm || true
playwright install chromium || true

echo "=== Running Data Pipeline ==="
python main.py