"""
src/lyrics/validate_lyrics_features.py
Owner: Member 3
Validates extracted lyrics features and logs audit results.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def main():
    feat_path = ROOT / "data" / "processed" / "lyrics_features.csv"
    if not feat_path.exists():
        print(f"Error: {feat_path} does not exist.")
        sys.exit(1)

    df = pd.read_csv(feat_path)
    print(f"Validating {len(df)} records in lyrics_features.csv...")

    checks = []

    def log_check(name, passed, detail):
        status = "PASS" if passed else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        print(f"[{status}] {name}: {detail}")

    # 1. Total rows
    log_check("total_tracks_count", len(df) == 1912, f"Total records = {len(df)} (expected 1912)")

    # 2. Primary key uniqueness
    dup_pk = df["spotify_track_id"].duplicated().sum()
    log_check("primary_key_unique", dup_pk == 0, f"Duplicates in spotify_track_id: {dup_pk}")

    # 3. Status distribution
    success_count = (df["lyrics_status"] == "success").sum()
    not_found_count = (df["lyrics_status"] == "not_found").sum()
    log_check("status_categories", success_count == 1909 and not_found_count == 3,
              f"Success: {success_count}, Not Found: {not_found_count}")

    # 4. Success cases have word_count > 0
    success_df = df[df["lyrics_status"] == "success"]
    valid_wc = (success_df["word_count"] > 0).all()
    log_check("success_word_count_positive", valid_wc, f"All success tracks have word_count > 0")

    # 5. lexical_diversity in (0, 1]
    valid_ld = ((success_df["lexical_diversity"] > 0) & (success_df["lexical_diversity"] <= 1.0)).all()
    log_check("lexical_diversity_range", valid_ld, f"All success tracks have lexical_diversity in (0, 1]")

    # 6. repetition_ratio = 1 - lexical_diversity
    diff = (success_df["repetition_ratio"] - (1.0 - success_df["lexical_diversity"])).abs()
    log_check("repetition_formula_exact", (diff < 1e-4).all(), f"repetition_ratio matches 1 - lexical_diversity")

    # 7. punctuation_ratio in [0, 1]
    valid_pr = ((success_df["punctuation_ratio"] >= 0) & (success_df["punctuation_ratio"] <= 1.0)).all()
    log_check("punctuation_ratio_range", valid_pr, f"All success tracks have punctuation_ratio in [0, 1]")

    # 8. Not found cases have NaN for features (not 0)
    nf_df = df[df["lyrics_status"] == "not_found"]
    nf_nan = nf_df["word_count"].isna().all() and nf_df["lexical_diversity"].isna().all()
    log_check("not_found_has_nulls_not_zero", nf_nan, f"Not found tracks have NULLs, not 0")

    # Summary
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    print(f"\nAudit complete: {pass_count}/{len(checks)} checks PASSED.")

if __name__ == "__main__":
    main()
