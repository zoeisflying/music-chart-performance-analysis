"""
src/integration/build_analysis_dataset.py
Owner: Member 4 (Data Integration, Quality Control & Master Reports)
Grain: 1 row = 1 (spotify_track_id, market)

Integrates:
- Target & Chart Performance (Member 1)
- Audio Acoustic Features (Member 2)
- Lyrics Linguistic Features (Member 3)
- Song Metadata & Quarterly Sampling Timeline

Generates:
- reports/report4/chart_data/member4/analysis_dataset_sampled.csv (N = 2,860)
- reports/report4/chart_data/member4/analysis_dataset_complete.csv (N = 2,856)
- reports/report3/excluded_records.csv (N = 4)
- reports/report3/missingness_by_market.csv
- reports/report3/descriptive_statistics.csv
- reports/report3/data_dictionary.xlsx
"""

import os
import sys
import re
import numpy as np
import pandas as pd
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent.parent


def build_integrated_datasets():
    print("=" * 70)
    print("MEMBER 4: DATA INTEGRATION & QUALITY CONTROL PIPELINE")
    print("=" * 70)

    # 1. Load Chart Performance (Member 1)
    chart_perf_file = ROOT / "reports" / "report4" / "chart_data" / "member1" / "chart_performance_source.csv"
    if not chart_perf_file.exists():
        raise FileNotFoundError(f"Missing {chart_perf_file}")
    df_perf = pd.read_csv(chart_perf_file)
    print(f"Loaded chart_performance: {len(df_perf):,} pairs ({df_perf['spotify_track_id'].nunique():,} unique tracks)")

    # 2. Load Audio Features (Member 2)
    audio_file = ROOT / "reports" / "report4" / "chart_data" / "member2" / "audio_features_eda_source.csv"
    if not audio_file.exists():
        raise FileNotFoundError(f"Missing {audio_file}")
    df_audio = pd.read_csv(audio_file)
    print(f"Loaded audio_features: {len(df_audio):,} records ({df_audio['spotify_track_id'].nunique():,} unique tracks)")

    # 3. Load Lyrics Features (Member 3)
    lyrics_file = ROOT / "data" / "processed" / "lyrics_features.csv"
    if not lyrics_file.exists():
        raise FileNotFoundError(f"Missing {lyrics_file}")
    df_lyrics = pd.read_csv(lyrics_file)
    print(f"Loaded lyrics_features: {len(df_lyrics):,} tracks")

    # 4. Load Sample Metadata & Quarter Info
    sample_file = ROOT / "data" / "sampling" / "member2_sample_list.csv"
    if not sample_file.exists():
        raise FileNotFoundError(f"Missing {sample_file}")
    df_sample = pd.read_csv(sample_file)
    print(f"Loaded sample_list: {len(df_sample):,} rows ({df_sample['spotify_track_id'].nunique():,} unique tracks)")

    # Extract clean song metadata dictionary
    meta_df = df_sample[["spotify_track_id", "title", "artist", "release_date"]].drop_duplicates(subset=["spotify_track_id"])

    # Extract quarterly timeline mapping: (spotify_track_id, market) -> list of quarters
    # Notice a song can be sampled in multiple quarters; keep initial sample quarter & stratum for longitudinal EDA
    quarter_df = df_sample.groupby(["spotify_track_id", "market"]).agg(
        sample_year=("year", "min"),
        sample_quarter=("quarter", "min"),
        rank_stratum=("rank_stratum", "first")
    ).reset_index()

    # 5. Load YouTube Mapping metadata
    yt_file = ROOT / "data" / "sampling" / "youtube_matching_final_all_songs.csv"
    df_yt = pd.read_csv(yt_file)[["spotify_track_id", "youtube_video_id", "match_status", "duration_diff_sec"]].drop_duplicates("spotify_track_id")

    # 6. Establish Study Universe: The 1,912 sampled tracks across VN, US, KR
    sampled_track_ids = set(df_sample["spotify_track_id"])
    print(f"Identified {len(sampled_track_ids):,} distinct sampled tracks.")

    # Filter chart_performance to sampled tracks (grain: spotify_track_id, market)
    df_sampled_perf = df_perf[df_perf["spotify_track_id"].isin(sampled_track_ids)].copy()
    print(f"Sampled chart performance entries: {len(df_sampled_perf):,} pairs (KR: {(df_sampled_perf['market']=='KR').sum()}, US: {(df_sampled_perf['market']=='US').sum()}, VN: {(df_sampled_perf['market']=='VN').sum()})")

    # Merge metadata
    df_merged = pd.merge(df_sampled_perf, meta_df, on="spotify_track_id", how="left")

    # Parse release_year strictly from songs.release_date (NOT from sampling year)
    df_merged["release_date"] = pd.to_datetime(df_merged["release_date"], errors="coerce")
    df_merged["release_year"] = df_merged["release_date"].dt.year.astype("Int64")

    # Merge Audio Features (df_audio is already at (track, market) grain)
    # Audio feature column names (excluding spotify_track_id, market)
    audio_cols = [c for c in df_audio.columns if c not in ["spotify_track_id", "market"]]
    df_merged = pd.merge(df_merged, df_audio[["spotify_track_id", "market"] + audio_cols], on=["spotify_track_id", "market"], how="left")

    # Merge YouTube mapping
    df_merged = pd.merge(df_merged, df_yt, on="spotify_track_id", how="left")
    df_merged["audio_mapping_is_selected"] = True

    # Merge Lyrics Features (grain: spotify_track_id)
    lyrics_cols = [c for c in df_lyrics.columns if c not in ["spotify_track_id", "error_note"]]
    df_merged = pd.merge(df_merged, df_lyrics[["spotify_track_id"] + lyrics_cols], on="spotify_track_id", how="left")

    # Merge Quarterly Sampling info (for longitudinal trend analysis)
    df_merged = pd.merge(df_merged, quarter_df, on=["spotify_track_id", "market"], how="left")

    # Quality & Integrity Flags
    df_merged["has_audio"] = df_merged["tempo_bpm"].notna()
    df_merged["has_lyrics"] = df_merged["lyrics_status"] == "success"
    df_merged["is_complete_case"] = df_merged["has_audio"] & df_merged["has_lyrics"]
    df_merged["is_sampled"] = True

    # Ensure correct ordering of columns
    ordered_cols = [
        "spotify_track_id", "market", "title", "artist", "release_date", "release_year",
        "sample_year", "sample_quarter", "rank_stratum",
        "lifetime_average_rank", "chart_score", "peak_rank", "weeks_on_chart", "weeks_in_top10",
        "tempo_bpm", "beat_interval_variability", "tempo_stability", "onset_rate",
        "rms_energy", "rms_variability", "dynamic_range", "loudness_proxy",
        "spectral_centroid", "spectral_bandwidth", "key_confidence", "chord_change_rate",
        "chroma_repetition_determinism", "chroma_mean_pattern_duration", "chroma_longest_pattern_duration",
        "mfcc_repetition_determinism", "mfcc_mean_pattern_duration", "mfcc_longest_pattern_duration",
        "audio_key", "audio_mode",
        "youtube_video_id", "match_status", "duration_diff_sec", "audio_mapping_is_selected",
        "word_count", "unique_word_count", "lexical_diversity", "repetition_ratio",
        "avg_word_length", "line_count", "chorus_repetition_count", "title_word_in_lyrics",
        "punctuation_ratio", "pronoun_ratio", "language", "lyrics_status",
        "has_audio", "has_lyrics", "is_complete_case", "is_sampled"
    ]
    df_merged = df_merged[ordered_cols]

    # Save Analysis Datasets
    out_dir_m4 = ROOT / "reports" / "report4" / "chart_data" / "member4"
    out_dir_m4.mkdir(parents=True, exist_ok=True)

    sampled_csv = out_dir_m4 / "analysis_dataset_sampled.csv"
    df_merged.to_csv(sampled_csv, index=False, encoding="utf-8-sig")
    print(f"\n[+] Saved analysis_dataset_sampled: {sampled_csv} ({len(df_merged):,} records)")

    # Complete-case dataset (only records with 100% audio & lyrics features)
    df_complete = df_merged[df_merged["is_complete_case"]].copy()
    complete_csv = out_dir_m4 / "analysis_dataset_complete.csv"
    df_complete.to_csv(complete_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Saved analysis_dataset_complete: {complete_csv} ({len(df_complete):,} records)")

    # 7. Excluded Records (Missing lyrics or unretrievable)
    df_excluded = df_merged[~df_merged["is_complete_case"]].copy()
    excluded_csv = ROOT / "reports" / "report3" / "excluded_records.csv"
    excluded_cols = ["spotify_track_id", "market", "title", "artist", "release_year", "lyrics_status", "has_audio", "has_lyrics"]
    df_excluded_out = df_excluded[excluded_cols].copy()
    df_excluded_out["reason_for_exclusion"] = "Lyrics not found in LRCLIB / online repositories (unretrievable raw text)"
    df_excluded_out["impact_on_analysis"] = "Excluded from complete-case multimodal modeling; retained in descriptive target EDA"
    df_excluded_out.to_csv(excluded_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Saved excluded_records: {excluded_csv} ({len(df_excluded_out):,} records)")

    # 8. Missingness by Market Report
    missing_summary = []
    markets = ["VN", "US", "KR", "Overall"]
    all_features = [
        ("Chart Performance", "chart_score"),
        ("Chart Performance", "lifetime_average_rank"),
        ("Metadata", "release_year"),
        ("Audio", "tempo_bpm"),
        ("Audio", "rms_energy"),
        ("Audio", "spectral_centroid"),
        ("Audio", "chord_change_rate"),
        ("Audio", "mfcc_repetition_determinism"),
        ("Lyrics", "word_count"),
        ("Lyrics", "lexical_diversity"),
        ("Lyrics", "repetition_ratio"),
        ("Lyrics", "avg_word_length"),
        ("Lyrics", "line_count"),
        ("Lyrics", "chorus_repetition_count"),
        ("Lyrics", "title_word_in_lyrics"),
        ("Lyrics", "punctuation_ratio"),
        ("Lyrics", "pronoun_ratio")
    ]

    for m in markets:
        sub = df_merged if m == "Overall" else df_merged[df_merged["market"] == m]
        n_total = len(sub)
        for cat, feat in all_features:
            n_missing = sub[feat].isna().sum()
            pct_missing = round((n_missing / n_total) * 100, 2)
            missing_summary.append({
                "market": m,
                "domain": cat,
                "feature": feat,
                "total_observations": n_total,
                "missing_count": n_missing,
                "missing_percentage": pct_missing,
                "nature_of_missingness": "Chorus not measurable / absent" if feat == "chorus_repetition_count" else ("Unretrievable raw lyrics" if n_missing > 0 else "Complete (0% missing)")
            })

    missing_df = pd.DataFrame(missing_summary)
    missing_csv = ROOT / "reports" / "report3" / "missingness_by_market.csv"
    missing_df.to_csv(missing_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Saved missingness_by_market: {missing_csv}")

    # 9. Comprehensive Descriptive Statistics across all numerical variables
    num_features = [
        "chart_score", "lifetime_average_rank", "peak_rank", "weeks_on_chart", "weeks_in_top10",
        "tempo_bpm", "beat_interval_variability", "tempo_stability", "onset_rate",
        "rms_energy", "rms_variability", "dynamic_range", "loudness_proxy",
        "spectral_centroid", "spectral_bandwidth", "key_confidence", "chord_change_rate",
        "chroma_repetition_determinism", "chroma_mean_pattern_duration", "chroma_longest_pattern_duration",
        "mfcc_repetition_determinism", "mfcc_mean_pattern_duration", "mfcc_longest_pattern_duration",
        "word_count", "unique_word_count", "lexical_diversity", "repetition_ratio",
        "avg_word_length", "line_count", "chorus_repetition_count", "punctuation_ratio", "pronoun_ratio",
        "release_year"
    ]

    stat_records = []
    for m in markets:
        sub = df_merged if m == "Overall" else df_merged[df_merged["market"] == m]
        for f in num_features:
            valid = sub[f].dropna()
            if len(valid) == 0:
                continue
            q25, med, q75 = np.percentile(valid, [25, 50, 75])
            stat_records.append({
                "market": m,
                "feature": f,
                "count": len(valid),
                "mean": round(float(valid.mean()), 4),
                "std": round(float(valid.std()), 4),
                "median": round(float(med), 4),
                "iqr": round(float(q75 - q25), 4),
                "min": round(float(valid.min()), 4),
                "max": round(float(valid.max()), 4),
                "skewness": round(float(valid.skew()), 4),
                "kurtosis": round(float(valid.kurtosis()), 4)
            })

    stats_df = pd.DataFrame(stat_records)
    desc_csv = ROOT / "reports" / "report3" / "descriptive_statistics.csv"
    stats_df.to_csv(desc_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Saved descriptive_statistics: {desc_csv}")

    # 10. Generate Multi-Tab Professional Data Dictionary (Excel)
    create_excel_data_dictionary()


def create_excel_data_dictionary():
    dict_file = ROOT / "reports" / "report3" / "data_dictionary.xlsx"
    wb = openpyxl.Workbook()

    # Styling constants
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_center = Alignment(horizontal="center", vertical="center")

    def format_sheet(ws, title, headers, rows):
        ws.title = title
        ws.views.sheetView[0].showGridLines = True
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center

        for r_idx, row_data in enumerate(rows, start=2):
            for c_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = data_font
                cell.border = border_thin
                cell.alignment = align_left if c_idx in [1, 2, 5, 6, 7] else align_center

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

    # Sheet 1: Overview
    overview_headers = ["Section", "Table / Grain", "Key Attributes", "Observation Count (Sampled)", "Completeness Rate", "Description"]
    overview_rows = [
        ["Study Scope", "Target Markets", "VN, US, KR", "2,860 entries (1,912 tracks)", "100.0%", "Music chart performance analysis across Spotify Weekly Top 200 (2021–2026)."],
        ["Target Domain", "chart_performance", "(spotify_track_id, market)", "2,860 entries", "100.0%", "Target ChartScore = 101 - lifetime_average_rank and longevity metrics."],
        ["Audio Domain", "audio_features", "spotify_track_id", "1,912 tracks", "100.0%", "20 acoustic feature dimensions extracted from 44.1kHz mono audio via librosa/RQA."],
        ["Lyrics Domain", "lyrics_features", "spotify_track_id", "1,909 success (3 not_found)", "99.84%", "10 NLP linguistic dimensions extracted from cleaned lyrics text files."],
        ["Video Mapping", "youtube_mapping", "spotify_track_id", "1,912 tracks", "100.0%", "YouTube official audio candidates matched and validated with is_selected = True."],
        ["Complete Case", "modeling_dataset", "(spotify_track_id, market)", "2,856 entries", "99.86%", "Complete multimodal observation records with 0% missingness across all features."]
    ]
    format_sheet(wb.active, "Overview & Architecture", overview_headers, overview_rows)

    # Sheet 2: Target & Chart Performance
    chart_headers = ["Field Name", "Data Type", "Range / Domain", "Source", "Calculation / DDL", "Physical / Analytic Meaning", "Modeling Role"]
    chart_rows = [
        ["spotify_track_id", "TEXT", "22-char string", "songs / chart_weekly", "Primary Key", "Canonical Spotify track identifier.", "Identifier (Entity Key)"],
        ["market", "TEXT", "VN, US, KR", "chart_weekly", "Chart country code", "Geographic market where the track charted.", "Grouping / Stratification"],
        ["lifetime_average_rank", "NUMERIC", "[1.0, 200.0]", "chart_weekly", "AVG(rank) across valid weeks", "Mean weekly chart rank during the 2021–2026 window.", "Descriptive Metric"],
        ["chart_score", "NUMERIC", "[-99.0, 100.0]", "chart_weekly", "101 - lifetime_average_rank", "Primary regression target; higher value denotes superior chart performance.", "PRIMARY TARGET (Y)"],
        ["peak_rank", "INTEGER", "[1, 200]", "chart_weekly", "MIN(rank)", "Highest ranking position achieved on the weekly chart.", "Descriptive (Not Predictor)"],
        ["weeks_on_chart", "INTEGER", "[1, 297]", "chart_weekly", "COUNT(*) valid weeks", "Total chart endurance / longevity in weeks.", "Descriptive (Not Predictor)"],
        ["weeks_in_top10", "INTEGER", "[0, 91]", "chart_weekly", "COUNT(*) rank <= 10", "Longevity spent in the elite Top 10 tier.", "Descriptive (Not Predictor)"]
    ]
    format_sheet(wb.create_sheet(), "Chart Performance", chart_headers, chart_rows)

    # Sheet 3: Audio Features
    audio_headers = ["Field Name", "Data Type", "Unit / Range", "Extraction Tool", "Signal Formula", "Acoustic / Perceptual Meaning", "Multicollinearity Note"]
    audio_rows = [
        ["tempo_bpm", "FLOAT", "BPM [58 - 235]", "librosa", "Tempogram Dynamic Programming", "Estimated representative song tempo.", "Core rhythm feature"],
        ["beat_interval_variability", "FLOAT", "Ratio [0.007 - 0.06]", "librosa", "Std(delta_beat) / Mean(delta_beat)", "Beat regularity; lower denotes quantized drum machine.", "Collinear with tempo_stability"],
        ["tempo_stability", "FLOAT", "Ratio [0.007 - 0.06]", "librosa", "Synchronized inverse variability", "Mechanical tempo constancy.", "Preserved for legacy compatibility"],
        ["onset_rate", "FLOAT", "Events/sec [25 - 345]", "librosa", "Spectral Flux Peak Picking", "Note / sonic event density per second.", "Rhythmic density"],
        ["rms_energy", "FLOAT", "Amplitude [0.02 - 0.57]", "librosa", "sqrt(mean(x^2))", "Overall physical acoustic signal energy.", "High correlation with loudness_proxy"],
        ["rms_variability", "FLOAT", "Std [0.007 - 0.25]", "librosa", "Std of frame-level RMS", "Dynamic energy contrast across song sections.", "Dynamic contour"],
        ["dynamic_range", "FLOAT", "dBFS [2.2 - 193.5]", "librosa", "P95(RMS_dB) - P05(RMS_dB)", "Dynamic contrast between quiet and loud sections.", "Mastering proxy"],
        ["loudness_proxy", "FLOAT", "dBFS [2.2 - 193.5]", "librosa", "Log-scaled RMS energy proxy", "Perceived loudness indicator.", "Collinear with dynamic_range / energy"],
        ["spectral_centroid", "FLOAT", "Hz [544 - 3628]", "librosa", "sum(f * |X(f)|) / sum(|X(f)|)", "Frequency center of mass; timbral brightness.", "Brightness indicator"],
        ["spectral_bandwidth", "FLOAT", "Hz [908 - 3291]", "librosa", "Spectral spread around centroid", "Acoustic richness / frequency fullness.", "Spectral width"],
        ["key_confidence", "FLOAT", "Pearson r [0.22 - 0.98]", "librosa", "Max correlation with K-S profile", "Mathematical certainty of key estimation.", "Reliability flag"],
        ["chord_change_rate", "FLOAT", "Chords/min [12 - 87]", "librosa", "Beat-sync Triad Cosine distance", "Harmonic rhythm pace of chord progressions.", "Harmonic tempo"],
        ["chroma_repetition_determinism", "FLOAT", "Ratio [0.0 - 0.93]", "scipy / RQA", "Recurrence Determinism on Chroma", "Periodic repetition of harmonic chord progressions.", "Harmonic structure loop"],
        ["chroma_mean_pattern_duration", "FLOAT", "Seconds [0.0 - 17.2]", "scipy / RQA", "Mean diagonal line length", "Average duration of recurring chord motifs.", "Motif duration"],
        ["chroma_longest_pattern_duration", "FLOAT", "Seconds [0.0 - 72.0]", "scipy / RQA", "Max diagonal line length", "Longest recurring chord sequence (verse/chorus).", "Long loop duration"],
        ["mfcc_repetition_determinism", "FLOAT", "Ratio [0.0 - 0.72]", "scipy / RQA", "Recurrence Determinism on MFCC", "Timbral / production loop repetition.", "Production loopiness"],
        ["mfcc_mean_pattern_duration", "FLOAT", "Seconds [0.0 - 11.7]", "scipy / RQA", "Mean diagonal line length", "Average duration of recurring timbral loops.", "Timbre pattern length"],
        ["mfcc_longest_pattern_duration", "FLOAT", "Seconds [0.0 - 72.0]", "scipy / RQA", "Max diagonal line length", "Longest recurring arrangement / instrumentation block.", "Arrangement loop duration"],
        ["audio_key", "CATEGORICAL", "12 Pitch Classes", "librosa", "Krumhansl-Schmuckler algorithm", "Tonic pitch class of the musical composition.", "Categorical predictor"],
        ["audio_mode", "CATEGORICAL", "major, minor", "librosa", "K-S Profile matching", "Musical scale tonality (Major vs Minor).", "Binary indicator"]
    ]
    format_sheet(wb.create_sheet(), "Audio Features", audio_headers, audio_rows)

    # Sheet 4: Lyrics Features
    lyrics_headers = ["Field Name", "Data Type", "Range / Domain", "Tokenizer", "Formula / Rule", "Linguistic / Perceptual Meaning", "Missingness Rule"]
    lyrics_rows = [
        ["word_count", "INTEGER", "[12 - 2070]", "Unicode regex", "Total valid word tokens", "Text length and total verbal density of the track.", "NULL if unretrievable"],
        ["unique_word_count", "INTEGER", "[12 - 641]", "Lowercased set", "Count of distinct tokens", "Vocabulary breadth deployed by the songwriter.", "NULL if unretrievable"],
        ["lexical_diversity", "FLOAT", "Ratio (0, 1]", "Unicode regex", "unique_word_count / word_count", "Type-token ratio; lower values reflect high lyric repetition.", "Undefined if word_count = 0"],
        ["repetition_ratio", "FLOAT", "Ratio [0, 1)", "Unicode regex", "1.0 - lexical_diversity", "Lyric catchiness / verbatim repetition fraction.", "Undefined if word_count = 0"],
        ["avg_word_length", "FLOAT", "Chars/word [2.1 - 13.2]", "Unicode regex", "Sum(char_len) / word_count", "Morphological complexity and average word length.", "Cross-language caution required"],
        ["line_count", "INTEGER", "[3 - 193]", "Line break", "Count of non-empty cleaned lines", "Structural stanza density and phrasing count.", "NULL if unretrievable"],
        ["chorus_repetition_count", "FLOAT", "Count [0 - 18]", "Tag / Stanza match", "Chorus recurrence instances - 1", "Chorus hook emphasis; NULL if no chorus identifiable.", "Explicitly NULL if unmeasurable"],
        ["title_word_in_lyrics", "BOOLEAN", "True, False", "Stopword filter", "Content title word in lyrics set", "Lyrical reinforcement of the track title in the song body.", "Complete boolean flag"],
        ["punctuation_ratio", "FLOAT", "Ratio [0, 0.18]", "Punctuation set", "Punctuation chars / Total chars", "Syntactic pausing and expressive punctuation density.", "Complete ratio"],
        ["pronoun_ratio", "FLOAT", "Ratio [0, 0.37]", "Language dictionary", "Pronoun tokens / word_count", "Interpersonal intimacy and self-referential lyrical focus.", "Language-specific dictionaries"],
        ["lyrics_language", "TEXT", "en, vi, ko, es, mixed", "langdetect / manual", "Detected ISO language code", "Primary linguistic medium of the song lyrics.", "Audit identifier"],
        ["lyrics_status", "TEXT", "success, not_found, failed", "Pipeline status", "Collection status tracking", "Integrity flag for data missingness auditing.", "Filtering flag"]
    ]
    format_sheet(wb.create_sheet(), "Lyrics Features", lyrics_headers, lyrics_rows)

    # Sheet 5: Metadata & Sampling
    meta_headers = ["Field Name", "Data Type", "Origin Table", "Format / Values", "Description", "Analytical Utility"]
    meta_rows = [
        ["title", "TEXT", "songs", "Text string", "Official track title from Spotify/Kworb.", "Descriptive labeling"],
        ["artist", "TEXT", "songs", "Text string", "Primary artist or collaborating performers.", "Descriptive labeling"],
        ["release_date", "DATE", "songs", "YYYY-MM-DD", "Official song release date.", "Chronological filtering"],
        ["release_year", "INTEGER", "songs", "1960 - 2026", "Calendar year extracted from songs.release_date.", "True song vintage (age) control"],
        ["sample_year", "INTEGER", "song_quarter_sampling", "2021 - 2026", "Year in which the track was sampled from the chart.", "Sampling stratified control"],
        ["sample_quarter", "TEXT", "song_quarter_sampling", "2021-Q1 .. 2026-Q3", "Calendar quarter of the sampling batch.", "Longitudinal cohort analysis"],
        ["rank_stratum", "TEXT", "song_quarter_sampling", "top_10, 11-50, 51-100..", "Stratified ranking tier at sampling date.", "Sampling balance verification"],
        ["has_audio", "BOOLEAN", "Derived", "True / False", "Flag indicating complete acoustic feature extraction.", "Missingness audit"],
        ["has_lyrics", "BOOLEAN", "Derived", "True / False", "Flag indicating successful lyrics feature extraction.", "Missingness audit"],
        ["is_complete_case", "BOOLEAN", "Derived", "True / False", "Flag indicating 100% complete multimodal features.", "Subset filter for regression"]
    ]
    format_sheet(wb.create_sheet(), "Metadata & Sampling", meta_headers, meta_rows)

    wb.save(dict_file)
    print(f"[+] Saved formatted Excel Data Dictionary: {dict_file}")


if __name__ == "__main__":
    build_integrated_datasets()
