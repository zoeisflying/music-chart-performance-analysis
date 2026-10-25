import json
import os
import re
import time
from collections import Counter

try:
    from langdetect import detect
    from langdetect.lang_detect_exception import LangDetectException
    from langdetect import DetectorFactory
    DetectorFactory.seed = 0
except ImportError:
    print("Chưa cài langdetect. Chạy: pip install langdetect")
    raise

RESULT_FILE = "data/raw/lyrics_collection_results.json"
LYRICS_FOLDER = "data/raw/lyrics"
CHECKPOINT_FILE = "data/raw/language_detection_v2_checkpoint.json"

MIN_TEXT_LENGTH = 15
MAIN_LANGUAGE_THRESHOLD = 0.70
MIXED_THRESHOLD = 0.30

# Các nhãn/metadata của Genius không phải nội dung lyrics.
SECTION_PATTERN = re.compile(
    r"^\s*\[(?:verse|pre-chorus|chorus|post-chorus|bridge|intro|outro|hook|refrain|instrumental|interlude|break|part|spoken)[^\]]*\]\s*$",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_atomic(path, data):
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def clean_line(line):
    """Remove Genius/markdown metadata while keeping actual lyric text."""
    line = line.strip()
    if not line:
        return ""

    # Bỏ section labels: [Verse 1], [Chorus], ...
    if SECTION_PATTERN.match(line):
        return ""

    # [text](url) -> text
    line = MARKDOWN_LINK_PATTERN.sub(r"\1", line)

    # Xóa URL còn sót lại
    line = URL_PATTERN.sub("", line)

    # Một số Genius lines có [text] nhưng không phải section label.
    # Giữ text bên trong ngoặc để không mất lyrics.
    line = BRACKET_PATTERN.sub(r"\1", line)

    return line.strip()


def clean_lyrics(text):
    lines = []
    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        if line:
            lines.append(line)
    return lines


def count_script_chars(text):
    counts = Counter()
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F:
            counts["ko"] += 1
        elif (
            0x3040 <= code <= 0x30FF
            or 0x31F0 <= code <= 0x31FF
            or 0xFF66 <= code <= 0xFF9D
        ):
            counts["ja"] += 1
        elif 0x4E00 <= code <= 0x9FFF:
            counts["zh"] += 1
    return counts


def latin_letter_count(text):
    return len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]", text))


def detect_line_language(line):
    """Detect a lyric line using script first, langdetect second."""
    script_counts = count_script_chars(line)
    script_total = sum(script_counts.values())

    # Nếu một script chiếm phần lớn ký tự script thì ưu tiên nó.
    if script_total > 0:
        top_script, top_count = script_counts.most_common(1)[0]
        if top_count / script_total >= 0.60:
            return top_script

    # Dòng không có đủ chữ thì bỏ qua.
    if latin_letter_count(line) < MIN_TEXT_LENGTH and script_total < MIN_TEXT_LENGTH:
        return None

    try:
        return detect(line)
    except LangDetectException:
        return None
    except Exception:
        return None


def detect_language(lyrics_text):
    lines = clean_lyrics(lyrics_text)

    weighted_counts = Counter()
    total_weight = 0

    for line in lines:
        language = detect_line_language(line)
        if not language:
            continue

        # Dùng số ký tự chữ làm trọng số thay vì mỗi dòng = 1.
        # Điều này giảm ảnh hưởng của các dòng cực ngắn như "Oh", "Yeah".
        weight = latin_letter_count(line) + sum(count_script_chars(line).values())
        if weight < MIN_TEXT_LENGTH:
            continue

        weighted_counts[language] += weight
        total_weight += weight

    if total_weight == 0:
        return "unknown", {}

    distribution = {
        lang: round(count / total_weight, 4)
        for lang, count in weighted_counts.most_common()
    }

    ranked = weighted_counts.most_common()
    top_lang, top_count = ranked[0]
    top_ratio = top_count / total_weight

    # 1 ngôn ngữ chiếm >= 70% -> main language
    if top_ratio >= MAIN_LANGUAGE_THRESHOLD:
        return top_lang, distribution

    # 2 ngôn ngữ cùng >= 30% -> mixed
    significant = [
        lang for lang, count in ranked
        if count / total_weight >= MIXED_THRESHOLD
    ]
    if len(significant) >= 2:
        return "mixed", distribution

    # Không đủ rõ ràng: lấy ngôn ngữ đứng đầu.
    return top_lang, distribution


def get_lyrics_text(item, track_id):
    lyrics_file = item.get("lyrics_file")
    if lyrics_file:
        path = lyrics_file.replace("\\", os.sep)
    else:
        path = os.path.join(LYRICS_FOLDER, f"{track_id}.txt")

    if not os.path.exists(path):
        fallback = os.path.join(LYRICS_FOLDER, f"{track_id}.txt")
        if os.path.exists(fallback):
            path = fallback
        else:
            return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return {}
    return load_json(CHECKPOINT_FILE)


def main():
    results = load_json(RESULT_FILE)
    checkpoint = load_checkpoint()

    print(f"Tổng số records: {len(results)}")
    print(f"Đã có checkpoint: {len(checkpoint)}")
    print("Language detection v2: clean lyrics + script detection + weighted lines")

    success_records = [
        (track_id, item)
        for track_id, item in results.items()
        if item.get("lyrics_status") == "success"
    ]

    for index, (track_id, item) in enumerate(success_records, start=1):
        if track_id in checkpoint:
            print(f"\n[{index}/{len(success_records)}] SKIP: {item.get('title')}")
            continue

        print(f"\n[{index}/{len(success_records)}]")
        print(f"Title: {item.get('title')}")
        print(f"Artist: {item.get('artist')}")

        lyrics_text = get_lyrics_text(item, track_id)
        if not lyrics_text:
            item["language"] = "unknown"
            checkpoint[track_id] = "unknown"
            print("  Language: unknown (lyrics file not found)")
            save_json_atomic(CHECKPOINT_FILE, checkpoint)
            save_json_atomic(RESULT_FILE, results)
            continue

        language, distribution = detect_language(lyrics_text)
        item["language"] = language
        checkpoint[track_id] = language

        print(f"  Language: {language}")
        print(f"  Distribution: {distribution}")

        save_json_atomic(CHECKPOINT_FILE, checkpoint)
        save_json_atomic(RESULT_FILE, results)
        time.sleep(0.05)

    print("\n" + "=" * 60)
    print("LANGUAGE DETECTION V2 COMPLETED")
    print("=" * 60)
    print(f"Success records processed: {len(success_records)}")
    print(f"Checkpoint: {CHECKPOINT_FILE}")
    print(f"Results: {RESULT_FILE}")


if __name__ == "__main__":
    main()
