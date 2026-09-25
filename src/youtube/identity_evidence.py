import re

from rapidfuzz import fuzz
from title_normalizer import normalize_title


def normalize_artist(text):
    """
    Normalize an artist/channel name for comparison.
    """
    if not text:
        return ""

    text = normalize_title(text)

    return text.strip()


def clean_channel_for_exact_artist(channel_text):
    """
    Strip common YouTube channel suffixes/badges (e.g. '- Topic', 'Official', 'VEVO',
    Korean script accompaniment) to check if the channel belongs directly to the artist.
    """
    if not channel_text:
        return ""

    text = channel_text.strip()
    text = re.sub(r"\s*[-–—]\s*topic\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"vevo$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bofficial\b", " ", text, flags=re.IGNORECASE)
    # Remove Korean characters if Latin artist name is also present
    if re.search(r"[A-Za-z]", text):
        text = re.sub(r"[가-힣]+", " ", text)

    return normalize_artist(text)


def artist_similarity(
    spotify_artist,
    youtube_artist,
):
    """
    Compare Spotify artist with YouTube channel/artist text.

    Returns:
        float similarity in the range 0-100
        or None when either value is missing.
    """
    spotify_normalized = normalize_artist(
        spotify_artist
    )

    youtube_normalized = normalize_artist(
        youtube_artist
    )

    if not spotify_normalized or not youtube_normalized:
        return None

    return float(
        fuzz.ratio(
            spotify_normalized,
            youtube_normalized,
        )
    )


def artist_name_in_text(
    spotify_artist,
    text,
):
    """
    Check whether the normalized Spotify artist name
    appears as a complete phrase inside the text.
    """
    artist = normalize_artist(spotify_artist)
    normalized_text = normalize_artist(text)

    if not artist or not normalized_text:
        return False

    pattern = rf"\b{re.escape(artist)}\b"

    if re.search(pattern, normalized_text):
        return True

    # Space-insensitive check for multi-char artist names (e.g. KANGDANIEL vs KANG DANIEL, ImagineDragons vs Imagine Dragons)
    compact_artist = re.sub(r"\s+", "", artist)
    compact_text = re.sub(r"\s+", "", normalized_text)
    if len(compact_artist) >= 5 and compact_artist in compact_text:
        return True

    return False


def get_identity_evidence(
    spotify_artist,
    youtube_title,
    youtube_channel,
):
    """
    Collect transparent identity evidence.

    Evidence types:
        exact_channel_artist
        artist_in_channel
        artist_in_title
    """

    evidence = []

    artist = normalize_artist(
        spotify_artist
    )

    channel = normalize_artist(
        youtube_channel
    )

    title = normalize_artist(
        youtube_title
    )

    if not artist:
        return evidence

    if channel:
        similarity = artist_similarity(
            artist,
            channel,
        )

        cleaned_channel = clean_channel_for_exact_artist(youtube_channel)
        compact_artist = re.sub(r"\s+", "", artist)
        compact_channel = re.sub(r"\s+", "", cleaned_channel)

        if (
            similarity == 100.0
            or (cleaned_channel and cleaned_channel == artist)
            or (len(compact_artist) >= 3 and compact_artist == compact_channel)
        ):
            evidence.append(
                "exact_channel_artist"
            )
            if re.search(r"\btopic\b", youtube_channel or "", flags=re.IGNORECASE):
                evidence.append("artist_in_channel")

        elif artist_name_in_text(
            artist,
            youtube_channel,
        ):
            evidence.append(
                "artist_in_channel"
            )
        else:
            artist_agency_channels = {
                "bts": ("bangtantv", "bighit music", "hybe labels"),
                "agust d": ("bangtantv", "bighit music", "hybe labels"),
                "v": ("bangtantv", "bighit music", "hybe labels"),
                "jungkook": ("bangtantv", "bighit music", "hybe labels"),
                "jimin": ("bangtantv", "bighit music", "hybe labels"),
                "jin": ("bangtantv", "bighit music", "hybe labels"),
                "rm": ("bangtantv", "bighit music", "hybe labels"),
                "j hope": ("bangtantv", "bighit music", "hybe labels"),
                "rosé": ("blackpink", "yg entertainment"),
                "lisa": ("blackpink", "yg entertainment", "lloud"),
                "jennie": ("blackpink", "yg entertainment"),
                "blackpink": ("yg entertainment",),
                "twice": ("jyp entertainment",),
                "nct u": ("smtown", "nct"),
                "nct dream": ("smtown", "nct dream"),
                "aespa": ("smtown",),
                "exo": ("smtown",),
                "shinee": ("smtown",),
                "taemin": ("smtown",),
                "iz one": ("stone music", "official iz one"),
                "brave girls": ("1thek", "brave entertainment"),
                "iu": ("이지금", "1thek", "edam"),
            }
            for agency in artist_agency_channels.get(artist, ()):
                if agency in (youtube_channel or "").lower():
                    evidence.append("artist_in_channel")
                    break

    if artist_name_in_text(
        artist,
        youtube_title,
    ):
        evidence.append(
            "artist_in_title"
        )

    return evidence