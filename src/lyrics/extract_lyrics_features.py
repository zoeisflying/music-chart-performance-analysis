"""
src/lyrics/extract_lyrics_features.py
Owner: Member 3 (Lyrics Feature Engineering & NLP Analytics)
Grain: 1 row per spotify_track_id (N = 1,912 tracks).

Extracts 10 standardized NLP features from raw lyrics:
- word_count
- unique_word_count
- lexical_diversity (unique / total)
- repetition_ratio (1 - lexical_diversity)
- avg_word_length (char / word)
- line_count
- chorus_repetition_count (repeats of detected chorus; None if not identifiable)
- title_word_in_lyrics (boolean: content title word in lyrics)
- punctuation_ratio (punctuation / total characters)
- pronoun_ratio (pronouns / word_count)
- language
- lyrics_status (success, not_found, failed)
"""

import os
import sys
import re
import string
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

CHORUS_TAG_PATTERN = re.compile(
    r"^\s*\[(?:chorus|pre-chorus|post-chorus|hook|refrain|điệp\s*khúc|후렴)[^\]]*\]\s*$",
    re.IGNORECASE
)
ALL_SECTION_TAG_PATTERN = re.compile(
    r"^\s*\[(?:verse|pre-chorus|chorus|post-chorus|bridge|intro|outro|hook|refrain|điệp\s*khúc|instrumental|interlude|break|part|spoken|후렴)[^\]]*\]\s*$",
    re.IGNORECASE
)
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
PUNCTUATION_CHARS = set(string.punctuation + ".,!?;:\"'()[]-–—…/„“”‘’`~«»")


def load_rules():
    rule_file = ROOT / "src" / "lyrics" / "language_rules.yaml"
    if rule_file.exists():
        with open(rule_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"pronouns": {}, "title_stopwords": {}}


