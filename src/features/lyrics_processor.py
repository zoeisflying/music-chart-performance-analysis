
import os
import re
import json
import unicodedata
import pandas as pd


# ==========================================
# 1. CONFIGURATION
# ==========================================

INPUT_FILE = "data/processed/modeling_dataset.csv"
LYRICS_FOLDER = "data/raw/lyrics"
OUTPUT_FILE = "data/processed/lyrics_features_recomputed.csv"

FEATURE_COLUMNS = [
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


# ==========================================
# 2. LANGUAGE PRONOUN LISTS
# ==========================================

PRONOUNS = {
    "en": {
        "i", "me", "my", "mine", "myself",
        "you", "your", "yours", "yourself",
        "he", "him", "his", "himself",
        "she", "her", "hers", "herself",
        "it", "its", "itself",
        "we", "us", "our", "ours", "ourselves",
        "they", "them", "their", "theirs", "themselves"
    },
    "vi": {
        "tôi", "ta", "tao", "mình", "tớ",
        "bạn", "cậu", "mày", "anh", "em",
        "chị", "chúng", "chúng tôi", "chúng ta",
        "họ", "nó", "người"
    },
    "ko": {
        "나", "너", "우리", "저", "당신",
        "그", "그녀", "그들", "내", "네",
        "저희", "너희"
    }
}

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "vietnamese": "vi",
    "vi": "vi",
    "korean": "ko",
    "ko": "ko"
}


# ==========================================
# 3. LOAD LYRICS
# ==========================================

def load_lyrics(track_id):
    file_path = os.path.join(
        LYRICS_FOLDER,
        str(track_id) + ".txt"
    )

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# ==========================================
# 4. CLEAN LYRICS
# ==========================================

def clean_lyrics(raw_lyrics):
    if not raw_lyrics:
        return ""

    lines = raw_lyrics.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Remove timestamps at the beginning of a line
        line = re.sub(
            r"^\[\d{1,2}:\d{2}(?:\.\d+)?\]\s*",
            "",
            line
        )

        # Remove section labels such as [Chorus], [Verse 1]
        if re.fullmatch(
            r"\[(?:verse|chorus|bridge|intro|outro|"
            r"pre[- ]chorus|hook|refrain)"
            r"(?:\s+\d+)?\]",
            line,
            flags=re.IGNORECASE
        ):
            continue

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ==========================================
# 5. TOKENIZE WORDS
# ==========================================

def tokenize(text):
    # Keep Unicode letters and apostrophes inside words
    pattern = r"[^\W\d_]+(?:['’][^\W\d_]+)*"

    return re.findall(pattern, text.lower())


# ==========================================
# 6. CALCULATE FEATURES
# ==========================================


def calculate_chorus_repetition(lines):
    """
    Estimate lyric repetition by counting repeated lines.
    This is an approximation, not guaranteed chorus detection.
    """

    normalized_lines = [
        " ".join(tokenize(line))
        for line in lines
    ]

    normalized_lines = [
        line for line in normalized_lines if line
    ]

    seen = set()
    repeated_count = 0

    for line in normalized_lines:
        if line in seen:
            repeated_count += 1
        else:
            seen.add(line)

    return repeated_count



def calculate_pronoun_ratio(words, language):
    language = str(language).strip().lower()

    language_code = LANGUAGE_ALIASES.get(language)

    if language_code is None:
        return None

    pronoun_list = PRONOUNS[language_code]

    pronoun_count = sum(
        1 for word in words
        if word in pronoun_list
    )

    if len(words) == 0:
        return None

    return pronoun_count / len(words)


def calculate_features(cleaned_lyrics, title, language):

    lines = [
        line.strip()
        for line in cleaned_lyrics.splitlines()
        if line.strip()
    ]

    words = tokenize(cleaned_lyrics)

    word_count = len(words)
    unique_word_count = len(set(words))

    if word_count > 0:
        lexical_diversity = unique_word_count / word_count
        repetition_ratio = 1 - lexical_diversity

        avg_word_length = sum(
            len(word.replace("'", "").replace("’", ""))
            for word in words
        ) / word_count
    else:
        lexical_diversity = None
        repetition_ratio = None
        avg_word_length = None

    line_count = len(lines)

    chorus_repetition_count = calculate_chorus_repetition(
        lines
    )

    title_words = set(tokenize(str(title)))
    lyrics_words = set(words)

    title_word_in_lyrics = (
        len(title_words.intersection(lyrics_words)) > 0
    )

    punctuation_count = sum(
        1 for char in cleaned_lyrics
        if unicodedata.category(char).startswith("P")
    )

    total_characters = sum(
        1 for char in cleaned_lyrics
        if not char.isspace()
    )

    if total_characters > 0:
        punctuation_ratio = (
            punctuation_count / total_characters
        )
    else:
        punctuation_ratio = None

    pronoun_ratio = calculate_pronoun_ratio(
        words, language
    )

    return {
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "lexical_diversity": lexical_diversity,
        "repetition_ratio": repetition_ratio,
        "avg_word_length": avg_word_length,
        "line_count": line_count,
        "chorus_repetition_count": chorus_repetition_count,
        "title_word_in_lyrics": title_word_in_lyrics,
        "punctuation_ratio": punctuation_ratio,
        "pronoun_ratio": pronoun_ratio
    }


# ==========================================
# 7. PROCESS DATASET
# ==========================================

def main():

    df = pd.read_csv(INPUT_FILE)

    results = []

    total = len(df)
    success_count = 0
    missing_count = 0

    for _, row in df.iterrows():

        track_id = row["spotify_track_id"]
        lyrics_status = row["lyrics_status"]

        result = {
            "spotify_track_id": track_id
        }

        # Only process tracks with successful lyrics
        if lyrics_status != "success":
            result.update({
                feature: None
                for feature in FEATURE_COLUMNS
            })

            result["processing_status"] = "skipped"
            results.append(result)
            continue

        raw_lyrics = load_lyrics(track_id)

        if raw_lyrics is None:
            result.update({
                feature: None
                for feature in FEATURE_COLUMNS
            })

            result["processing_status"] = "file_not_found"
            missing_count += 1
            results.append(result)
            continue

        cleaned_lyrics = clean_lyrics(raw_lyrics)

        features = calculate_features(
            cleaned_lyrics,
            row["title"],
            row["language"]
        )

        result.update(features)
        result["processing_status"] = "success"

        success_count += 1
        results.append(result)

    # Export to a separate CSV file
    output_df = pd.DataFrame(results)

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n========== PROCESSING SUMMARY ==========")
    print("Total tracks:", total)
    print("Successfully processed:", success_count)
    print("Missing lyrics files:", missing_count)
    print("Output:", OUTPUT_FILE)

    print("\nProcessing status:")
    print(output_df["processing_status"].value_counts())

    print("\nFirst 5 results:")
    print(output_df.head())


if __name__ == "__main__":
    main()
