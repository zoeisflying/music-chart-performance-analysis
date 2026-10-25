"""
src/integration/validate_analysis_dataset.py
Owner: Member 4 (Data Integration, Quality Control & Master Reports)

Automated Quality Control & Validation Engine:
Validates data integrity, entity grains, relational constraints, mathematical formulas,
value ranges, missingness boundaries, and cross-source consistency.

Outputs audit log to:
logs/integration_validation_log.csv
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    print("=" * 70)
    print("MEMBER 4: COMPREHENSIVE INTEGRATION VALIDATION & AUDIT SUITE")
    print("=" * 70)

    sampled_csv = ROOT / "reports" / "report4" / "chart_data" / "member4" / "analysis_dataset_sampled.csv"
    complete_csv = ROOT / "reports" / "report4" / "chart_data" / "member4" / "analysis_dataset_complete.csv"
    excluded_csv = ROOT / "reports" / "report3" / "excluded_records.csv"

    if not sampled_csv.exists() or not complete_csv.exists() or not excluded_csv.exists():
        raise FileNotFoundError("Missing one or more required integration dataset files.")

    df_sampled = pd.read_csv(sampled_csv)
    df_complete = pd.read_csv(complete_csv)
    df_excluded = pd.read_csv(excluded_csv)

    logs = []

    def log_check(name, scope, passed, val, exp, note=""):
        status = "PASS" if passed else "FAIL"
        logs.append({
            "check_name": name,
            "scope": scope,
            "status": status,
            "actual_value": str(val),
            "expected_value": str(exp),
            "audit_note": note
        })
        print(f"[{status:4s}] {name:35s} | Actual: {str(val):18s} | Expected: {str(exp):18s} | {note}")

    # --- 1. Entity Grain & Row Count Preservation ---
    log_check("sampled_row_count", "analysis_dataset_sampled",
              len(df_sampled) == 2860, len(df_sampled), 2860, "Matches sampled chart entries (KR: 1020, US: 955, VN: 885)")

    log_check("complete_row_count", "analysis_dataset_complete",
              len(df_complete) == 2856, len(df_complete), 2856, "2860 - 4 excluded instrumental/missing lyrics records")

    log_check("excluded_row_count", "excluded_records",
              len(df_excluded) == 4, len(df_excluded), 4, "Exact 4 unretrievable lyrics tracks (all instrumental tracks)")

    # --- 2. Primary Key & Uniqueness ---
    dup_keys_sampled = int(df_sampled.duplicated(subset=["spotify_track_id", "market"]).sum())
    log_check("primary_key_uniqueness_sampled", "analysis_dataset_sampled",
              dup_keys_sampled == 0, dup_keys_sampled, 0, "No duplicate (spotify_track_id, market) in sampled dataset")

    dup_keys_complete = int(df_complete.duplicated(subset=["spotify_track_id", "market"]).sum())
    log_check("primary_key_uniqueness_complete", "analysis_dataset_complete",
              dup_keys_complete == 0, dup_keys_complete, 0, "No duplicate (spotify_track_id, market) in complete dataset")

    unique_tracks = df_sampled["spotify_track_id"].nunique()
    log_check("unique_tracks_count", "analysis_dataset_sampled",
              unique_tracks == 1912, unique_tracks, 1912, "Matches exact study sample size of 1,912 tracks")

    # --- 3. Market Distribution ---
    markets_valid = df_sampled["market"].isin(["VN", "US", "KR"]).all()
    log_check("market_domain_validity", "analysis_dataset_sampled",
              markets_valid, list(df_sampled["market"].unique()), "['KR', 'US', 'VN']", "Markets strictly in VN, US, KR")

    # --- 4. Chart Target & Mathematical Formulas ---
    diff_chart_score = (df_sampled["chart_score"] - (101.0 - df_sampled["lifetime_average_rank"])).abs().max()
    log_check("chart_score_formula_exact", "chart_performance",
              diff_chart_score < 1e-6, round(float(diff_chart_score), 9), "< 1e-6", "chart_score = 101 - lifetime_average_rank holds across all rows")

    peak_rank_valid = (df_sampled["peak_rank"].between(1, 200)).all()
    log_check("peak_rank_range", "chart_performance",
              peak_rank_valid, f"min={df_sampled['peak_rank'].min()}, max={df_sampled['peak_rank'].max()}", "[1, 200]", "Peak rank within weekly Top 200 boundary")

    weeks_on_chart_valid = (df_sampled["weeks_on_chart"] >= 1).all()
    log_check("weeks_on_chart_positive", "chart_performance",
              weeks_on_chart_valid, f"min={df_sampled['weeks_on_chart'].min()}", ">= 1", "Every charting song has at least 1 charting week")

    weeks_top10_valid = ((df_sampled["weeks_in_top10"] >= 0) & (df_sampled["weeks_in_top10"] <= df_sampled["weeks_on_chart"])).all()
    log_check("weeks_in_top10_le_weeks_on_chart", "chart_performance",
              weeks_top10_valid, "Valid", "True", "weeks_in_top10 is non-negative and <= weeks_on_chart")

    # --- 5. Metadata Integrity ---
    release_years_valid = df_sampled["release_year"].dropna().between(1950, 2026).all()
    log_check("release_year_range", "songs",
              release_years_valid, f"min={df_sampled['release_year'].min()}, max={df_sampled['release_year'].max()}", "[1950, 2026]", "Release year parsed from release_date (vintage control)")

    # --- 6. Audio Acoustic Feature Consistency ---
    audio_missing = int(df_sampled["tempo_bpm"].isna().sum())
    log_check("audio_features_missing_count", "audio_features",
              audio_missing == 0, audio_missing, 0, "Audio features are 100% complete across all 2,860 entries")

    tempo_valid = df_sampled["tempo_bpm"].between(40, 260).all()
    log_check("tempo_bpm_range", "audio_features",
              tempo_valid, f"min={df_sampled['tempo_bpm'].min():.1f}, max={df_sampled['tempo_bpm'].max():.1f}", "[40, 260]", "Valid BPM tempo range")

    energy_valid = (df_sampled["rms_energy"] > 0).all()
    log_check("rms_energy_positive", "audio_features",
              energy_valid, f"min={df_sampled['rms_energy'].min():.4f}", "> 0", "RMS energy strictly positive physical signal")

    centroid_valid = df_sampled["spectral_centroid"].between(400, 5000).all()
    log_check("spectral_centroid_range", "audio_features",
              centroid_valid, f"min={df_sampled['spectral_centroid'].min():.1f}, max={df_sampled['spectral_centroid'].max():.1f}", "[400, 5000]", "Spectral brightness centroid within human audible range")

    rqa_chroma_valid = df_sampled["chroma_repetition_determinism"].between(0, 1).all()
    log_check("rqa_chroma_det_range", "audio_features",
              rqa_chroma_valid, f"min={df_sampled['chroma_repetition_determinism'].min():.4f}, max={df_sampled['chroma_repetition_determinism'].max():.4f}", "[0, 1]", "Recurrence determinism ratio bounded in [0, 1]")

    # --- 7. YouTube Mapping Alignment ---
    yt_selected_all = (df_sampled["audio_mapping_is_selected"] == True).all()
    log_check("youtube_mapping_is_selected", "youtube_mapping",
              yt_selected_all, "All True", "True", "All audio features originate from verified selected YouTube candidates")

    # --- 8. Lyrics Feature Integrity (on Complete Case) ---
    wc_valid = (df_complete["word_count"] > 0).all()
    log_check("complete_word_count_positive", "lyrics_features",
              wc_valid, f"min={df_complete['word_count'].min()}", "> 0", "All complete case lyrics have word_count > 0")

    lex_div_valid = df_complete["lexical_diversity"].between(0.01, 1.0).all()
    log_check("complete_lexical_diversity_range", "lyrics_features",
              lex_div_valid, f"min={df_complete['lexical_diversity'].min():.4f}, max={df_complete['lexical_diversity'].max():.4f}", "(0, 1]", "Type-token ratio bounded within (0, 1]")

    rep_formula_valid = ((df_complete["repetition_ratio"] - (1.0 - df_complete["lexical_diversity"])).abs() < 1e-4).all()
    log_check("complete_repetition_ratio_formula", "lyrics_features",
              rep_formula_valid, "Valid", "True", "repetition_ratio = 1 - lexical_diversity strictly maintained")

    punct_valid = df_complete["punctuation_ratio"].between(0.0, 0.5).all()
    log_check("complete_punctuation_ratio_range", "lyrics_features",
              punct_valid, f"min={df_complete['punctuation_ratio'].min():.4f}, max={df_complete['punctuation_ratio'].max():.4f}", "[0, 0.5]", "Punctuation ratio within normal range")

    pronoun_valid = df_complete["pronoun_ratio"].between(0.0, 0.5).all()
    log_check("complete_pronoun_ratio_range", "lyrics_features",
              pronoun_valid, f"min={df_complete['pronoun_ratio'].min():.4f}, max={df_complete['pronoun_ratio'].max():.4f}", "[0, 0.5]", "Pronoun ratio bounded in [0, 0.5]")

    # --- 9. Missingness & Non-Zero Replacement Rules ---
    # Ensure unretrievable lyrics tracks have NaN in word_count and NOT 0
    excluded_ids = set(df_excluded["spotify_track_id"])
    excluded_in_sampled = df_sampled[df_sampled["spotify_track_id"].isin(excluded_ids)]
    no_zero_imputation = excluded_in_sampled["word_count"].isna().all()
    log_check("no_zero_imputation_policy", "data_preparation",
              no_zero_imputation, "All NaN", "NaN", "Unretrievable lyrics are NOT arbitrarily imputed with 0; preserved as missing")

    # --- 10. Write Audit Log ---
    log_df = pd.DataFrame(logs)
    log_path = ROOT / "logs" / "integration_validation_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"\n[+] Validation audit log saved: {log_path}")

    pass_count = (log_df["status"] == "PASS").sum()
    total_checks = len(log_df)
    print(f"\n======================================================================")
    print(f"AUDIT SUMMARY: {pass_count}/{total_checks} CHECKS PASSED ({pass_count/total_checks*100:.1f}%)")
    print(f"======================================================================")

    if pass_count < total_checks:
        sys.exit(1)


if __name__ == "__main__":
    main()
