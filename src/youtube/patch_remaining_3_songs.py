import os
import csv
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Erroneous IDs from earlier test
wrong_ids = ["0k1WUmIRnGevOj4ajyKtYG", "0WvBRw00gR7wXkQWj42n7K", "4C6U5NNG7KHnfRukjoIpZa"]
supabase.table("youtube_mapping").delete().in_("spotify_track_id", wrong_ids).execute()
supabase.table("songs").delete().in_("spotify_track_id", wrong_ids).execute()
print("Cleaned wrong IDs from Supabase!")

# 2. Correct 15 candidates with the real track IDs from songs table
real_candidates = [
    # Drake - Way 2 Sexy (0k1WUmIRnG3xU6fvvDVfRG)
    {
        "spotify_track_id": "0k1WUmIRnG3xU6fvvDVfRG",
        "candidate_number": 1,
        "is_selected": True,
        "youtube_video_id": "Qr2PWFDB4ZU",
        "youtube_title": "Drake - Way 2 Sexy (Audio) ft. Future, Young Thug",
        "youtube_channel": "Drake",
        "spotify_duration_ms": 257604,
        "youtube_duration": 258.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_audio"],
        "duration_difference_ratio": 0.0015,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "automatic",
        "status": "success",
    },
    {
        "spotify_track_id": "0k1WUmIRnG3xU6fvvDVfRG",
        "candidate_number": 2,
        "is_selected": False,
        "youtube_video_id": "vX9msKu75qs",
        "youtube_title": "Drake ft. Future and Young Thug - Way 2 Sexy (Official Video)",
        "youtube_channel": "Drake",
        "spotify_duration_ms": 257604,
        "youtube_duration": 281.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_video"],
        "duration_difference_ratio": 0.0908,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "0k1WUmIRnG3xU6fvvDVfRG",
        "candidate_number": 3,
        "is_selected": False,
        "youtube_video_id": "6yWSdQNQ9ac",
        "youtube_title": "Drake - Way 2 Sexy (Lyrics) ft. Future, Young Thug",
        "youtube_channel": "Creative Chaos",
        "spotify_duration_ms": 257604,
        "youtube_duration": 258.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": ["lyrics"],
        "duration_difference_ratio": 0.0015,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "0k1WUmIRnG3xU6fvvDVfRG",
        "candidate_number": 4,
        "is_selected": False,
        "youtube_video_id": "J3qSrKvu9wo",
        "youtube_title": "Drake ft Kawhi Leonard & Future - Way too Sexy",
        "youtube_channel": "All Capital Yow",
        "spotify_duration_ms": 257604,
        "youtube_duration": 26.0,
        "title_similarity": 80.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": [],
        "duration_difference_ratio": 0.899,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "0k1WUmIRnG3xU6fvvDVfRG",
        "candidate_number": 5,
        "is_selected": False,
        "youtube_video_id": "I3zKrRCy6vs",
        "youtube_title": "Kawhi Leonard in Drake's Music Video",
        "youtube_channel": "Fruit Punch Official",
        "spotify_duration_ms": 257604,
        "youtube_duration": 25.0,
        "title_similarity": 40.0,
        "title_conflict": True,
        "version_conflict": False,
        "identity_evidence": [],
        "source_evidence": [],
        "duration_difference_ratio": 0.903,
        "hard_invalid": True,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },

    # Drake - Pussy & Millions (2KLwPaRDOB87XOYAT2fgxh)
    {
        "spotify_track_id": "2KLwPaRDOB87XOYAT2fgxh",
        "candidate_number": 1,
        "is_selected": True,
        "youtube_video_id": "8LpAtRIakkk",
        "youtube_title": "Drake, 21 Savage - Pussy & Millions (Audio) ft. Travis Scott",
        "youtube_channel": "Drake",
        "spotify_duration_ms": 242026,
        "youtube_duration": 243.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_audio"],
        "duration_difference_ratio": 0.004,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "automatic",
        "status": "success",
    },
    {
        "spotify_track_id": "2KLwPaRDOB87XOYAT2fgxh",
        "candidate_number": 2,
        "is_selected": False,
        "youtube_video_id": "UCDv0tWLjDM",
        "youtube_title": "Drake & 21 Savage - Pussy & Millions ft. Travis Scott",
        "youtube_channel": "Cash Money Records",
        "spotify_duration_ms": 242026,
        "youtube_duration": 243.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": ["official_channel"],
        "duration_difference_ratio": 0.004,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2KLwPaRDOB87XOYAT2fgxh",
        "candidate_number": 3,
        "is_selected": False,
        "youtube_video_id": "2q__v7JbSyA",
        "youtube_title": "[Lyrics + Vietsub] Drake, 21 Savage - Pussy & Millions ft. Travis Scott",
        "youtube_channel": "Hoang Sub",
        "spotify_duration_ms": 242026,
        "youtube_duration": 243.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": ["lyrics"],
        "duration_difference_ratio": 0.004,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2KLwPaRDOB87XOYAT2fgxh",
        "candidate_number": 4,
        "is_selected": False,
        "youtube_video_id": "1AdoP1Fz1OA",
        "youtube_title": "Drake, 21 Savage - Pussy & Millions feat. Travis Scott (Audio)",
        "youtube_channel": "Hits & Lyrics",
        "spotify_duration_ms": 242026,
        "youtube_duration": 243.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": ["lyrics"],
        "duration_difference_ratio": 0.004,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2KLwPaRDOB87XOYAT2fgxh",
        "candidate_number": 5,
        "is_selected": False,
        "youtube_video_id": "-qOZb_UJLNY",
        "youtube_title": "Drake - Pussy & Millions (Travis Scott Verse only)",
        "youtube_channel": "Jorge",
        "spotify_duration_ms": 242026,
        "youtube_duration": 81.0,
        "title_similarity": 75.0,
        "title_conflict": False,
        "version_conflict": True,
        "identity_evidence": ["artist_in_title"],
        "source_evidence": [],
        "duration_difference_ratio": 0.665,
        "hard_invalid": True,
        "match_method": "youtube_search",
        "is_official": False,
        "decision_status": "automatic",
        "status": "rejected",
    },

    # Nicki Minaj - Super Freaky Girl (2yjlYDiNiQkdxVqTlaSrlX)
    {
        "spotify_track_id": "2yjlYDiNiQkdxVqTlaSrlX",
        "candidate_number": 1,
        "is_selected": True,
        "youtube_video_id": "j5uAR9w7LBg",
        "youtube_title": "Nicki Minaj - Super Freaky Girl (Official Music Video)",
        "youtube_channel": "Nicki Minaj",
        "spotify_duration_ms": 170977,
        "youtube_duration": 230.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_music_video"],
        "duration_difference_ratio": 0.345,
        "hard_invalid": False,
        "match_method": "manual_review",
        "is_official": True,
        "decision_status": "manual_selected",
        "status": "success",
    },
    {
        "spotify_track_id": "2yjlYDiNiQkdxVqTlaSrlX",
        "candidate_number": 2,
        "is_selected": False,
        "youtube_video_id": "q6dM07r8j_Q",
        "youtube_title": "Super Freaky Girl (Queen Mix) - Nicki Minaj",
        "youtube_channel": "Nicki Minaj",
        "spotify_duration_ms": 170977,
        "youtube_duration": 230.0,
        "title_similarity": 80.0,
        "title_conflict": False,
        "version_conflict": True,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_channel"],
        "duration_difference_ratio": 0.345,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "manual_selected",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2yjlYDiNiQkdxVqTlaSrlX",
        "candidate_number": 3,
        "is_selected": False,
        "youtube_video_id": "oV85_d8-s4c",
        "youtube_title": "Super Freaky Girl (Roman Remix) - Nicki Minaj",
        "youtube_channel": "Nicki Minaj",
        "spotify_duration_ms": 170977,
        "youtube_duration": 230.0,
        "title_similarity": 80.0,
        "title_conflict": False,
        "version_conflict": True,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_channel"],
        "duration_difference_ratio": 0.345,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "manual_selected",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2yjlYDiNiQkdxVqTlaSrlX",
        "candidate_number": 4,
        "is_selected": False,
        "youtube_video_id": "Yp69Rk5R328",
        "youtube_title": "Nicki Minaj - Super Freaky Girl (Official Lyric Video)",
        "youtube_channel": "Nicki Minaj",
        "spotify_duration_ms": 170977,
        "youtube_duration": 171.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_lyric_video"],
        "duration_difference_ratio": 0.0001,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "manual_selected",
        "status": "rejected",
    },
    {
        "spotify_track_id": "2yjlYDiNiQkdxVqTlaSrlX",
        "candidate_number": 5,
        "is_selected": False,
        "youtube_video_id": "46c7iJ154Wk",
        "youtube_title": "Nicki Minaj - Super Freaky Girl (Official Audio)",
        "youtube_channel": "Nicki Minaj",
        "spotify_duration_ms": 170977,
        "youtube_duration": 171.0,
        "title_similarity": 100.0,
        "title_conflict": False,
        "version_conflict": False,
        "identity_evidence": ["exact_channel_artist", "artist_in_title"],
        "source_evidence": ["official_audio"],
        "duration_difference_ratio": 0.0001,
        "hard_invalid": False,
        "match_method": "youtube_search",
        "is_official": True,
        "decision_status": "manual_selected",
        "status": "rejected",
    },
]

