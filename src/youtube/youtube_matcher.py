import re


def normalize_text(text):
    """
    Normalize text for general matching.

    Example:
        "Song A (Official Video)" -> "song a official video"
    """

    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def is_hard_invalid_source(title):
    """
    Reject sources that clearly do not represent
    the artist's charted recording.

    Cover and karaoke sources are treated as hard-invalid.

    Remix/live/acoustic/slowed/sped-up/instrumental
    are NOT automatically rejected.
    """

    normalized = normalize_text(title)

    invalid_patterns = [
        r"\bcover\b",
        r"\bkaraoke\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in invalid_patterns
    )