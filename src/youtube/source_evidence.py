import re

from identity_evidence import get_identity_evidence


OFFICIAL_CHANNEL_PATTERNS = [
    r"\bofficial\b",
    r"\bentertainment\b",
    r"\brecords?\b",
    r"\blabels?\b",
    r"\bcontents?\b",
    r"\bmedia\b",
    r"\bproduction\b",
    r"\bsmtown\b",
    r"\bbangtantv\b",
    r"\b1thek\b",
    r"\bstarshiptv\b",
    r"\baomg\b",
    r"\b88rising\b",
    r"\bstone\s+music\b",
    r"\buniversal\s+music\b",
    r"\bsony\s+music\b",
    r"\bwarner\s+music\b",
    r"\bgenie\s+music\b",
]

FAN_CHANNEL_INDICATORS = [
    r"\bcrew\b",
    r"\bfan\b",
    r"\bbackup\b",
    r"\bleaks\b",
    r"\blyrics?\b",
    r"\bhype\b",
    r"\bvibes\b",
    r"\bclouds\b",
    r"\bclean\s+music\b",
    r"\bclean\s+audio\b",
    r"\bnew\s+music\b",
    r"\bsub\b",
    r"\bvietsub\b",
    r"\bengsub\b",
    r"\bcolor\s*coded\b",
    r"\barchive\b",
    r"\bchannel\b",
]


VEVO_CHANNEL_PATTERN = r"vevo$"


TOPIC_PATTERN = r"\btopic\b"


OFFICIAL_TITLE_PATTERNS = [
    (
        r"\bofficial\s+music\s+video\b",
        "official_music_video",
    ),
    (
        r"\bofficial\s+m\s*/?\s*v\b",
        "official_music_video",
    ),
    (
        r"\bofficial\s+video\b",
        "official_video",
    ),
    (
        r"\bofficial\s+audio\b",
        "official_audio",
    ),
    (
        r"\bofficial\s+lyric\s+video\b",
        "official_lyric_video",
    ),
    (
        r"\bofficial\s+live\s+(?:performance|video)\b",
        "official_live",
    ),
    (
        r"\bofficial\s+performance\b",
        "official_live",
    ),
    (
        r"\bvisualizer\b",
        "visualizer",
    ),
    (
        r"\blyric\s+video\b",
        "lyric_video",
    ),
    (
        r"\blyrics?\b",
        "lyrics",
    ),
    (
        r"\bm\s*/\s*v\b",
        "music_video",
    ),
    (
        r"\bmv\b",
        "music_video",
    ),
]

DOWNGRADED_UNVERIFIED_SOURCE = {
    "official_music_video": "music_video",
    "official_video": "music_video",
    "official_audio": "lyrics",
    "official_lyric_video": "lyric_video",
    "official_live": "lyrics",
}


def normalize_source_text(text):
    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def is_verified_channel_for_artist(youtube_channel, spotify_artist, evidence):
    """
    Verify that the YouTube channel is genuinely an official/artist/label/Topic channel
    before trusting 'Official Audio' / 'Official Video' claims in the video title.
    """
    if not spotify_artist:
        return True

    channel_norm = normalize_source_text(youtube_channel)
    if any(re.search(p, channel_norm) for p in FAN_CHANNEL_INDICATORS):
        return False

    if "topic_channel" in evidence or "official_channel" in evidence:
        return True

    id_ev = get_identity_evidence(spotify_artist, "", youtube_channel)
    if "exact_channel_artist" in id_ev or "artist_in_channel" in id_ev:
        return True

    return False


def get_source_evidence(
    youtube_title,
    youtube_channel,
    spotify_artist=None,
):
    title = normalize_source_text(
        youtube_title
    )

    channel = normalize_source_text(
        youtube_channel
    )

    evidence = []

    if re.search(
        TOPIC_PATTERN,
        channel,
    ):
        evidence.append(
            "topic_channel"
        )

    is_fan_channel = any(
        re.search(p, channel) for p in FAN_CHANNEL_INDICATORS
    )

    if not is_fan_channel and any(
        re.search(pattern, channel)
        for pattern in OFFICIAL_CHANNEL_PATTERNS
    ):
        evidence.append(
            "official_channel"
        )

    if (
        not is_fan_channel
        and re.search(
            VEVO_CHANNEL_PATTERN,
            channel,
        )
        and "official_channel" not in evidence
    ):
        evidence.append(
            "official_channel"
        )

    verified_channel = is_verified_channel_for_artist(
        youtube_channel,
        spotify_artist,
        evidence,
    )

    for pattern, evidence_name in OFFICIAL_TITLE_PATTERNS:
        if re.search(
            pattern,
            title,
        ):
            if not verified_channel and evidence_name in DOWNGRADED_UNVERIFIED_SOURCE:
                evidence.append(DOWNGRADED_UNVERIFIED_SOURCE[evidence_name])
            else:
                evidence.append(evidence_name)
            break

    return evidence