supabase.table("youtube_mapping").upsert(
    real_candidates, on_conflict="spotify_track_id,candidate_number"
).execute()
print("Upserted 15 candidates for real track IDs!")

tot = supabase.table("youtube_mapping").select("id", count="exact").execute()
sel = supabase.table("youtube_selected_mapping").select("id", count="exact").execute()
print("Confirmed total rows in youtube_mapping on Supabase:", tot.count)
print("Confirmed total selected rows in youtube_selected_mapping on Supabase:", sel.count)

# Clean and sync local CSVs
cand_file = "data/sampling/youtube_matching_candidates.csv"
with open(cand_file, "r", encoding="utf-8-sig", newline="") as f:
    rows = [r for r in csv.DictReader(f) if r["spotify_track_id"] not in wrong_ids]
    fieldnames = list(rows[0].keys())

existing = {(r["spotify_track_id"], r["candidate_number"]) for r in rows}
for c in real_candidates:
    key = (c["spotify_track_id"], str(c["candidate_number"]))
    if key not in existing:
        rows.append({
            "spotify_track_id": c["spotify_track_id"],
            "spotify_title": c["youtube_title"].split(" - ")[-1].split(" (")[0],
            "spotify_artist": c["youtube_channel"],
            "spotify_duration_ms": c["spotify_duration_ms"],
            "candidate_number": c["candidate_number"],
            "youtube_video_id": c["youtube_video_id"],
            "youtube_title": c["youtube_title"],
            "youtube_channel": c["youtube_channel"],
            "youtube_duration": c["youtube_duration"],
            "title_similarity": c["title_similarity"],
            "title_conflict": c["title_conflict"],
            "identity_evidence": json.dumps(c["identity_evidence"]),
            "source_evidence": json.dumps(c["source_evidence"]),
            "duration_difference_ratio": c["duration_difference_ratio"],
            "hard_invalid": c["hard_invalid"],
        })

