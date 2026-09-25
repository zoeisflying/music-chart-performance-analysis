import argparse
import csv
import json
import os
import random
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from title_similarity import title_similarity
from title_normalizer import (
    has_title_conflict,
    has_version_conflict,
    extract_bilingual_aliases,
)
from identity_evidence import get_identity_evidence
from source_evidence import get_source_evidence
from duration_utils import duration_difference_ratio
from match_decision import decide_match
from youtube_matcher import is_hard_invalid_source


# ============================================================
# FILES
# ============================================================

INPUT_FILE = (
    "data/sampling/"
    "member2_unique_song_list_with_duration.csv"
)

RESULTS_FILE = (
    "data/sampling/"
    "youtube_matching_results.csv"
)

CANDIDATES_FILE = (
    "data/sampling/"
    "youtube_matching_candidates.csv"
)


# ============================================================
# YOUTUBE SEARCH SETTINGS
# ============================================================

NUMBER_OF_CANDIDATES = 5

MAX_RETRIES = 3

SLEEP_MIN = 0.5
SLEEP_MAX = 1.2


# ============================================================
# RESULTS CSV
# One row per Spotify song
# ============================================================

RESULT_FIELDS = [
    "spotify_track_id",
    "title",
    "artist",
    "release_date",
    "duration_ms",
    "youtube_video_id",
    "youtube_title",
    "youtube_channel",
    "youtube_duration",
    "title_similarity",
    "title_conflict",
    "identity_evidence",
    "source_evidence",
    "duration_difference_ratio",
    "hard_invalid",
    "status",
    "match_method",
    "is_official",
]


# ============================================================
# CANDIDATES CSV
# Up to 5 rows per Spotify song
# ============================================================

CANDIDATE_FIELDS = [
    "spotify_track_id",
    "spotify_title",
    "spotify_artist",
    "spotify_duration_ms",
    "candidate_number",
    "youtube_video_id",
    "youtube_title",
    "youtube_channel",
    "youtube_duration",
    "title_similarity",
    "title_conflict",
    "identity_evidence",
    "source_evidence",
    "duration_difference_ratio",
    "hard_invalid",
]


# ============================================================
# YOUTUBE SEARCH
# ============================================================

def search_youtube(
    artist,
    title,
):
    query = f"{artist} {title}"

    command = [
        "python",
        "-m",
        "yt_dlp",
        f"ytsearch{NUMBER_OF_CANDIDATES}:{query}",
        "--flat-playlist",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
    ]

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )

            if result.returncode != 0:

                if attempt == MAX_RETRIES:

                    print(
                        "  YouTube search failed "
                        f"after {MAX_RETRIES} attempts."
                    )

                    return []

                time.sleep(
                    2 * attempt
                )

                continue

            try:

                data = json.loads(
                    result.stdout
                )

            except json.JSONDecodeError:

                if attempt == MAX_RETRIES:

                    print(
                        "  Could not parse "
                        "YouTube search result."
                    )

                    return []

                time.sleep(
                    2 * attempt
                )

                continue

            entries = data.get(
                "entries",
                [],
            )

            valid_entries = [
                entry
                for entry in entries
                if entry
            ]

            if not valid_entries and attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
                continue

            return valid_entries

        except (
            subprocess.TimeoutExpired,
            OSError,
        ) as error:

            if attempt == MAX_RETRIES:

                print(
                    "  YouTube search error:",
                    error,
                )

                return []

            time.sleep(
                2 * attempt
            )

    return []


# ============================================================
# CANDIDATE EVALUATION
# ============================================================

