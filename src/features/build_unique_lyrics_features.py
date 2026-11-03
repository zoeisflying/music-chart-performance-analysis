
import pandas as pd

# 1. Read recomputed lyrics features
df = pd.read_csv(
    "data/processed/lyrics_features_recomputed.csv"
)

# 2. Keep one row per Spotify track ID
df_unique = df.drop_duplicates(
    subset=["spotify_track_id"]
).copy()

# 3. Remove processing status
df_unique = df_unique.drop(
    columns=["processing_status"]
)

# 4. Save unique lyrics features
output_path = "data/processed/lyrics_features_unique.csv"

df_unique.to_csv(
    output_path,
    index=False
)

# 5. Display summary
print("========== UNIQUE LYRICS FEATURES ==========")
print("Original rows:", len(df))
print("Unique rows:", len(df_unique))
print("Unique track IDs:", df_unique["spotify_track_id"].nunique())
print("Output:", output_path)

print("\nMissing values:")
print(df_unique.isna().sum())

print("\nFirst 5 rows:")
print(df_unique.head())
