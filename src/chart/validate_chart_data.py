"""Validate chart_weekly and chart_performance (Member 1, Report 3).

Writes:
  logs/chart_validation_log.csv            (check, scope, status, value, expected, note)
  reports/report3/chart_statistics.csv      (descriptive stats per market)

Usage:
  python src/chart/validate_chart_data.py                 # reads Supabase
  python src/chart/validate_chart_data.py --source csv    # offline: recompute from data/raw/chart/*.csv
"""
import argparse
import os
from pathlib import Path

import pandas as pd

import build_chart_performance as b

ROOT = b.ROOT
VARS = ["lifetime_average_rank", "chart_score", "peak_rank", "weeks_on_chart"]


def load_supabase_table(name: str, cols: str) -> pd.DataFrame:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(ROOT / ".env")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    rows, start, page = [], 0, 1000
    while True:
        r = sb.table(name).select(cols).range(start, start + page - 1).execute()
        rows += r.data
        if len(r.data) < page:
            break
        start += page
    return pd.DataFrame(rows)


def main(source: str) -> None:
    log = []

    def check(name, scope, ok, value, expected, note=""):
        log.append(dict(check=name, scope=scope, status="PASS" if ok else "FAIL",
                        value=value, expected=expected, note=note))

    if source == "csv":
        raw = b.load_from_csv()
        overlap = int(raw.duplicated(b.KEY).sum())
        check("csv_shard_overlap_rows", "chart_weekly", True, overlap, "info",
              "chart_weekly*.csv shards overlap; removed before checks (Supabase UNIQUE does the same)")
        raw = raw.drop_duplicates(b.KEY)
        songs = None   # songs table is only reachable via Supabase; FK already enforces this there
        perf = b.build(b.clean(raw))
        note_src = "recomputed from CSV"
    else:
        raw = b.load_from_supabase()
        songs = set(load_supabase_table("songs", "spotify_track_id")["spotify_track_id"])
        perf = load_supabase_table("chart_performance", ",".join(
            ["spotify_track_id", "market"] + VARS + ["weeks_in_top10"]))
        note_src = "chart_performance table"

    # --- chart_weekly quality ---
    check("rows_total", "chart_weekly", True, len(raw), "info")
    if songs is not None:
        check("track_id_in_songs", "chart_weekly", raw["spotify_track_id"].isin(songs).all(),
              int((~raw["spotify_track_id"].isin(songs)).sum()), 0, "orphan rows")
    check("market_in_VN_US_KR", "chart_weekly", raw["market"].isin(b.MARKETS).all(),
          int((~raw["market"].isin(b.MARKETS)).sum()), 0)
    check("rank_in_1_200", "chart_weekly", raw["rank"].between(1, 200).all(),
          int((~raw["rank"].between(1, 200)).sum()), 0)
    check("streams_not_null_nonnegative", "chart_weekly",
          raw["streams"].notna().all() and (raw["streams"] >= 0).all(),
          int(raw["streams"].isna().sum() + (raw["streams"] < 0).sum()), 0)
    zero = int((raw["streams"] == 0).sum())
    check("streams_equal_zero_rows", "chart_weekly", True, zero, "info",
          "kept: streams is not used in ChartScore (known case: KR 2021-06-10, rank 101)")
    dates = pd.to_datetime(raw["chart_date"], errors="coerce")
    check("chart_date_valid", "chart_weekly", dates.notna().all(), int(dates.isna().sum()), 0)
    check("chart_date_all_thursday", "chart_weekly", (dates.dt.dayofweek == 3).all(),
          int((dates.dt.dayofweek != 3).sum()), 0)
    dup = int(raw.duplicated(b.KEY).sum())
    check("no_duplicate_track_market_date", "chart_weekly", dup == 0, dup, 0)
    check("rank_gt_100_share", "chart_weekly", True, round(float((raw['rank'] > 100).mean()), 4),
          "info", "Top-200 chart -> chart_score can be negative")

    # --- chart_performance quality ---
    check("pairs_total", "chart_performance", True, len(perf), "info", note_src)
    check("no_duplicate_track_market", "chart_performance",
          not perf.duplicated(["spotify_track_id", "market"]).any(),
          int(perf.duplicated(["spotify_track_id", "market"]).sum()), 0)
    formula_err = (perf["chart_score"].astype(float) - (b.CHART_SCORE_BASE - perf["lifetime_average_rank"].astype(float))).abs().max()
    check("chart_score_equals_101_minus_avg", "chart_performance", formula_err < 1e-9, float(formula_err), "<1e-9")
    clean = b.build(b.clean(raw))
    m = perf.merge(clean, on=["spotify_track_id", "market"], suffixes=("", "_src"), how="outer", indicator=True)
    check("pairs_match_source", "chart_performance", (m["_merge"] == "both").all(),
          int((m["_merge"] != "both").sum()), 0, "pairs only in one side")
    both = m[m["_merge"] == "both"]
    for c in ["lifetime_average_rank", "peak_rank", "weeks_on_chart", "weeks_in_top10"]:
        diff = (both[c].astype(float) - both[c + "_src"].astype(float)).abs().max()
        check(f"{c}_matches_source", "chart_performance", diff < 1e-9, float(diff), "<1e-9")
    check("weeks_sum_equals_clean_rows", "chart_performance",
          int(perf["weeks_on_chart"].sum()) == len(b.clean(raw)),
          int(perf["weeks_on_chart"].sum()), len(b.clean(raw)))
    check("no_null_scores", "chart_performance", perf[VARS].notna().all().all(), int(perf[VARS].isna().sum().sum()), 0)
    check("negative_chart_score_pairs", "chart_performance", True, int((perf["chart_score"].astype(float) < 0).sum()),
          "info", "expected when avg rank > 101 (Top-200 chart)")
    for mk, n in perf.groupby("market").size().items():
        check("pairs_by_market", mk, True, int(n), "info")

    (ROOT / "logs").mkdir(exist_ok=True)
    pd.DataFrame(log).to_csv(ROOT / "logs/chart_validation_log.csv", index=False, encoding="utf-8-sig")

    # --- descriptive statistics per market ---
    rows = []
    p = perf.copy()
    for v in VARS:
        p[v] = p[v].astype(float)
    for mk in list(b.MARKETS) + ["ALL"]:
        sub = p if mk == "ALL" else p[p["market"] == mk]
        for v in VARS:
            s = sub[v]
            rows.append(dict(market=mk, variable=v, n=len(s), mean=s.mean(), std=s.std(),
                             min=s.min(), q1=s.quantile(.25), median=s.median(),
                             q3=s.quantile(.75), max=s.max()))
    out = pd.DataFrame(rows).round(4)
    (ROOT / "reports/report3").mkdir(parents=True, exist_ok=True)
    out.to_csv(ROOT / "reports/report3/chart_statistics.csv", index=False, encoding="utf-8-sig")

    res = pd.DataFrame(log)
    print(res[res.status == "FAIL"].to_string() if (res.status == "FAIL").any() else "ALL CHECKS PASS")
    print(f"{(res.status == 'PASS').sum()} pass / {(res.status == 'FAIL').sum()} fail")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["supabase", "csv"], default="supabase")
    main(ap.parse_args().source)
