import pandas as pd

original = pd.read_csv("data/processed/modeling_dataset.csv")
new = pd.read_csv("data/processed/modeling_dataset_with_lyrics.csv")

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

print("1. Row count:", len(original) == len(new))
print("2. Track IDs:", original["spotify_track_id"].nunique() == new["spotify_track_id"].nunique())
print("3. Market distribution:")
print(original["market"].value_counts().sort_index())
print(new["market"].value_counts().sort_index())

print("\n4. Check missing features by lyrics status:")
print(
    new.groupby("lyrics_status")[feature_cols]
    .apply(lambda x: x.isna().sum())
)

print("\n5. Check duplicated IDs have identical features:")
check = new.groupby("spotify_track_id")[feature_cols].nunique(dropna=False)
conflicts = check[(check > 1).any(axis=1)]
print("Conflicting tracks:", len(conflicts))

print("\n6. Required metadata columns:")
print("language:", "language" in new.columns)
print("lyrics_status:", "lyrics_status" in new.columns)