def extract_track_lyrics_features(track_id, title, artist, language, lyrics_file_rel, rules):
    lyrics_path = ROOT / lyrics_file_rel if isinstance(lyrics_file_rel, str) and lyrics_file_rel else None
    
    if not lyrics_path or not lyrics_path.exists():
        return {
            "spotify_track_id": track_id,
            "word_count": np.nan,
            "unique_word_count": np.nan,
            "lexical_diversity": np.nan,
            "repetition_ratio": np.nan,
            "avg_word_length": np.nan,
            "line_count": np.nan,
            "chorus_repetition_count": np.nan,
            "title_word_in_lyrics": False,
            "punctuation_ratio": np.nan,
            "pronoun_ratio": np.nan,
            "language": language or "unknown",
            "lyrics_status": "not_found",
            "error_note": "Lyrics file does not exist"
        }

    try:
        with open(lyrics_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read().strip()
    except Exception as e:
        return {
            "spotify_track_id": track_id,
            "word_count": np.nan,
            "unique_word_count": np.nan,
            "lexical_diversity": np.nan,
            "repetition_ratio": np.nan,
            "avg_word_length": np.nan,
            "line_count": np.nan,
            "chorus_repetition_count": np.nan,
            "title_word_in_lyrics": False,
            "punctuation_ratio": np.nan,
            "pronoun_ratio": np.nan,
            "language": language or "unknown",
            "lyrics_status": "failed",
            "error_note": f"Error reading file: {e}"
        }

    if not raw_text:
        return {
            "spotify_track_id": track_id,
            "word_count": np.nan,
            "unique_word_count": np.nan,
            "lexical_diversity": np.nan,
            "repetition_ratio": np.nan,
            "avg_word_length": np.nan,
            "line_count": 0,
            "chorus_repetition_count": np.nan,
            "title_word_in_lyrics": False,
            "punctuation_ratio": np.nan,
            "pronoun_ratio": np.nan,
            "language": language or "unknown",
            "lyrics_status": "failed",
            "error_note": "Empty lyrics file"
        }

    raw_lines = raw_text.splitlines()

    # 1. Detect chorus structure
    chorus_headers_count = 0
    for line in raw_lines:
        if CHORUS_TAG_PATTERN.match(line):
            chorus_headers_count += 1

    chorus_repetition_count = np.nan
    if chorus_headers_count > 0:
        chorus_repetition_count = chorus_headers_count - 1
    else:
        # Fallback: stanza repetition detection
        stanzas = [s.strip() for s in re.split(r"\n\s*\n", raw_text) if s.strip()]
        if len(stanzas) > 1:
            norm_stanzas = [re.sub(r"\s+", " ", s.lower()) for s in stanzas]
            from collections import Counter
            counts = Counter(norm_stanzas)
            max_repeat = max(counts.values())
            if max_repeat > 1:
                chorus_repetition_count = max_repeat - 1

    # 2. Clean lines: strip markdown, URLs, and section labels
    cleaned_lines = []
    for line in raw_lines:
        line_s = line.strip()
        if not line_s:
            continue
        if ALL_SECTION_TAG_PATTERN.match(line_s):
            continue
        line_s = MARKDOWN_LINK_PATTERN.sub(r"\1", line_s)
        line_s = URL_PATTERN.sub("", line_s).strip()
        if line_s:
            cleaned_lines.append(line_s)

    line_count = len(cleaned_lines)
    cleaned_full_text = "\n".join(cleaned_lines)

    if line_count == 0 or not cleaned_full_text:
        return {
            "spotify_track_id": track_id,
            "word_count": np.nan,
            "unique_word_count": np.nan,
            "lexical_diversity": np.nan,
            "repetition_ratio": np.nan,
            "avg_word_length": np.nan,
            "line_count": 0,
            "chorus_repetition_count": np.nan,
            "title_word_in_lyrics": False,
            "punctuation_ratio": np.nan,
            "pronoun_ratio": np.nan,
            "language": language or "unknown",
            "lyrics_status": "failed",
            "error_note": "No valid lyrics lines after section tag removal"
        }

    # 3. Punctuation ratio
    total_chars = len(cleaned_full_text)
    punct_chars = sum(1 for c in cleaned_full_text if c in PUNCTUATION_CHARS)
    punctuation_ratio = punct_chars / total_chars if total_chars > 0 else 0.0

    # 4. Tokenization
    lower_text = cleaned_full_text.lower()
    # Unicode word tokens
    tokens = re.findall(r"[^\W_]+", lower_text, re.UNICODE)
    word_count = len(tokens)

    if word_count == 0:
        return {
            "spotify_track_id": track_id,
            "word_count": 0,
            "unique_word_count": 0,
            "lexical_diversity": np.nan,
            "repetition_ratio": np.nan,
            "avg_word_length": np.nan,
            "line_count": line_count,
            "chorus_repetition_count": chorus_repetition_count,
            "title_word_in_lyrics": False,
            "punctuation_ratio": punctuation_ratio,
            "pronoun_ratio": np.nan,
            "language": language or "unknown",
            "lyrics_status": "success",
            "error_note": "No tokens extracted"
        }

    unique_tokens = set(tokens)
    unique_word_count = len(unique_tokens)
    lexical_diversity = unique_word_count / word_count
    repetition_ratio = 1.0 - lexical_diversity
    avg_word_length = sum(len(t) for t in tokens) / word_count

    # 5. Pronoun ratio
    lang_key = language if language in ["en", "vi", "ko"] else "en"
    pronoun_list = set(rules.get("pronouns", {}).get(lang_key, []))
    pronoun_count = sum(1 for t in tokens if t in pronoun_list)
    # Check multi-word pronouns for Vietnamese like "chúng ta"
    if lang_key == "vi":
        for multi_p in ["chúng ta", "chúng tôi", "chúng em", "chúng mình"]:
            pronoun_count += lower_text.count(multi_p)
    pronoun_ratio = pronoun_count / word_count

    # 6. Title word in lyrics
    title_stop = set(rules.get("title_stopwords", {}).get(lang_key, []))
    title_tokens = re.findall(r"[^\W_]+", (title or "").lower(), re.UNICODE)
    content_title_words = [t for t in title_tokens if t not in title_stop and len(t) > 1]
    
    title_word_in_lyrics = any(w in unique_tokens for w in content_title_words) if content_title_words else False

    return {
        "spotify_track_id": track_id,
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "lexical_diversity": round(lexical_diversity, 6),
        "repetition_ratio": round(repetition_ratio, 6),
        "avg_word_length": round(avg_word_length, 4),
        "line_count": line_count,
        "chorus_repetition_count": chorus_repetition_count if not np.isnan(chorus_repetition_count) else np.nan,
        "title_word_in_lyrics": title_word_in_lyrics,
        "punctuation_ratio": round(punctuation_ratio, 6),
        "pronoun_ratio": round(pronoun_ratio, 6),
        "language": language or "unknown",
        "lyrics_status": "success",
        "error_note": ""
    }


def main():
    print("=" * 60)
    print("MEMBER 3: LYRICS FEATURE EXTRACTION PIPELINE")
    print("=" * 60)

    rules = load_rules()
    status_file = ROOT / "data" / "processed" / "lyrics_status.csv"
    if not status_file.exists():
        raise FileNotFoundError(f"Missing {status_file}")

    status_df = pd.read_csv(status_file)
    print(f"Loaded {len(status_df)} tracks from {status_file.name}")

    features = []
    logs = []

    for _, row in status_df.iterrows():
        res = extract_track_lyrics_features(
            track_id=row["spotify_track_id"],
            title=row.get("title", ""),
            artist=row.get("artist", ""),
            language=row.get("language", ""),
            lyrics_file_rel=row.get("lyrics_file", ""),
            rules=rules
        )
        features.append(res)
        logs.append({
            "spotify_track_id": res["spotify_track_id"],
            "lyrics_status": res["lyrics_status"],
            "word_count": res["word_count"],
            "lexical_diversity": res["lexical_diversity"],
            "error_note": res.get("error_note", "")
        })

    feat_df = pd.DataFrame(features)
    log_df = pd.DataFrame(logs)

    # Save outputs
    out_csv = ROOT / "data" / "processed" / "lyrics_features.csv"
    feat_df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"Saved extracted features: {out_csv} ({len(feat_df)} rows)")

    log_path = ROOT / "logs" / "lyrics_extraction_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"Saved extraction log: {log_path}")

    # Generate Inventory
    inv_path = ROOT / "reports" / "report3" / "lyrics_inventory.csv"
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge with market from audio / sample list for market-level inventory
    sample_path = ROOT / "data" / "sampling" / "member2_sample_list.csv"
    if sample_path.exists():
        sdf = pd.read_csv(sample_path)[["spotify_track_id", "market"]].drop_duplicates()
        m_df = pd.merge(sdf, feat_df, on="spotify_track_id", how="left")
        inv_summary = []
        for mkt, grp in m_df.groupby("market"):
            inv_summary.append({
                "market": mkt,
                "total_chart_entries": len(grp),
                "unique_tracks": grp["spotify_track_id"].nunique(),
                "lyrics_success": (grp["lyrics_status"] == "success").sum(),
                "lyrics_not_found": (grp["lyrics_status"] == "not_found").sum(),
                "success_rate_pct": round(((grp["lyrics_status"] == "success").sum() / len(grp)) * 100, 2),
                "mean_word_count": round(grp["word_count"].mean(), 1),
                "mean_lexical_diversity": round(grp["lexical_diversity"].mean(), 4)
            })
        inv_summary.append({
            "market": "Overall",
            "total_chart_entries": len(m_df),
            "unique_tracks": m_df["spotify_track_id"].nunique(),
            "lyrics_success": (m_df["lyrics_status"] == "success").sum(),
            "lyrics_not_found": (m_df["lyrics_status"] == "not_found").sum(),
            "success_rate_pct": round(((m_df["lyrics_status"] == "success").sum() / len(m_df)) * 100, 2),
            "mean_word_count": round(m_df["word_count"].mean(), 1),
            "mean_lexical_diversity": round(m_df["lexical_diversity"].mean(), 4)
        })
        pd.DataFrame(inv_summary).to_csv(inv_path, index=False, encoding="utf-8-sig")
        print(f"Saved lyrics inventory: {inv_path}")

    # Generate descriptive statistics
    stats_path = ROOT / "reports" / "report3" / "lyrics_statistics.csv"
    numeric_cols = [
        "word_count", "unique_word_count", "lexical_diversity", "repetition_ratio",
        "avg_word_length", "line_count", "chorus_repetition_count", "punctuation_ratio", "pronoun_ratio"
    ]
    stat_rows = []
    if "m_df" in locals():
        for mkt, grp in list(m_df.groupby("market")) + [("Overall", m_df)]:
            for col in numeric_cols:
                valid = grp[col].dropna()
                if len(valid) == 0:
                    continue
                q25, med, q75 = np.percentile(valid, [25, 50, 75])
                stat_rows.append({
                    "market": mkt,
                    "feature": col,
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
        pd.DataFrame(stat_rows).to_csv(stats_path, index=False, encoding="utf-8-sig")
        print(f"Saved lyrics statistics: {stats_path}")

    print("Lyrics feature extraction completed successfully!")


if __name__ == "__main__":
    main()
