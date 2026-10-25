import pandas as pd

INPUT_PATH = "data/sampling/member2_sample_list.csv"
OUTPUT_PATH = "data/sampling/member2_unique_song_list.csv"


df = pd.read_csv(INPUT_PATH)

# Keep only one row for each unique Spotify Track ID
unique_df = (
    df
    .drop_duplicates(subset=["spotify_track_id"])
    .copy()
)

# Keep the columns needed for YouTube matching
unique_df = unique_df[
    [
        "spotify_track_id",
        "title",
        "artist",
        "release_date",
    ]
]

# Save
unique_df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("===== UNIQUE SONG LIST =====")
print(unique_df.head(10))

print("\nTotal sampled rows:", len(df))
print("Unique Spotify tracks:", len(unique_df))
print("Saved to:", OUTPUT_PATH)

print("\nMissing values:")
print(unique_df.isnull().sum())