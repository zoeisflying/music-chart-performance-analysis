# Full-run lyrics collection script with Supabase pagination + checkpoint.
# Replace src/lyrics/lyrics_collection.py with this file.

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not GENIUS_API_TOKEN:
    print("Không tìm thấy GENIUS_API_TOKEN.")
    raise SystemExit
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Không tìm thấy SUPABASE_URL hoặc SUPABASE_KEY.")
    raise SystemExit

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PENDING = "pending"
PROCESSING = "processing"
SUCCESS = "success"
FAILED = "failed"
NOT_FOUND = "not_found"
REJECTED = "rejected"

LYRICS_FOLDER = os.path.join("data", "raw", "lyrics")
CHECKPOINT_FILE = os.path.join("data", "raw", "lyrics_collection_checkpoint.json")
RESULT_FILE = os.path.join("data", "raw", "lyrics_collection_results.json")
os.makedirs(LYRICS_FOLDER, exist_ok=True)


def normalize_text(text):
    if not text:
        return ""
    return " ".join(text.lower().split())


def is_original_song(result, title, artist):
    result_title = result.get("title", "")
    result_artist = result.get("primary_artist", {}).get("name", "")
    rt = normalize_text(result_title)
    ra = normalize_text(result_artist)
    t = normalize_text(title)
    a = normalize_text(artist)

    bad_keywords = [
        "translation", "translated", "romanized", "romanization",
        "traducción", "traduction", "перевод", "übersetzung",
        "中文翻譯", "中文翻译", "çeviri", "ترجمة", "karaoke",
        "instrumental", "remix", "live", "acoustic", "sped up",
        "slowed", "tribute", "parody", "cover"
    ]
    for keyword in bad_keywords:
        if keyword in rt or keyword in ra:
            return False

    title_match = t == rt or t in rt or rt in t
    artist_match = a in ra or ra in a
    return title_match and artist_match


def search_genius_song(title, artist):
    url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    try:
        response = requests.get(
            url, headers=headers, params={"q": f"{title} {artist}"}, timeout=15
        )
    except requests.exceptions.RequestException as e:
        print("Lỗi Genius API:", e)
        return None

    print("Genius HTTP:", response.status_code)
    if response.status_code != 200:
        return None

    try:
        hits = response.json().get("response", {}).get("hits", [])
    except Exception:
        return None

    for hit in hits:
        result = hit.get("result", {})
        if is_original_song(result, title, artist):
            genius_url = result.get("url")
            if genius_url:
                return {
                    "title": result.get("title", ""),
                    "artist": result.get("primary_artist", {}).get("name", ""),
                    "url": genius_url,
                }
    return None


def get_lyrics_from_url(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        print("Lỗi request Genius:", e)
        return None, FAILED

    print("Genius page HTTP:", response.status_code)
    if response.status_code != 200:
        return None, FAILED

    soup = BeautifulSoup(response.text, "html.parser")
    containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
    if not containers:
        return None, FAILED

    parts = []
    for container in containers:
        text = container.get_text("\n", strip=True)
        if text:
            parts.append(text)

    lyrics = "\n\n".join(parts)
    if not lyrics.strip():
        return None, FAILED
    return lyrics, SUCCESS


def get_lyrics_from_lrclib(title, artist, max_retries=3):
    url = "https://lrclib.net/api/search"
    params = {"track_name": title, "artist_name": artist}
    results = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=20)
            print(f"LRCLIB HTTP: {response.status_code} (attempt {attempt}/{max_retries})")

            if response.status_code in (502, 503, 504):
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                return None, FAILED

            if response.status_code != 200:
                return None, FAILED

            try:
                results = response.json()
            except Exception:
                return None, FAILED
            break

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print("Lỗi kết nối LRCLIB:", e)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            return None, FAILED
        except requests.exceptions.RequestException as e:
            print("Lỗi LRCLIB:", e)
            return None, FAILED

    if not results:
        return None, NOT_FOUND

    title_normalized = normalize_text(title)
    artist_normalized = normalize_text(artist)

    for result in results:
        result_title = result.get("trackName", "")
        result_artist = result.get("artistName", "")
        title_match = title_normalized == normalize_text(result_title)
        artist_match = (
            artist_normalized in normalize_text(result_artist)
            or normalize_text(result_artist) in artist_normalized
        )
        if not (title_match and artist_match):
            continue

        lyrics = result.get("plainLyrics")
        if lyrics and lyrics.strip():
            return lyrics, SUCCESS

        synced = result.get("syncedLyrics")
        if synced and synced.strip():
            lines = []
            for line in synced.splitlines():
                text = line.split("]", 1)[1] if "]" in line else line
                if text.strip():
                    lines.append(text.strip())
            lyrics = "\n".join(lines)
            if lyrics.strip():
                return lyrics, SUCCESS

    return None, NOT_FOUND