def evaluate_candidate(
    candidate,
    spotify_title,
    spotify_artist,
    spotify_duration_ms,
    bilingual_aliases=None,
):

    youtube_title = candidate.get(
        "title",
        "",
    )

    youtube_channel = (
        candidate.get("channel")
        or candidate.get("uploader")
        or ""
    )

    youtube_duration = candidate.get(
        "duration"
    )

    # --------------------------------------------------------
    # 1. TITLE EVIDENCE
    # --------------------------------------------------------

    similarity = title_similarity(
        spotify_title,
        youtube_title,
        spotify_artist=spotify_artist,
        bilingual_aliases=bilingual_aliases,
    )

    title_conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist=spotify_artist,
        bilingual_aliases=bilingual_aliases,
    )

    version_conflict = has_version_conflict(
        spotify_title,
        youtube_title,
        spotify_artist=spotify_artist,
    )

    # --------------------------------------------------------
    # 2. IDENTITY EVIDENCE
    # --------------------------------------------------------

    identity = get_identity_evidence(
        spotify_artist,
        youtube_title,
        youtube_channel,
    )

    # --------------------------------------------------------
    # 3. SOURCE EVIDENCE
    # --------------------------------------------------------

    source = get_source_evidence(
        youtube_title,
        youtube_channel,
        spotify_artist=spotify_artist,
    )

    # --------------------------------------------------------
    # 4. DURATION EVIDENCE
    # --------------------------------------------------------

    duration_ratio = None

    if (
        youtube_duration is not None
        and spotify_duration_ms > 0
    ):

        duration_ratio = (
            duration_difference_ratio(
                spotify_duration_ms,
                int(
                    youtube_duration * 1000
                ),
            )
        )

    # --------------------------------------------------------
    # 5. HARD INVALID
    # --------------------------------------------------------

    hard_invalid = is_hard_invalid_source(
        youtube_title
    )

    return {
        "id": candidate.get("id"),
        "title": youtube_title,
        "spotify_title": spotify_title,
        "spotify_artist": spotify_artist,
        "channel": youtube_channel,
        "duration": youtube_duration,
        "title_similarity": similarity,
        "title_conflict": title_conflict,
        "version_conflict": version_conflict,
        "identity_evidence": identity,
        "source_evidence": source,
        "duration_difference_ratio": duration_ratio,
        "hard_invalid": hard_invalid,
    }


# ============================================================
# OFFICIAL SOURCE EVIDENCE
# ============================================================

def is_official_source(
    source_evidence,
    identity_evidence=None,
):

    if identity_evidence and "exact_channel_artist" in identity_evidence:
        return True

    official_evidence = {
        "topic_channel",
        "official_channel",
        "official_audio",
        "official_lyric_video",
        "official_music_video",
        "official_video",
        "official_live",
    }

    return any(
        evidence in official_evidence
        for evidence in (source_evidence or [])
    )


# ============================================================
# SERIALIZATION
# ============================================================

def serialize_evidence(
    value,
):

    if not value:
        return ""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


# ============================================================
# BUILD FINAL RESULT ROW
# ============================================================

def build_result_row(
    song,
    decision,
):

    selected = decision[
        "selected_candidate"
    ]

    status = decision[
        "status"
    ]

    # --------------------------------------------------------
    # No selected candidate
    # --------------------------------------------------------

    if selected is None:

        return {
            "spotify_track_id": song[
                "spotify_track_id"
            ],
            "title": song[
                "title"
            ],
            "artist": song[
                "artist"
            ],
            "release_date": song.get(
                "release_date",
                "",
            ),
            "duration_ms": song[
                "duration_ms"
            ],
            "youtube_video_id": "",
            "youtube_title": "",
            "youtube_channel": "",
            "youtube_duration": "",
            "title_similarity": "",
            "title_conflict": "",
            "identity_evidence": "",
            "source_evidence": "",
            "duration_difference_ratio": "",
            "hard_invalid": "",
            "status": status,
            "match_method": "youtube_search",
            "is_official": "",
        }

    # --------------------------------------------------------
    # Selected candidate
    # --------------------------------------------------------

    return {
        "spotify_track_id": song[
            "spotify_track_id"
        ],
        "title": song[
            "title"
        ],
        "artist": song[
            "artist"
        ],
        "release_date": song.get(
            "release_date",
            "",
        ),
        "duration_ms": song[
            "duration_ms"
        ],
        "youtube_video_id": selected[
            "id"
        ],
        "youtube_title": selected[
            "title"
        ],
        "youtube_channel": selected[
            "channel"
        ],
        "youtube_duration": selected[
            "duration"
        ],
        "title_similarity": selected[
            "title_similarity"
        ],
        "title_conflict": selected[
            "title_conflict"
        ],
        "identity_evidence": serialize_evidence(
            selected[
                "identity_evidence"
            ]
        ),
        "source_evidence": serialize_evidence(
            selected[
                "source_evidence"
            ]
        ),
        "duration_difference_ratio": selected[
            "duration_difference_ratio"
        ],
        "hard_invalid": selected[
            "hard_invalid"
        ],
        "status": status,
        "match_method": "youtube_search",
        "is_official": is_official_source(
            selected[
                "source_evidence"
            ],
            selected.get(
                "identity_evidence"
            ),
        ),
    }


