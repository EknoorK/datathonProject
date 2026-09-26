import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config


def clean_odds_data(input_filename: str = "raw_odds.csv") -> pd.DataFrame:
    raw_path = os.path.join(config.RAW_DIR, input_filename)
    
    if not os.path.exists(raw_path):
        print(f"File {raw_path} not found. Generating mock odds for pipeline continuity.")
        return _generate_mock_odds()

    df = pd.read_csv(raw_path)

    # Standardize column naming variations across Kaggle datasets
    col_map = {
        "Date": "game_date", "date": "game_date",
        "Home": "home_team", "HomeTeam": "home_team", "home": "home_team",
        "Away": "away_team", "AwayTeam": "away_team", "away": "away_team",
        "Spread": "spread", "home_spread": "spread", "Point_Spread": "spread"
    }
    df = df.rename(columns=col_map)
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Harmonize team abbreviations
    df["home_team"] = df["home_team"].replace(config.HISTORICAL_TEAM_MAP)
    df["away_team"] = df["away_team"].replace(config.HISTORICAL_TEAM_MAP)
    df["spread"] = pd.to_numeric(df["spread"], errors="coerce")

    cleaned = df.dropna(subset=["game_date", "home_team", "away_team", "spread"])
    output_path = os.path.join(config.PROCESSED_DIR, "cleaned_odds.csv")
    cleaned.to_csv(output_path, index=False)
    return cleaned


def _generate_mock_odds() -> pd.DataFrame:
    import numpy as np
    teams = ["BOS", "NYK", "PHI", "MIL", "LAL", "DEN", "GSW", "PHX", "MIA", "DAL"]
    dates = pd.date_range(start="2023-10-24", end="2024-04-14", freq="D")
    
    rows = []
    for d in dates:
        for _ in range(3):
            home, away = np.random.choice(teams, size=2, replace=False)
            rows.append({
                "game_date": d,
                "home_team": home,
                "away_team": away,
                "spread": round(float(np.random.normal(-3.0, 5.0)), 1)
            })
    
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(config.PROCESSED_DIR, "cleaned_odds.csv"), index=False)
    return df


if __name__ == "__main__":
    clean_odds_data()
