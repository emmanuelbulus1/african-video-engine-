#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# quickstart.sh — African Video Engine local dev launcher
# ─────────────────────────────────────────────────────────
set -e

echo ""
echo "🌍  African Video Engine — Quickstart"
echo "─────────────────────────────────────"

# ── Check .env file ───────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "⚠️  No .env file found. Creating template…"
  cat > .env << 'EOF'
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ASSEMBLYAI_API_KEY=...
EOF
  echo "✏️  Please edit .env and add your 3 API keys, then re-run this script."
  exit 1
fi

# ── Validate required keys ────────────────────────────────
source .env

check_key() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ] || [ "$value" = "sk-..." ] || [ "$value" = "..." ]; then
    echo "❌  $name is missing or placeholder in .env"
    MISSING=1
  else
    echo "✅  $name found"
  fi
}

MISSING=0
check_key "OPENAI_API_KEY"     "$OPENAI_API_KEY"
check_key "ELEVENLABS_API_KEY" "$ELEVENLABS_API_KEY"
check_key "ASSEMBLYAI_API_KEY" "$ASSEMBLYAI_API_KEY"

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo "Fix the missing keys in .env and re-run."
  exit 1
fi

echo ""
echo "🐍  Installing Python dependencies…"
pip install -r requirements.txt -q

echo ""
echo "⚛️   Building frontend…"
cd frontend
npm install -q
npm run build -q
cd ..

echo ""
echo "🚀  Starting server on http://localhost:8000"
echo "    Press Ctrl+C to stop."
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
