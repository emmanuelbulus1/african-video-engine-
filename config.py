import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ASSEMBLYAI_API_KEY  = os.getenv("ASSEMBLYAI_API_KEY", "")

# ── Models ────────────────────────────────────────────────
OPENAI_MODEL        = "gpt-4o-mini"
ELEVENLABS_VOICE_ID = "ErXwobaYiN019PkySvjV"   # Antoni — deep African tone

# ── App Settings ──────────────────────────────────────────
APP_TITLE           = "African Video Engine"
APP_VERSION         = "2.0.0"
MAX_VIDEO_DURATION  = 600          # seconds (10 min cap)
TEMP_DIR            = "/tmp/african_engine"
