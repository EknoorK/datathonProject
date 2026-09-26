import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config


def blend_prior(game_num: int, rolling_val: float, baseline_val: float, fade_window: int = 15) -> float:
    """Blends the 2025-26 season baseline with the live season rolling average."""
    if pd.isna(rolling_val) or game_num <= 1:
        return baseline_val
    if game_num >= fade_window:
        return rolling_val
    weight_current = game_num / fade_window
    return (rolling_val * weight_current) + (baseline_val * (1.0 - weight_current))


def compute_leak_free_rolling(gamelogs: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Computes trailing team statistics using strict shift(1) to prevent look-ahead bias."""
    gamelogs = gamelogs.sort_values(["team", "game_date"]).reset_index(drop=True)
    gamelogs["game_num"] = gamelogs.groupby("team").cumcount() + 1

    # Shift(1) guarantees current game points are excluded from the rolling average
    gamelogs["rolling_pts"] = (
        gamelogs.groupby("team")["pts"]
        .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    )
    gamelogs["rolling_opp_pts"] = (
        gamelogs.groupby("team")["opp_pts"]
        .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    )
    
    # Rest days calculation
    gamelogs["days_rest"] = gamelogs.groupby("team")["game_date"].diff().dt.days
    gamelogs["days_rest"] = gamelogs["days_rest"].clip(lower=1, upper=7).fillna(3)

    return gamelogs


def build_feature_table(schedule: pd.DataFrame, odds: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """Merges rolling form, priors, and point spreads into a unified modeling dataset."""
    df = schedule.copy()
    
    # Join spreads
    df = df.merge(odds, on=["game_date", "home_team", "away_team"], how="inner")
    
    # Calculate point differential and binary target (Did home cover spread?)
    # Spread is from Home team's perspective (-5.5 means Home is favored by 5.5)
    df["home_margin"] = df["home_pts"] - df["away_pts"]
    df["target_cover"] = ((df["home_margin"] + df["spread"]) > 0).astype(int)

    # Standardize baseline ratings
    baseline_map = {}
    if not baseline.empty and "Team" in baseline.columns:
        baseline_clean = baseline.copy()
        baseline_clean["Team"] = baseline_clean["Team"].replace(config.HISTORICAL_TEAM_MAP)
        baseline_map = baseline_clean.set_index("Team")["NRtg"].to_dict()

    df["home_prior_nrtg"] = df["home_team"].map(baseline_map).fillna(0.0)
    df["away_prior_nrtg"] = df["away_team"].map(baseline_map).fillna(0.0)
    df["net_prior_edge"] = df["home_prior_nrtg"] - df["away_prior_nrtg"]

    # Final feature schema for Person C
    feature_df = pd.DataFrame({
        "game_id": df["game_date"].dt.strftime("%Y%m%d") + "_" + df["home_team"] + "_" + df["away_team"],
        "date": df["game_date"],
        "home_team": df["home_team"],
        "away_team": df["away_team"],
        "spread": df["spread"],
        "net_prior_edge": df["net_prior_edge"],
        "home_prior_nrtg": df["home_prior_nrtg"],
        "away_prior_nrtg": df["away_prior_nrtg"],
        "target_cover": df["target_cover"]
    }).sort_values("date").reset_index(drop=True)

    return feature_df


if __name__ == "__main__":
    odds_file = os.path.join(config.PROCESSED_DIR, "cleaned_odds.csv")
    baseline_file = os.path.join(config.RAW_DIR, f"baseline_{config.BASELINE_SEASON}_advanced.csv")
    
    if os.path.exists(odds_file):
        odds_df = pd.read_csv(odds_file, parse_dates=["game_date"])
    else:
        from load_odds import clean_odds_data
        odds_df = clean_odds_data()

    baseline_df = pd.read_csv(baseline_file) if os.path.exists(baseline_file) else pd.DataFrame()

    # Generate synthetic game results to match cleaned_odds for building training set
    sched_mock = odds_df.copy()
    sched_mock["home_pts"] = np.random.normal(114, 10, len(sched_mock)).round()
    sched_mock["away_pts"] = np.random.normal(110, 10, len(sched_mock)).round()

    features = build_feature_table(sched_mock, odds_df, baseline_df)
    out_path = os.path.join(config.PROCESSED_DIR, "team_game_features.csv")
    features.to_csv(out_path, index=False)
    print(f"Features generated: {len(features)} rows written to {out_path}")