with open(cand_file, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
print("Updated local candidates CSV. Total rows:", len(rows))

final_file = "data/sampling/youtube_matching_final_all_songs.csv"
with open(final_file, "r", encoding="utf-8-sig", newline="") as f:
    f_rows = [r for r in csv.DictReader(f) if r["spotify_track_id"] not in wrong_ids]
    f_fieldnames = list(f_rows[0].keys())

f_tracks = {r["spotify_track_id"] for r in f_rows}
for c in [c for c in real_candidates if c["is_selected"]]:
    if c["spotify_track_id"] not in f_tracks:
        vid = c["youtube_video_id"]
        dur_diff = round(c["youtube_duration"] - (c["spotify_duration_ms"] / 1000), 1)
        f_rows.append({
            "spotify_track_id": c["spotify_track_id"],
            "spotify_artist": c["youtube_channel"],
            "spotify_title": c["youtube_title"].split(" - ")[-1].split(" (")[0],
            "spotify_duration_sec": round(c["spotify_duration_ms"] / 1000, 1),
            "match_status": c["decision_status"],
            "selected_candidate_number": c["candidate_number"],
            "youtube_video_id": vid,
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "youtube_title": c["youtube_title"],
            "youtube_channel": c["youtube_channel"],
            "youtube_duration_sec": c["youtube_duration"],
            "duration_diff_sec": dur_diff,
            "audio_note": "Auto-accepted confident match" if c["decision_status"] == "automatic" else "Manual selected",
        })

with open(final_file, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=f_fieldnames)
    w.writeheader()
    w.writerows(f_rows)
print("Updated local final all songs CSV. Total rows:", len(f_rows))
