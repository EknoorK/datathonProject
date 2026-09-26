# config.py

SEASON = 2026
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

# Map legacy/historical Kaggle acronyms to modern Bref acronyms
TEAM_MAPPINGS = {
    'SEA': 'OKC',  # Seattle SuperSonics -> Thunder
    'NJN': 'BRK',  # New Jersey Nets -> Brooklyn Nets
    'BKN': 'BRK',  # Alternate Brooklyn abbreviation
    'CHA': 'CHO',  # Charlotte Bobcats/Hornets -> Bref CHO
    'CHH': 'CHO',  # Old Charlotte Hornets
    'NOH': 'NOP',  # New Orleans Hornets -> Pelicans
    'NOK': 'NOP',  # New Orleans/Oklahoma City Hornets -> Pelicans
    'PHX': 'PHO'   # Phoenix Suns
}