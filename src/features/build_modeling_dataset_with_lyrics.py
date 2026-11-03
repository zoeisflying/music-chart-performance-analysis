import pandas as pd

# 1. Read original dataset and unique lyrics features
base = pd.read_csv("data/processed/modeling_dataset.csv")
lyrics = pd.read_csv("data/processed/lyrics_features_unique.csv")

# 2. Define lyrics feature columns
feature_cols = [
    "word_count",
    "unique_word_count",
    "lexical_diversity",
    "repetition_ratio",
    "avg_word_length",
    "line_count",
    "chorus_repetition_count",
    "title_word_in_lyrics",
    "punctuation_ratio",
    "pronoun_ratio"
]

# 3. Keep original row order
base["_row_order"] = range(len(base))

# 4. Remove old lyrics features
base = base.drop(columns=feature_cols, errors="ignore")

# 5. Merge new lyrics features
result = base.merge(
    lyrics[["spotify_track_id"] + feature_cols],
    on="spotify_track_id",
    how="left",
    validate="many_to_one"
)

# 6. Restore original row order
result = result.sort_values("_row_order")
result = result.drop(columns=["_row_order"])

# 7. Save new dataset
output_path = "data/processed/modeling_dataset_with_lyrics.csv"
result.to_csv(output_path, index=False)

print("Original dataset:", base.shape)
print("New dataset:", result.shape)
print("Unique track IDs:", result["spotify_track_id"].nunique())

print("\nLyrics status:")
print(result["lyrics_status"].value_counts(dropna=False))

print("\nMissing lyrics features:")
print(result[feature_cols].isna().sum())

print("\nMarkets:")
print(result["market"].value_counts())

print("\nSaved:", output_path)