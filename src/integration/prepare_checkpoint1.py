
import os
import json
import joblib
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler


# ==========================================
# 1. CAU HINH
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Khong tim thay thong tin Supabase trong .env")

TABLE_NAME = "view_clean_modeling_dataset"

RANDOM_STATE = 42
TEST_SIZE = 0.2

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. KET NOI VA TAI DU LIEU SUPABASE
# ==========================================

print("Dang ket noi Supabase...")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

all_rows = []
start = 0
page_size = 1000

while True:
    response = (
        sb.table(TABLE_NAME)
        .select("*")
        .range(start, start + page_size - 1)
        .execute()
    )

    rows = response.data
    all_rows.extend(rows)

    if len(rows) < page_size:
        break

    start += page_size

df = pd.DataFrame(all_rows)

print("Tai du lieu thanh cong:", len(df), "dong")


# ==========================================
# 3. KIEM TRA DU LIEU
# ==========================================

assert len(df) == 2098, (
    f"Expected 2098 rows, got {len(df)}"
)

assert df["spotify_track_id"].nunique() == 1912

assert not df.duplicated(
    ["spotify_track_id", "market"]
).any()

assert df["chart_score"].notna().all()

print("Kiem tra du lieu: PASS")


# ==========================================
# 4. XAC DINH FEATURE
# ==========================================

audio_features = [
    "tempo_bpm",
    "beat_interval_variability",
    "onset_rate",
    "rms_energy",
    "rms_variability",
    "dynamic_range",
    "spectral_centroid",
    "spectral_bandwidth",
    "duration_seconds",
    "duration_analyzed_seconds",
    "key_confidence",
    "chord_change_rate",
    "chroma_repetition_determinism",
    "chroma_mean_pattern_duration",
    "chroma_longest_pattern_duration",
    "mfcc_repetition_determinism",
    "mfcc_mean_pattern_duration",
    "mfcc_longest_pattern_duration"
]

lyrics_features = [
    "word_count",
    "unique_word_count",
    "lexical_diversity",
    "repetition_ratio",
    "avg_word_length",
    "line_count",
    "chorus_repetition_count",
    "punctuation_ratio",
    "pronoun_ratio"
]

numeric_features = (
    ["release_year"]
    + audio_features
    + lyrics_features
)

for col in numeric_features:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# ==========================================
# 5. GROUP TRAIN / TEST SPLIT
# ==========================================

print("\nDang chia Train/Test...")

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE
)

train_idx, test_idx = next(
    splitter.split(
        df,
        groups=df["spotify_track_id"]
    )
)

train_df = df.iloc[train_idx].copy()
test_df = df.iloc[test_idx].copy()

train_ids = set(train_df["spotify_track_id"])
test_ids = set(test_df["spotify_track_id"])

assert train_ids.isdisjoint(test_ids)

print("Train rows:", len(train_df))
print("Test rows:", len(test_df))
print("Train tracks:", len(train_ids))
print("Test tracks:", len(test_ids))


# ==========================================
# 6. TINH MEDIAN LYRICS THEO MARKET
# CHI SU DUNG TRAIN
# ==========================================

print("\nDang tinh lyrics market medians...")

market_medians = (
    train_df
    .groupby("market")[lyrics_features]
    .median()
)

if market_medians.isna().any().any():
    raise ValueError(
        "Co market/lyrics feature khong tinh duoc median"
    )

median_dict = {}

for market in market_medians.index:
    median_dict[market] = {
        col: float(market_medians.loc[market, col])
        for col in lyrics_features
    }

median_path = (
    OUTPUT_DIR / "lyrics_market_medians.json"
)

with open(median_path, "w", encoding="utf-8") as f:
    json.dump(
        median_dict,
        f,
        ensure_ascii=False,
        indent=4
    )

print("Da luu:", median_path)


# ==========================================
# 7. DIEN MISSING LYRICS
# SU DUNG MEDIAN TU TRAIN
# ==========================================

def fill_lyrics_missing(data):
    data = data.copy()

    for col in lyrics_features:
        median_by_market = {
            market: values[col]
            for market, values in median_dict.items()
        }

        missing_mask = data[col].isna()

        data.loc[missing_mask, col] = (
            data.loc[missing_mask, "market"]
            .map(median_by_market)
        )

    return data


train_df = fill_lyrics_missing(train_df)
test_df = fill_lyrics_missing(test_df)

assert train_df[lyrics_features].notna().all().all()
assert test_df[lyrics_features].notna().all().all()


# ==========================================
# 8. STANDARD SCALER
# FIT TRAIN ONLY
# ==========================================

print("\nDang StandardScaler...")

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(
    train_df[numeric_features]
)

X_test_scaled = scaler.transform(
    test_df[numeric_features]
)

scaled_train = pd.DataFrame(
    X_train_scaled,
    columns=numeric_features,
    index=train_df.index
)

scaled_test = pd.DataFrame(
    X_test_scaled,
    columns=numeric_features,
    index=test_df.index
)

print("Scaler da fit tren Train.")
print("Test chi duoc transform.")


# ==========================================
# 9. LUU KET QUA
# ==========================================

# Luu du lieu sau khi dien missing
train_df.to_csv(
    OUTPUT_DIR / "checkpoint1_train.csv",
    index=False
)

test_df.to_csv(
    OUTPUT_DIR / "checkpoint1_test.csv",
    index=False
)

# Luu du lieu da scale
scaled_train_output = pd.concat(
    [
        train_df[["spotify_track_id", "market", "chart_score"]],
        scaled_train
    ],
    axis=1
)

scaled_test_output = pd.concat(
    [
        test_df[["spotify_track_id", "market", "chart_score"]],
        scaled_test
    ],
    axis=1
)

scaled_train_output.to_csv(
    OUTPUT_DIR / "checkpoint1_train_scaled.csv",
    index=False
)

scaled_test_output.to_csv(
    OUTPUT_DIR / "checkpoint1_test_scaled.csv",
    index=False
)

# Luu Test Track IDs
test_track_ids_path = MODEL_DIR / "test_track_ids.json"

with open(test_track_ids_path, "w", encoding="utf-8") as f:
    json.dump(
        sorted(test_ids),
        f,
        ensure_ascii=False,
        indent=4
    )

# Luu scaler
joblib.dump(
    scaler,
    MODEL_DIR / "checkpoint1_scaler.joblib"
)


# ==========================================
# 10. TONG KET
# ==========================================

print("\n========== CHECKPOINT 1 ==========")

print("Tong rows:", len(df))
print("Train rows:", len(train_df))
print("Test rows:", len(test_df))

print("Train tracks:", len(train_ids))
print("Test tracks:", len(test_ids))

print(
    "Track overlap:",
    len(train_ids.intersection(test_ids))
)

print("Feature count:", len(numeric_features))

print("\nFiles da luu:")
print("- data/processed/checkpoint1_train.csv")
print("- data/processed/checkpoint1_test.csv")
print("- data/processed/checkpoint1_train_scaled.csv")
print("- data/processed/checkpoint1_test_scaled.csv")
print("- data/processed/lyrics_market_medians.json")
print("- models/test_track_ids.json")
print("- models/checkpoint1_scaler.joblib")

print("\nCHECKPOINT 1 PREPARATION COMPLETED!")