# ============================================================
# BUILD CANDIDATE ROW
# ============================================================

def build_candidate_row(
    song,
    candidate,
    candidate_number,
):

    return {
        "spotify_track_id": song[
            "spotify_track_id"
        ],
        "spotify_title": song[
            "title"
        ],
        "spotify_artist": song[
            "artist"
        ],
        "spotify_duration_ms": song[
            "duration_ms"
        ],
        "candidate_number": candidate_number,
        "youtube_video_id": candidate[
            "id"
        ],
        "youtube_title": candidate[
            "title"
        ],
        "youtube_channel": candidate[
            "channel"
        ],
        "youtube_duration": candidate[
            "duration"
        ],
        "title_similarity": candidate[
            "title_similarity"
        ],
        "title_conflict": candidate[
            "title_conflict"
        ],
        "identity_evidence": serialize_evidence(
            candidate[
                "identity_evidence"
            ]
        ),
        "source_evidence": serialize_evidence(
            candidate[
                "source_evidence"
            ]
        ),
        "duration_difference_ratio": candidate[
            "duration_difference_ratio"
        ],
        "hard_invalid": candidate[
            "hard_invalid"
        ],
    }


# ============================================================
# LOAD PROCESSED SONG IDS
# ============================================================

def load_processed_ids():

    processed_ids = set()

    if not os.path.exists(
        RESULTS_FILE
    ):

        return processed_ids

    with open(
        RESULTS_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            track_id = row.get(
                "spotify_track_id"
            )

            if track_id:

                processed_ids.add(
                    track_id
                )

    return processed_ids


# ============================================================
# INITIALIZE OUTPUT FILES
# ============================================================

def initialize_results_file():

    if os.path.exists(
        RESULTS_FILE
    ):

        return

    os.makedirs(
        os.path.dirname(
            RESULTS_FILE
        ),
        exist_ok=True,
    )

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=RESULT_FIELDS,
        )

        writer.writeheader()


def initialize_candidates_file():

    if os.path.exists(
        CANDIDATES_FILE
    ):

        return

    os.makedirs(
        os.path.dirname(
            CANDIDATES_FILE
        ),
        exist_ok=True,
    )

    with open(
        CANDIDATES_FILE,
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CANDIDATE_FIELDS,
        )

        writer.writeheader()


# ============================================================
# APPEND RESULT
# ============================================================

def append_result(
    row,
):

    for attempt in range(60):
        try:
            with open(
                RESULTS_FILE,
                "a",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=RESULT_FIELDS,
                )

                writer.writerow(
                    row
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )
            return
        except PermissionError:
            if attempt == 0:
                print("  [File locked by another program, waiting to write result...]")
            time.sleep(2)


# ============================================================
# APPEND CANDIDATES
# ============================================================

def append_candidates(
    rows,
):

    if not rows:

        return

    for attempt in range(60):
        try:
            with open(
                CANDIDATES_FILE,
                "a",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=CANDIDATE_FIELDS,
                )

                writer.writerows(
                    rows
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )
            return
        except PermissionError:
            if attempt == 0:
                print("  [File locked by another program, waiting to write candidates...]")
            time.sleep(2)


# ============================================================
# LOAD SONGS
# ============================================================

