import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# =========================
# CONFIG
# =========================

load_dotenv()

GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")

LYRICS_FOLDER = os.path.join("data", "raw", "lyrics")

RESULT_FILE = os.path.join(
    "data", "raw", "lyrics_collection_results.json"
)

CHECKPOINT_FILE = os.path.join(
    "data", "raw", "lyrics_retry_checkpoint.json"
)

os.makedirs(LYRICS_FOLDER, exist_ok=True)


# =========================
# STATUS
# =========================

SUCCESS = "success"
FAILED = "failed"
NOT_FOUND = "not_found"


# =========================
# TEXT NORMALIZATION
# =========================

def normalize_text(text):
    if not text:
        return ""

    return " ".join(text.lower().split())


# =========================
# CHECK ORIGINAL SONG
# =========================

def is_original_song(result_title, result_artist, title, artist):

    bad_keywords = [
        "translation",
        "translated",
        "romanized",
        "karaoke",
        "instrumental",
        "remix",
        "live",
        "acoustic",
        "sped up",
        "slowed",
        "tribute",
        "parody",
        "cover"
    ]

    result_text = normalize_text(
        f"{result_title} {result_artist}"
    )

    for keyword in bad_keywords:
        if keyword in result_text:
            return False

    normalized_title = normalize_text(title)
    normalized_artist = normalize_text(artist)

    if not normalized_title or not normalized_artist:
        return False

    title_match = (
        normalized_title == normalize_text(result_title)
        or normalized_title in normalize_text(result_title)
        or normalize_text(result_title) in normalized_title
    )

    artist_match = (
        normalized_artist == normalize_text(result_artist)
        or normalized_artist in normalize_text(result_artist)
        or normalize_text(result_artist) in normalized_artist
    )

    return title_match and artist_match


# =========================
# GENIUS SEARCH
# =========================

def search_genius_song(title, artist):

    if not GENIUS_API_TOKEN:
        print("Không có GENIUS_API_TOKEN.")
        return None

    url = "https://api.genius.com/search"

    headers = {
        "Authorization": f"Bearer {GENIUS_API_TOKEN}"
    }

    params = {
        "q": f"{title} {artist}"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            print(
                f"Genius HTTP {response.status_code}"
            )
            return None

        data = response.json()

        hits = data.get("response", {}).get("hits", [])

        for hit in hits:

            result = hit.get("result", {})

            result_title = result.get("title", "")
            result_artist = result.get(
                "primary_artist", {}
            ).get("name", "")

            if is_original_song(
                result_title,
                result_artist,
                title,
                artist
            ):
                return {
                    "title": result_title,
                    "artist": result_artist,
                    "url": result.get("url")
                }

        return None

    except requests.RequestException as e:

        print(f"Genius search error: {e}")

        return None


# =========================
# GENIUS SCRAPE
# =========================

def get_lyrics_from_url(url, max_retries=3):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
        )
    }

    for attempt in range(1, max_retries + 1):

        try:

            print(
                f"  Genius scrape attempt "
                f"{attempt}/{max_retries}"
            )

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:

                print(
                    f"  Genius HTTP "
                    f"{response.status_code}"
                )

                if attempt < max_retries:
                    time.sleep(2)
                    continue

                return None, FAILED

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            containers = soup.select(
                'div[data-lyrics-container="true"]'
            )

            if not containers:

                print(
                    "  Không tìm thấy lyrics container."
                )

                if attempt < max_retries:
                    time.sleep(2)
                    continue

                return None, FAILED

            lyrics_parts = []

            for container in containers:
                lyrics_parts.append(
                    container.get_text(
                        "\n",
                        strip=True
                    )
                )

            lyrics = "\n".join(lyrics_parts).strip()

            if lyrics:
                return lyrics, SUCCESS

            if attempt < max_retries:
                time.sleep(2)
                continue

            return None, FAILED

        except requests.RequestException as e:

            print(
                f"  Genius scrape error: {e}"
            )

            if attempt < max_retries:
                time.sleep(2)
                continue

            return None, FAILED

    return None, FAILED


# =========================
# LRCLIB
# =========================

