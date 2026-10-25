"""Build public.chart_performance from public.chart_weekly (Member 1, Report 3).

Definitions (official):
  lifetime_average_rank = mean(rank) over all valid weekly rows of (track, market)
                          within the 2021-2026 study window
  chart_score           = CHART_SCORE_BASE - lifetime_average_rank   (BASE = 101)
  peak_rank             = min(rank)
  weeks_on_chart        = number of valid weekly rows
  weeks_in_top10        = number of weeks with rank 1..10
Pairs with no chart rows get no row (never ChartScore = 0).
Re-runnable: upsert on (spotify_track_id, market), no duplicates.

Usage:
  python src/chart/build_chart_performance.py                 # read chart_weekly from Supabase, upsert
  python src/chart/build_chart_performance.py --source csv    # offline: data/raw/chart/chart_weekly*.csv
  python src/chart/build_chart_performance.py --dry-run       # compute only, do not write to Supabase
Env (.env, never commit): SUPABASE_URL, SUPABASE_KEY
"""
import argparse
import os
from pathlib import Path

import pandas as pd

CHART_SCORE_BASE = 101          # agreed definition; change here only if the whole team agrees
MARKETS = ("VN", "US", "KR")
KEY = ["spotify_track_id", "market", "chart_date"]
BATCH = 500
ROOT = Path(__file__).resolve().parents[2]


def load_from_csv() -> pd.DataFrame:
    files = sorted((ROOT / "data/raw/chart").glob("chart_weekly*.csv"))
    return pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in files], ignore_index=True)


def load_from_supabase() -> pd.DataFrame:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(ROOT / ".env")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    rows, start, page = [], 0, 1000
    while True:
        r = (sb.table("chart_weekly")
               .select("spotify_track_id,market,chart_date,rank,streams")
               .order("id").range(start, start + page - 1).execute())
        rows += r.data
        if len(r.data) < page:
            break
        start += page
    return pd.DataFrame(rows)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only valid rows; the cleaning rules are logged by validate_chart_data.py."""
    df = df.drop_duplicates(KEY)
    df = df[df["market"].isin(MARKETS)]
    df = df[df["rank"].between(1, 200)]
    return df.dropna(subset=["chart_date"])


def build(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["spotify_track_id", "market"])["rank"]
    out = g.agg(lifetime_average_rank="mean", peak_rank="min", weeks_on_chart="size").reset_index()
    out["weeks_in_top10"] = g.apply(lambda s: int((s <= 10).sum())).values
    out["chart_score"] = CHART_SCORE_BASE - out["lifetime_average_rank"]
    return out[["spotify_track_id", "market", "lifetime_average_rank", "chart_score",
                "peak_rank", "weeks_on_chart", "weeks_in_top10"]]


def upsert(out: pd.DataFrame) -> None:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(ROOT / ".env")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    recs = out.astype(object).where(out.notna(), None).to_dict("records")
    for i in range(0, len(recs), BATCH):
        sb.table("chart_performance").upsert(
            recs[i:i + BATCH], on_conflict="spotify_track_id,market").execute()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["supabase", "csv"], default="supabase")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    raw = load_from_csv() if a.source == "csv" else load_from_supabase()
    out = build(clean(raw))
    assert not out.duplicated(["spotify_track_id", "market"]).any()
    print(f"raw rows={len(raw)} -> pairs={len(out)}")
    print(out.groupby("market").size().to_string())
    if not a.dry_run:
        upsert(out)
        print("upserted", len(out), "rows into chart_performance")
