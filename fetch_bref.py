"""
Pulls schedule, team season (advanced) stats, and team game logs from
Basketball-Reference for a given season.

IMPORTANT — run this on your own machine, not in a sandboxed environment:
basketball-reference.com actively bot-detects and will temporarily block
IPs that request too fast or don't look like a browser. This script:
  - sets a real User-Agent
  - sleeps config.REQUEST_DELAY_SECONDS between requests
  - unwraps tables that bref hides inside HTML comments (a known quirk)

If you get repeatedly blocked, increase the delay, or use the free tier of
a proxy/API alternative (e.g. balldontlie.io) for game logs and reserve
bref scraping for the season-summary tables you can't get elsewhere.
"""

import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment

import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

BASE = "https://www.basketball-reference.com"


def _get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    time.sleep(config.REQUEST_DELAY_SECONDS)
    if resp.status_code != 200:
        raise RuntimeError(f"GET {url} -> {resp.status_code}. "
                            f"Likely rate-limited or blocked; slow down.")
    return BeautifulSoup(resp.text, "html.parser")


def _find_table(soup: BeautifulSoup, table_id: str):
    """bref renders many tables only inside HTML comments to deter scraping."""
    table = soup.find("table", id=table_id)
    if table is not None:
        return table
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if table_id in comment:
            inner = BeautifulSoup(comment, "html.parser")
            table = inner.find("table", id=table_id)
            if table is not None:
                return table
    return None


def _table_to_df(table) -> pd.DataFrame:
    df = pd.read_html(str(table))[0]
    # bref repeats the header row periodically inside the body; drop those
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[-1] for c in df.columns]
    return df[df.iloc[:, 0] != df.columns[0]].reset_index(drop=True)


def get_month_schedule(season: int, month: str) -> pd.DataFrame:
    """One month of the season's schedule/results, e.g. month='january'."""
    url = f"{BASE}/leagues/NBA_{season}_games-{month}.html"
    soup = _get_soup(url)
    table = _find_table(soup, "schedule")
    if table is None:
        return pd.DataFrame()
    df = _table_to_df(table)
    df["season"] = season
    return df


def get_full_schedule(season: int = config.SEASON) -> pd.DataFrame:
    """Concatenates every month of the season into one schedule/results table."""
    frames = []
    for month in config.MONTHS_IN_SEASON:
        try:
            df = get_month_schedule(season, month)
            if not df.empty:
                frames.append(df)
        except RuntimeError as e:
            print(f"  skipping {month}: {e}")
    if not frames:
        return pd.DataFrame()
    schedule = pd.concat(frames, ignore_index=True)
    schedule = schedule.rename(columns={
        "Visitor/Neutral": "away_team",
        "PTS": "away_pts",
        "Home/Neutral": "home_team",
        "PTS.1": "home_pts",
        "Date": "game_date",
    })
    keep = [c for c in ["game_date", "away_team", "away_pts",
                         "home_team", "home_pts", "season"] if c in schedule.columns]
    return schedule[keep]


def get_team_advanced_stats(season: int = config.SEASON) -> pd.DataFrame:
    """
    Season-level team advanced stats (SRS, pace, ORtg, DRtg, etc).
    NOTE: these are FULL-SEASON numbers, only safe to use once the season is
    over. For in-season prediction you need as-of-date rolling stats instead
    — see get_team_gamelog() + build_dataset.compute_rolling_team_form().
    """
    url = f"{BASE}/leagues/NBA_{season}.html"
    soup = _get_soup(url)
    table = _find_table(soup, "misc_stats") or _find_table(soup, "advanced-team")
    if table is None:
        raise RuntimeError(
            "Could not find team advanced-stats table. bref sometimes "
            "renames table ids year to year — inspect the page source "
            "for the correct id and update this function."
        )
    return _table_to_df(table)


def get_team_gamelog(team_abbr: str, season: int = config.SEASON) -> pd.DataFrame:
    """
    Game-by-game log for one team (basic box score stats), which is what you
    need to build as-of-date rolling features without leaking future data.
    """
    url = f"{BASE}/teams/{team_abbr}/{season}/gamelog/"
    soup = _get_soup(url)
    table = _find_table(soup, "tgl_basic")
    if table is None:
        raise RuntimeError(f"No game log table found for {team_abbr} {season}")
    df = _table_to_df(table)
    df["team"] = team_abbr
    return df


def fetch_all_team_gamelogs(season: int = config.SEASON) -> pd.DataFrame:
    """Loops every team. Slow by design (rate-limited) — cache the result."""
    frames = []
    for bref_code in config.BREF_TO_ODDS_TEAM:
        print(f"Fetching gamelog: {bref_code} {season}")
        try:
            frames.append(get_team_gamelog(bref_code, season))
        except RuntimeError as e:
            print(f"  failed {bref_code}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


if __name__ == "__main__":
    os.makedirs(config.RAW_DIR, exist_ok=True)

    print("Fetching season schedule...")
    schedule = get_full_schedule()
    schedule.to_csv(f"{config.RAW_DIR}/schedule_{config.SEASON}.csv", index=False)
    print(f"  saved {len(schedule)} games")

    print("Fetching team game logs (this takes a while, ~30 teams * delay)...")
    gamelogs = fetch_all_team_gamelogs()
    gamelogs.to_csv(f"{config.RAW_DIR}/team_gamelogs_{config.SEASON}.csv", index=False)
    print(f"  saved {len(gamelogs)} team-game rows")
