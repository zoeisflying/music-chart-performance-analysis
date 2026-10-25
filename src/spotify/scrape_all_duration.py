import os
import time
import random

import pandas as pd

from spotify_web_scraper import get_spotify_duration


INPUT_PATH = "data/sampling/member2_unique_song_list.csv"
OUTPUT_PATH = "data/sampling/member2_unique_song_list_with_duration.csv"

SAVE_EVERY = 50
MAX_RETRIES = 3


def scrape_duration_with_retry(track_id):

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            duration_ms = get_spotify_duration(track_id)

            return duration_ms, "success"

        except Exception as e:

            print(
                f"  Attempt {attempt}/{MAX_RETRIES} failed: {e}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)

    return None, "failed"


def main():

    print("===== SPOTIFY DURATION BATCH SCRAPER =====")

    df = pd.read_csv(INPUT_PATH)

    print("Input rows:", len(df))
    print(
        "Unique Spotify IDs:",
        df["spotify_track_id"].nunique()
    )

    # --------------------------------------------------
    # Resume existing progress
    # --------------------------------------------------

    if os.path.exists(OUTPUT_PATH):

        print("\nExisting output found.")
        print("Resuming previous progress...")

        result_df = pd.read_csv(OUTPUT_PATH)

        if "duration_ms" not in result_df.columns:
            result_df["duration_ms"] = None

        if "duration_status" not in result_df.columns:
            result_df["duration_status"] = None

    else:

        result_df = df.copy()

        result_df["duration_ms"] = None
        result_df["duration_status"] = None

    # --------------------------------------------------
    # Validate row count
    # --------------------------------------------------

    assert len(result_df) == len(df)

    print(
        "Already successful:",
        (
            result_df["duration_status"] == "success"
        ).sum()
    )

    # --------------------------------------------------
    # Scrape
    # --------------------------------------------------

    total = len(result_df)

    for index, row in result_df.iterrows():

        # Skip completed rows
        if row["duration_status"] == "success":
            continue

        track_id = row["spotify_track_id"]

        print(
            f"\n[{index + 1}/{total}] "
            f"{row['title']} - {row['artist']}"
        )

        duration_ms, status = scrape_duration_with_retry(
            track_id
        )

        result_df.at[index, "duration_ms"] = duration_ms
        result_df.at[index, "duration_status"] = status

        if status == "success":

            print(
                f"  Duration: "
                f"{duration_ms / 1000:.3f} seconds"
            )

        else:

            print("  FAILED")

        # --------------------------------------------------
        # Checkpoint
        # --------------------------------------------------

        if (index + 1) % SAVE_EVERY == 0:

            result_df.to_csv(
                OUTPUT_PATH,
                index=False,
                encoding="utf-8-sig"
            )

            print(
                f"\nCheckpoint saved at "
                f"{index + 1}/{total}"
            )

        # Small delay
        time.sleep(
            random.uniform(0.5, 1.2)
        )

    # --------------------------------------------------
    # Final save
    # --------------------------------------------------

    result_df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== SCRAPING COMPLETE =====")

    print(
        "Total rows:",
        len(result_df)
    )

    print(
        "Successful:",
        (
            result_df["duration_status"] == "success"
        ).sum()
    )

    print(
        "Failed:",
        (
            result_df["duration_status"] == "failed"
        ).sum()
    )

    print(
        "Output:",
        OUTPUT_PATH
    )


if __name__ == "__main__":
    main()