def get_lyrics_from_lrclib(
    title,
    artist,
    max_retries=3
):

    url = "https://lrclib.net/api/search"

    params = {
        "track_name": title,
        "artist_name": artist
    }

    for attempt in range(1, max_retries + 1):

        try:

            print(
                f"  LRCLIB attempt "
                f"{attempt}/{max_retries}"
            )

            response = requests.get(
                url,
                params=params,
                timeout=20
            )

            if response.status_code in [502, 503, 504]:

                print(
                    f"  LRCLIB HTTP "
                    f"{response.status_code}"
                )

                if attempt < max_retries:
                    time.sleep(2)
                    continue

                return None, FAILED

            if response.status_code != 200:

                print(
                    f"  LRCLIB HTTP "
                    f"{response.status_code}"
                )

                return None, NOT_FOUND

            results = response.json()

            normalized_title = normalize_text(title)
            normalized_artist = normalize_text(artist)

            for result in results:

                result_title = normalize_text(
                    result.get("trackName", "")
                )

                result_artist = normalize_text(
                    result.get("artistName", "")
                )

                title_match = (
                    normalized_title == result_title
                )

                artist_match = (
                    normalized_artist in result_artist
                    or result_artist in normalized_artist
                )

                if title_match and artist_match:

                    lyrics = result.get(
                        "plainLyrics"
                    )

                    if not lyrics:

                        synced = result.get(
                            "syncedLyrics"
                        )

                        if synced:

                            lines = []

                            for line in synced.splitlines():

                                if "]" in line:
                                    line = line.split(
                                        "]",
                                        1
                                    )[1]

                                lines.append(line)

                            lyrics = "\n".join(lines)

                    if lyrics and lyrics.strip():
                        return lyrics.strip(), SUCCESS

            return None, NOT_FOUND

        except (
            requests.Timeout,
            requests.ConnectionError
        ) as e:

            print(
                f"  LRCLIB connection error: {e}"
            )

            if attempt < max_retries:
                time.sleep(2)
                continue

            return None, FAILED

        except requests.RequestException as e:

            print(
                f"  LRCLIB error: {e}"
            )

            if attempt < max_retries:
                time.sleep(2)
                continue

            return None, FAILED

    return None, FAILED


# =========================
# SAVE LYRICS
# =========================

def save_lyrics(track_id, lyrics):

    filepath = os.path.join(
        LYRICS_FOLDER,
        f"{track_id}.txt"
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(lyrics)

    return filepath


# =========================
# PROCESS ONE SONG
# =========================

def retry_song(track_id, item):

    title = item.get("title", "")
    artist = item.get("artist", "")

    print()
    print("=" * 70)
    print(f"Track ID: {track_id}")
    print(f"Title: {title}")
    print(f"Artist: {artist}")
    print("=" * 70)

    # ---------------------------------
    # 1. TRY GENIUS SEARCH
    # ---------------------------------

    genius_song = search_genius_song(
        title,
        artist
    )

    if genius_song:

        print(
            f"  Genius found: "
            f"{genius_song['title']} "
            f"- {genius_song['artist']}"
        )

        lyrics, status = get_lyrics_from_url(
            genius_song["url"],
            max_retries=3
        )

        if status == SUCCESS:

            filepath = save_lyrics(
                track_id,
                lyrics
            )

            print(
                "  SUCCESS - Genius"
            )

            return {
                "success": True,
                "source": "Genius",
                "lyrics_status": SUCCESS,
                "lyrics_file": filepath
            }

        print(
            "  Genius page failed."
        )

    else:

        print(
            "  Genius search: NOT FOUND"
        )

    # ---------------------------------
    # 2. ALWAYS TRY LRCLIB
    # ---------------------------------

    print(
        "  Fallback -> LRCLIB"
    )

    lyrics, status = get_lyrics_from_lrclib(
        title,
        artist,
        max_retries=3
    )

    if status == SUCCESS:

        filepath = save_lyrics(
            track_id,
            lyrics
        )

        print(
            "  SUCCESS - LRCLIB"
        )

        return {
            "success": True,
            "source": "LRCLIB",
            "lyrics_status": SUCCESS,
            "lyrics_file": filepath
        }

    # ---------------------------------
    # 3. FINAL RESULT
    # ---------------------------------

    if status == NOT_FOUND:

        print(
            "  FINAL: NOT FOUND"
        )

        return {
            "success": False,
            "source": None,
            "lyrics_status": NOT_FOUND,
            "lyrics_file": None
        }

    print(
        "  FINAL: FAILED"
    )

    return {
        "success": False,
        "source": None,
        "lyrics_status": FAILED,
        "lyrics_file": None
    }


# =========================
# LOAD CHECKPOINT
# =========================

def load_checkpoint():

    if not os.path.exists(CHECKPOINT_FILE):
        return {}

    try:

        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


# =========================
# SAVE CHECKPOINT
# =========================

def save_checkpoint(checkpoint):

    temp_file = CHECKPOINT_FILE + ".tmp"

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            checkpoint,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temp_file,
        CHECKPOINT_FILE
    )


