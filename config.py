import os

# Season definitions
BASELINE_SEASON = 2026   # Mandatory 2025-26 Bref summary stats
PREDICT_SEASON = 2027    # 2026-27 upcoming season schedule

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "data", "models")

for path in [RAW_DIR, PROCESSED_DIR, MODELS_DIR]:
    os.makedirs(path, exist_ok=True)

# Rate limiting
REQUEST_DELAY_SECONDS = 3.5

# Standardized team mapping across Bref and odds providers
BREF_TO_STANDARD = {
    "BRK": "BKN", "CHO": "CHA", "PHO": "PHX"
}

# Historical odds provider / legacy franchise mappings to current franchise codes
HISTORICAL_TEAM_MAP = {
    "SEA": "OKC",  # Seattle SuperSonics -> Oklahoma City Thunder
    "NJN": "BKN",  # New Jersey Nets -> Brooklyn Nets
    "BRK": "BKN",  # Bref Brooklyn
    "CHO": "CHA",  # Bref Charlotte
    "CHH": "CHA",  # Original Charlotte Hornets
    "NOH": "NOP",  # New Orleans Hornets -> Pelicans
    "NOK": "NOP",  # New Orleans/OKC Hornets -> Pelicans
    "PHO": "PHX",  # Bref Phoenix
    "GS": "GSW",
    "NO": "NOP",
    "NY": "NYK",
    "SA": "SAS"
}