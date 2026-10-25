import csv
import json
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from title_normalizer import has_version_conflict
from run_youtube_matching import is_official_source

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

CANDIDATES_FILE = "data/sampling/youtube_matching_candidates.csv"
FINAL_SELECTED_FILE = "data/sampling/youtube_matching_final_all_songs.csv"
RESULTS_FILE = "data/sampling/youtube_matching_results.csv"

BATCH_SIZE = 500


def parse_json_list(raw_value):
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def parse_bool(raw_value):
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() == "true"


def parse_float(raw_value):
    if raw_value is None or str(raw_value).strip() == "":
        return None
    try:
        return float(raw_value)
    except ValueError:
        return None


def parse_int(raw_value):
    if raw_value is None or str(raw_value).strip() == "":
        return None
    try:
        return int(float(raw_value))
    except ValueError:
        return None


def load_final_selections():
    """
    Load final chosen video per song from youtube_matching_final_all_songs.csv
    (or fallback to youtube_matching_results.csv).
    """
    selections = {}

    if os.path.exists(FINAL_SELECTED_FILE):
        with open(FINAL_SELECTED_FILE, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                track_id = row.get("spotify_track_id")
                if not track_id:
                    continue
                raw_status = row.get("match_status", "")
                if "automatic" in raw_status:
                    decision_status = "automatic"
                    match_method = "youtube_search"
                elif row.get("youtube_video_id"):
                    decision_status = "manual_selected"
                    match_method = "manual_review"
                else:
                    decision_status = "no_confident_match"
                    match_method = "youtube_search"

                selections[track_id] = {
                    "selected_video_id": row.get("youtube_video_id") or None,
                    "selected_candidate_number": parse_int(row.get("selected_candidate_number")),
                    "decision_status": decision_status,
                    "match_method": match_method,
                }

    elif os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                track_id = row.get("spotify_track_id")
                if not track_id:
                    continue
                selections[track_id] = {
                    "selected_video_id": row.get("youtube_video_id") or None,
                    "selected_candidate_number": None,
                    "decision_status": row.get("status") or "no_confident_match",
                    "match_method": row.get("match_method") or "youtube_search",
                }

    return selections


def build_mapping_records():
    selections = load_final_selections()
    record_map = {}

    with open(CANDIDATES_FILE, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            track_id = row["spotify_track_id"]
            cand_num = parse_int(row["candidate_number"])
            video_id = row.get("youtube_video_id") or None
            sp_title = row.get("spotify_title", "")
            sp_artist = row.get("spotify_artist", "")
            yt_title = row.get("youtube_title", "")

            identity_ev = parse_json_list(row.get("identity_evidence"))
            source_ev = parse_json_list(row.get("source_evidence"))

            sel_info = selections.get(track_id, {})
            selected_vid = sel_info.get("selected_video_id")
            selected_cnum = sel_info.get("selected_candidate_number")
            decision_status = sel_info.get("decision_status", "no_confident_match")
            match_method = sel_info.get("match_method", "youtube_search")

            is_selected = False
            if selected_cnum is not None and cand_num == selected_cnum:
                is_selected = True
            elif selected_cnum is None and selected_vid and video_id == selected_vid:
                is_selected = True

            if is_selected:
                row_status = "success"
            elif selected_vid is None:
                row_status = "not_found"
            else:
                row_status = "rejected"

            v_conflict = has_version_conflict(
                sp_title,
                yt_title,
                spotify_artist=sp_artist,
            )

            official_flag = is_official_source(source_ev, identity_ev)

            key = (track_id, cand_num)
            record_map[key] = {
                "spotify_track_id": track_id,
                "candidate_number": cand_num,
                "is_selected": is_selected,
                "youtube_video_id": video_id,
                "youtube_title": yt_title,
                "youtube_channel": row.get("youtube_channel", ""),
                "spotify_duration_ms": parse_int(row.get("spotify_duration_ms")),
                "youtube_duration": parse_float(row.get("youtube_duration")),
                "title_similarity": parse_float(row.get("title_similarity")),
                "title_conflict": parse_bool(row.get("title_conflict")),
                "version_conflict": v_conflict,
                "identity_evidence": identity_ev,
                "source_evidence": source_ev,
                "duration_difference_ratio": parse_float(row.get("duration_difference_ratio")),
                "hard_invalid": parse_bool(row.get("hard_invalid")),
                "match_method": match_method if is_selected else "youtube_search",
                "is_official": official_flag,
                "decision_status": decision_status,
                "status": row_status,
            }

    return list(record_map.values())


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing from .env")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    records = build_mapping_records()

    print(f"Total youtube_mapping records prepared: {len(records)}")
    selected_count = sum(1 for r in records if r["is_selected"])
    print(f"Selected (status='success') songs: {selected_count}")

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]
        (
            supabase
            .table("youtube_mapping")
            .upsert(batch, on_conflict="spotify_track_id,candidate_number")
            .execute()
        )
        print(f"Upserted batch {start + 1}..{start + len(batch)} / {len(records)}")

    print("===== SUPABASE UPLOAD COMPLETE =====")


if __name__ == "__main__":
    main()