def load_songs():

    songs = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            songs.append(
                row
            )

    return songs


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of new songs "
            "to process. Useful for testing."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Initialize files
    # --------------------------------------------------------

    initialize_results_file()

    initialize_candidates_file()

    # --------------------------------------------------------
    # Load input
    # --------------------------------------------------------

    songs = load_songs()

    # --------------------------------------------------------
    # Resume support
    # --------------------------------------------------------

    processed_ids = (
        load_processed_ids()
    )

    remaining_songs = [
        song
        for song in songs
        if song[
            "spotify_track_id"
        ] not in processed_ids
    ]

    # --------------------------------------------------------
    # Apply test limit
    # --------------------------------------------------------

    if args.limit is not None:

        songs_to_process = (
            remaining_songs[
                :args.limit
            ]
        )

    else:

        songs_to_process = (
            remaining_songs
        )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print(
        "===== YOUTUBE MATCHING PIPELINE ====="
    )

    print(
        "Input songs:",
        len(songs),
    )

    print(
        "Already processed:",
        len(processed_ids),
    )

    print(
        "Remaining:",
        len(remaining_songs),
    )

    print(
        "Processing now:",
        len(songs_to_process),
    )

    print(
        "Candidates per song:",
        NUMBER_OF_CANDIDATES,
    )

    print()

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    counts = {
        "automatic": 0,
        "ambiguous": 0,
        "no_confident_match": 0,
    }

    total_candidates = 0

    # --------------------------------------------------------
    # Process songs
    # --------------------------------------------------------

    for index, song in enumerate(
        songs_to_process,
        start=1,
    ):

        track_id = song[
            "spotify_track_id"
        ]

        title = song[
            "title"
        ]

        artist = song[
            "artist"
        ]

        duration_ms = int(
            song[
                "duration_ms"
            ]
        )

        print(
            f"[{index}/{len(songs_to_process)}] "
            f"{artist} - {title}"
        )

        # ----------------------------------------------------
        # Search YouTube
        # ----------------------------------------------------

        candidates = search_youtube(
            artist,
            title,
        )

        total_candidates += len(
            candidates
        )

        # ----------------------------------------------------
        # Evaluate candidates
        # ----------------------------------------------------

        bilingual_aliases = extract_bilingual_aliases(
            title,
            candidates,
            spotify_artist=artist,
        )

        evaluated = []

        for candidate in candidates:

            evaluated_candidate = (
                evaluate_candidate(
                    candidate,
                    title,
                    artist,
                    duration_ms,
                    bilingual_aliases=bilingual_aliases,
                )
            )

            evaluated.append(
                evaluated_candidate
            )

        # ----------------------------------------------------
        # Save ALL candidate evidence
        # ----------------------------------------------------

        candidate_rows = []

        for candidate_number, candidate in enumerate(
            evaluated,
            start=1,
        ):

            candidate_rows.append(
                build_candidate_row(
                    song,
                    candidate,
                    candidate_number,
                )
            )

        append_candidates(
            candidate_rows
        )

        # ----------------------------------------------------
        # Final decision
        # ----------------------------------------------------

        decision = decide_match(
            evaluated
        )

        # ----------------------------------------------------
        # Save one final result row
        # ----------------------------------------------------

        result_row = build_result_row(
            song,
            decision,
        )

        append_result(
            result_row
        )

        status = decision[
            "status"
        ]

        counts[
            status
        ] += 1

        # ----------------------------------------------------
        # Progress output
        # ----------------------------------------------------

        print(
            "  Candidates:",
            len(candidates),
        )

        print(
            "  Status:",
            status,
        )

        selected = decision[
            "selected_candidate"
        ]

        if selected is not None:

            print(
                "  YouTube ID:",
                selected["id"],
            )

        else:

            print(
                "  YouTube ID: NONE"
            )

        # ----------------------------------------------------
        # Delay
        # ----------------------------------------------------

        if index < len(
            songs_to_process
        ):

            time.sleep(
                random.uniform(
                    SLEEP_MIN,
                    SLEEP_MAX,
                )
            )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()

    print(
        "===== RUN COMPLETE ====="
    )

    print(
        "Processed:",
        len(songs_to_process),
    )

    print(
        "Total candidates:",
        total_candidates,
    )

    print(
        "Automatic:",
        counts[
            "automatic"
        ],
    )

    print(
        "Ambiguous:",
        counts[
            "ambiguous"
        ],
    )

    print(
        "No confident match:",
        counts[
            "no_confident_match"
        ],
    )

    print()

    print(
        "Results:",
        RESULTS_FILE,
    )

    print(
        "Candidates:",
        CANDIDATES_FILE,
    )


if __name__ == "__main__":
    main()