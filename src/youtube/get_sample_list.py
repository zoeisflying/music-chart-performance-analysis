import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL or SUPABASE_KEY is missing from .env"
    )


# Create Supabase client
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def get_sample_list():
    rows = []

    page_size = 1000
    start = 0

    while True:
        response = (
            supabase
            .table("song_quarter_sampling")
            .select(
                """
                spotify_track_id,
                market,
                year,
                quarter,
                rank_stratum,
                sampled,
                songs (
                    title,
                    artist,
                    release_date
                )
                """
            )
            .eq("sampled", True)
            .range(start, start + page_size - 1)
            .execute()
        )

        data = response.data

        if not data:
            break

        for item in data:
            song = item.get("songs") or {}

            rows.append({
                "spotify_track_id": item["spotify_track_id"],
                "title": song.get("title"),
                "artist": song.get("artist"),
                "release_date": song.get("release_date"),
                "market": item["market"],
                "year": item["year"],
                "quarter": item["quarter"],
                "rank_stratum": item["rank_stratum"],
                "sampled": item["sampled"],
            })

        print(f"Loaded {len(rows)} rows...")

        if len(data) < page_size:
            break

        start += page_size

    return pd.DataFrame(rows)


if __name__ == "__main__":

    df = get_sample_list()

    print("\n===== SAMPLE LIST =====")
    print(df.head(10))

    print("\nNumber of rows:", len(df))

    print("\nMarkets:")
    print(df["market"].value_counts())

    print("\nMissing values:")
    print(df.isnull().sum())

    output_path = "data/sampling/member2_sample_list.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nSaved to: {output_path}")