# =========================
# MAIN
# =========================

def main():

    print("=" * 70)
    print("LYRICS RETRY")
    print("=" * 70)

    # ---------------------------------
    # LOAD RESULTS
    # ---------------------------------

    with open(
        RESULT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        results = json.load(f)

    # ---------------------------------
    # GET MISSING SONGS
    # ---------------------------------

    missing_songs = {}

    for track_id, item in results.items():

        if item.get("lyrics_status") in [
            NOT_FOUND,
            FAILED
        ]:

            missing_songs[track_id] = item

    print(
        f"Tổng số bài cần retry: "
        f"{len(missing_songs)}"
    )

    # ---------------------------------
    # LOAD RETRY CHECKPOINT
    # ---------------------------------

    checkpoint = load_checkpoint()

    recovered = 0
    still_not_found = 0
    failed = 0
    skipped = 0

    # ---------------------------------
    # RETRY
    # ---------------------------------

    for index, (track_id, item) in enumerate(
        missing_songs.items(),
        start=1
    ):

        print()
        print(
            f"[{index}/{len(missing_songs)}]"
        )

        # Already retried
        if track_id in checkpoint:

            print(
                "Đã retry trước đó -> skip"
            )

            skipped += 1

            continue

        result = retry_song(
            track_id,
            item
        )

        # ---------------------------------
        # SUCCESS
        # ---------------------------------

        if result["success"]:

            item["lyrics_status"] = SUCCESS
            item["collection_status"] = SUCCESS
            item["source"] = result["source"]
            item["lyrics_file"] = result[
                "lyrics_file"
            ]

            recovered += 1

        # ---------------------------------
        # NOT FOUND
        # ---------------------------------

        elif result["lyrics_status"] == NOT_FOUND:

            item["lyrics_status"] = NOT_FOUND
            item["collection_status"] = SUCCESS
            item["source"] = None

            still_not_found += 1

        # ---------------------------------
        # FAILED
        # ---------------------------------

        else:

            item["lyrics_status"] = FAILED
            item["collection_status"] = FAILED
            item["source"] = None

            failed += 1

        # ---------------------------------
        # CHECKPOINT
        # ---------------------------------

        checkpoint[track_id] = {
            "lyrics_status": item[
                "lyrics_status"
            ],
            "source": item.get("source"),
            "lyrics_file": item.get(
                "lyrics_file"
            )
        }

        save_checkpoint(checkpoint)

        # ---------------------------------
        # SAVE RESULTS AFTER EACH SONG
        # ---------------------------------

        temp_file = RESULT_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                results,
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temp_file,
            RESULT_FILE
        )

        time.sleep(0.5)

    # ---------------------------------
    # SUMMARY
    # ---------------------------------

    print()
    print("=" * 70)
    print("RETRY COMPLETED")
    print("=" * 70)

    print(
        f"Recovered: {recovered}"
    )

    print(
        f"Still not found: {still_not_found}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print()
    print(
        f"Checkpoint: {CHECKPOINT_FILE}"
    )

    print(
        f"Results: {RESULT_FILE}"
    )


if __name__ == "__main__":
    main()