def save_lyrics(spotify_track_id, lyrics):
    file_path = os.path.join(LYRICS_FOLDER, f"{spotify_track_id}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(lyrics)
    return file_path


def get_sample_songs(page_size=1000):
    all_rows = []
    start = 0

    while True:
        end = start + page_size - 1
        response = (
            supabase.table("song_quarter_sampling")
            .select("spotify_track_id,market,year,quarter,rank_stratum,sampled")
            .eq("sampled", True)
            .range(start, end)
            .execute()
        )
        rows = response.data or []
        print(f"Sampling rows {start}-{end}: {len(rows)}")
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size

    track_ids = []
    for row in all_rows:
        track_id = row.get("spotify_track_id")
        if track_id and track_id not in track_ids:
            track_ids.append(track_id)

    songs_by_id = {}
    batch_size = 100
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        response = (
            supabase.table("songs")
            .select("spotify_track_id,title,artist,album,release_date")
            .in_("spotify_track_id", batch)
            .execute()
        )
        for song in response.data or []:
            songs_by_id[song["spotify_track_id"]] = song

    songs = {}
    for row in all_rows:
        track_id = row.get("spotify_track_id")
        if not track_id or track_id not in songs_by_id:
            continue

        if track_id not in songs:
            song_info = songs_by_id[track_id]
            songs[track_id] = {
                "spotify_track_id": track_id,
                "title": song_info.get("title", ""),
                "artist": song_info.get("artist", ""),
                "album": song_info.get("album"),
                "release_date": song_info.get("release_date"),
                "sampling_provenance": [],
            }

        provenance = {
            "market": row.get("market"),
            "year": row.get("year"),
            "quarter": row.get("quarter"),
            "rank_stratum": row.get("rank_stratum"),
        }
        if provenance not in songs[track_id]["sampling_provenance"]:
            songs[track_id]["sampling_provenance"].append(provenance)

    result = list(songs.values())
    print("Unique songs:", len(result))
    return result


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return {}
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        print("Đã load checkpoint:", len(data), "bài")
        return data
    except Exception as e:
        print("Không đọc được checkpoint:", e)
        return {}


def save_json_atomic(path, data):
    temp_file = path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(temp_file, path)


def process_song(spotify_track_id, title, artist):
    print("\n" + "=" * 60)
    print("ĐANG XỬ LÝ", spotify_track_id, "|", title, "|", artist)
    print("=" * 60)

    genius_song = search_genius_song(title, artist)

    if genius_song is None:
        return {
            "spotify_track_id": spotify_track_id,
            "title": title,
            "artist": artist,
            "source": None,
            "genius_url": None,
            "language": None,
            "lyrics_status": NOT_FOUND,
            "collection_status": SUCCESS,
        }

    lyrics, status = get_lyrics_from_url(genius_song["url"])
    if status == SUCCESS:
        source = "Genius"
    else:
        print("Genius không lấy được lyrics -> LRCLIB")
        lyrics, lrclib_status = get_lyrics_from_lrclib(title, artist)
        if lrclib_status != SUCCESS:
            return {
                "spotify_track_id": spotify_track_id,
                "title": title,
                "artist": artist,
                "source": "Genius + LRCLIB",
                "genius_url": genius_song["url"],
                "language": None,
                "lyrics_status": lrclib_status,
                "collection_status": SUCCESS if lrclib_status == NOT_FOUND else FAILED,
            }
        source = "LRCLIB"

    file_path = save_lyrics(spotify_track_id, lyrics)
    print("Đã lưu:", file_path)

    return {
        "spotify_track_id": spotify_track_id,
        "title": title,
        "artist": artist,
        "source": source,
        "genius_url": genius_song["url"],
        "language": None,
        "lyrics_status": SUCCESS,
        "collection_status": SUCCESS,
        "lyrics_file": file_path,
    }


def print_summary(results):
    total = len(results)
    success = sum(r.get("lyrics_status") == SUCCESS for r in results.values())
    not_found = sum(r.get("lyrics_status") == NOT_FOUND for r in results.values())
    failed = sum(r.get("lyrics_status") == FAILED for r in results.values())
    rejected = sum(r.get("lyrics_status") == REJECTED for r in results.values())
    genius = sum(r.get("source") == "Genius" for r in results.values())
    lrclib = sum(r.get("source") == "LRCLIB" for r in results.values())

    print("\n" + "=" * 60)
    print("KẾT QUẢ")
    print("=" * 60)
    print("Tổng số bài:", total)
    print("Success:", success)
    print("Not found:", not_found)
    print("Failed:", failed)
    print("Rejected:", rejected)
    print("Nguồn Genius:", genius)
    print("Nguồn LRCLIB:", lrclib)
    print("Checkpoint:", CHECKPOINT_FILE)
    print("Final results:", RESULT_FILE)
    print("Lyrics folder:", LYRICS_FOLDER)


def process_sample_songs():
    songs = get_sample_songs()
    if not songs:
        print("Không có sampled songs.")
        return

    checkpoint = load_checkpoint()
    total = len(songs)

    for index, song in enumerate(songs, start=1):
        track_id = song["spotify_track_id"]
        lyrics_file = os.path.join(LYRICS_FOLDER, f"{track_id}.txt")
        existing = checkpoint.get(track_id)

        if (
            existing
            and existing.get("lyrics_status") == SUCCESS
            and os.path.exists(lyrics_file)
        ):
            print(f"[{index}/{total}] SKIP: {song['title']}")
            continue

        try:
            result = process_song(
                track_id,
                song["title"],
                song["artist"],
            )
            result["sampling_provenance"] = song["sampling_provenance"]
            result["release_date"] = song.get("release_date")
            result["album"] = song.get("album")
            checkpoint[track_id] = result

        except KeyboardInterrupt:
            save_json_atomic(CHECKPOINT_FILE, checkpoint)
            save_json_atomic(RESULT_FILE, checkpoint)
            print("\nĐã dừng. Checkpoint đã lưu.")
            print("Chạy lại script để tiếp tục.")
            return

        except Exception as e:
            print("LỖI:", e)
            checkpoint[track_id] = {
                "spotify_track_id": track_id,
                "title": song["title"],
                "artist": song["artist"],
                "source": None,
                "genius_url": None,
                "language": None,
                "lyrics_status": FAILED,
                "collection_status": FAILED,
                "error": str(e),
                "sampling_provenance": song["sampling_provenance"],
            }

        save_json_atomic(CHECKPOINT_FILE, checkpoint)
        print(f"Checkpoint saved: {index}/{total}")
        time.sleep(1)

    save_json_atomic(RESULT_FILE, checkpoint)
    print_summary(checkpoint)


def main():
    print("Đã đọc được Genius API token.")
    print("Đã kết nối Supabase.")
    process_sample_songs()


if __name__ == "__main__":
    main()
