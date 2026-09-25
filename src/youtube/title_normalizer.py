import re


# ============================================================
# 1. YOUTUBE PRESENTATION / SOURCE METADATA
# ============================================================

YOUTUBE_METADATA_PATTERNS = [
    r"\[20\d\d\s+festa\]",
    r"#\S+",
    r"\bofficial\s+music\s+video\b",
    r"\bofficial\s+video\b",
    r"\bofficial\s+audio\b",
    r"\bofficial\s+lyric\s+video\b",
    r"\bofficial\s+m\s*/?\s*v\b",
    r"\bcolor\s+coded(?:\s+lyrics?)?\b",
    r"\b(?:eng|rom|han|kan|kor|jpn|가사)(?:\s*[/|,_]\s*(?:eng|rom|han|kan|kor|jpn|sub|가사))+\b",
    r"\b(?:vietsub|engsub|korsub|eng\s+sub|kor\s+sub|日本語字幕)\b",
    r"\blyric\s+video\b",
    r"\blyrics?\b",
    r"\b가사\b",
    r"\baudio\b",
    r"\bvisualizer\b",
    r"\bm\s*/\s*v\b",
    r"\bmv\b",
    r"\bmusic\s+video\b",
    r"\bhq\b",
    r"\b4k\b",
    r"\bfull\s+hd\b",
    r"\bhd\b",
]


# ============================================================
# 2. VERSION / FEATURE METADATA
# ============================================================

FEATURE_CREDIT_PATTERNS = [
    r"\bfeat(?:uring)?\b\.?",
    r"\bft\b\.?",
    r"\bwith\b",
    r"\bprod\b\.?",
    r"\bproduced\s+by\b",
]

VERSION_MODIFIER_PATTERNS = [
    (r"\bremix\b", "remix"),
    (r"\bmega\s*mix\b", "remix"),
    (r"\blive\b", "live"),
    (r"\bperforms\b", "live"),
    (r"\bunplugged\b", "live"),
    (r"\b라이브\b", "live"),
    (r"\b공연\b", "live"),
    (r"\b무대\b", "live"),
    (r"\bspecial\s+stage\b", "live"),
    (r"\bcomeback\s+(?:special\s+)?stage\b", "live"),
    (r"\blate\s+show\b", "live"),
    (r"\btonight\s+show\b", "live"),
    (r"\btoday\s+show\b", "live"),
    (r"\bjimmy\s+fallon\b", "live"),
    (r"\bellen\s+degeneres\s+show\b", "live"),
    (r"\bplayathome\b", "live"),
    (r"\bsketchbook\b", "live"),
    (r"\binkigayo\b", "live"),
    (r"\b인기가요\b", "live"),
    (r"\bm\s*countdown\b", "live"),
    (r"\b엠카운트다운\b", "live"),
    (r"\bmusic\s*core\b", "live"),
    (r"\bmusic\s*bank\b", "live"),
    (r"\bshow\s+music\b", "live"),
    (r"\bimmortal\s+songs?\b", "live"),
    (r"\bopen\s+mic\b", "live"),
    (r"\btiny\s+desk\b", "live"),
    (r"\bfestival\b", "live"),
    (r"\bmuster\b", "live"),
    (r"\bworld\s+premiere\b", "live"),
    (r"\b(?:mma|mama)\s*20\d\d\b", "live"),
    (r"\b20\d\d\s*(?:mma|mama|sbs|kbs|mbc)\b", "live"),
    (r"\bgrammy(?:\s+awards|\b)", "live"),
    (r"\b(?:amas|vmas|bbmas)\b", "live"),
    (r"\biheart(?:radio)?\b", "live"),
    (r"@\s*(?:music\s+blood|the\s+tonight|the\s+\d+th|show|인기가요|7dream|sy\s+in|beyond\s+live|nct\s+127\s+world)", "live"),
    (r"\bfancam\b", "fancam"),
    (r"\b직캠\b", "fancam"),
    (r"\b예능연구소\b", "fancam"),
    (r"\bbe\s+original\b", "studio_choom"),
    (r"\bstudio\s+choom\b", "studio_choom"),
    (r"\bspecial\s+clip\b", "special_clip"),
    (r"\b스페셜클립\b", "special_clip"),
    (r"\btrack\s+video\b", "track_video"),
    (r"\bprologue\b", "teaser"),
    (r"\bteaser\b", "teaser"),
    (r"\bdocumentary\b", "documentary"),
    (r"\bfull\s+album\b", "full_album"),
    (r"\bplaylist\b", "playlist"),
    (r"\bconcert\b", "concert"),
    (r"\btour\b", "tour"),
    (r"\bacoustic\b", "acoustic"),
    (r"\binstrumental\b", "instrumental"),
    (r"\binst\.?(?=\s*$|\s*[\)\]])", "instrumental"),
    (r"\bsped\s*up\b", "sped_up"),
    (r"\bslowed\b", "slowed"),
    (r"\breverb\b", "reverb"),
    (r"\bnightcore\b", "nightcore"),
    (r"\b8d\b", "8d_audio"),
    (r"\bdance\s+practice\b", "dance_practice"),
    (r"\bdance\s+ver\.?\b", "dance_practice"),
    (r"\bdance\s+performance\b", "dance_practice"),
    (r"\bdance\s+mirror(?:ed)?\b", "dance_practice"),
    (r"\bchoreography\b", "dance_practice"),
    (r"\b안무영상\b", "dance_practice"),
    (r"\b교차편집\b", "stage_mix"),
    (r"\bstage\s+mix\b", "stage_mix"),
    (r"\bstage\s+ver\.?\b", "performance_ver"),
    (r"\bperformance\s+ver\.?\b", "performance_ver"),
    (r"\bperformance\s+video\b", "performance_ver"),
    (r"\bspecial\s+performance\b", "performance_ver"),
    (r"\bofficial\s+performance\b", "performance_ver"),
    (r"\bperformance\b", "performance_ver"),
    (r"\bprime\s+day\s+show\b", "live"),
    (r"\bband\s+(?:live\s+)?ver\.?\b", "band_ver"),
    (r"\benglish\s+ver\.?\b", "english_ver"),
    (r"\bjapanese\s+ver\.?\b", "japanese_ver"),
    (r"\bmidnight\s+version\b", "midnight_ver"),
    (r"\bclean(?:\s*[-/]\s*lyric|\s+version)?\b", "clean_ver"),
    (r"\bnicer\b", "clean_ver"),
    (r"\bextended(?:\s+version|\s+ver\.?)?\b", "extended"),
    (r"\b\d+\s*hours?\b", "loop"),
    (r"\bloop\b", "loop"),
    (r"\btaylor['’]s\s+version\b", "taylors_version"),
]

LIVE_COMPATIBLE_TAGS = {
    "live",
    "concert",
    "tour",
    "performance_ver",
    "band_ver",
}

PARENTHETICAL_METADATA_PATTERNS = [
    r"\bfeat(?:uring)?\b\.?",
    r"\bft\b\.?",
    r"\bprod\b\.?",
    r"\bproduced\s+by\b",
    r"\bremix\b",
    r"\blive\b",
    r"\bacoustic\b",
    r"\binstrumental\b",
    r"\bversion\b",
    r"\bedit\b",
    r"\bextended\b",
    r"\bradio\b",
    r"\bsped\s*up\b",
    r"\bslowed\b",
    r"\breverb\b",
]


BRACKET_METADATA_PATTERNS = list(PARENTHETICAL_METADATA_PATTERNS)


TRAILING_METADATA_PATTERNS = [
    r"\bfeat(?:uring)?\b\.?.*$",
    r"\bft\b\.?.*$",
    r"\bprod\b\.?.*$",
    r"\bproduced\s+by\b.*$",
    r"\bremix\b.*$",
    r"\blive\b.*$",
    r"\bacoustic\b.*$",
    r"\binstrumental\b.*$",
    r"\bversion\b.*$",
    r"\bedit\b.*$",
    r"\bextended\b.*$",
    r"\bradio\b.*$",
    r"\bsped\s*up\b.*$",
    r"\bslowed\b.*$",
    r"\breverb\b.*$",
]


# ============================================================
# 3. REMOVE YOUTUBE PRESENTATION METADATA
# ============================================================

def remove_youtube_metadata(title):
    if not title:
        return ""

    text = title

    for pattern in YOUTUBE_METADATA_PATTERNS:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\(\s*\)", " ", text)
    text = re.sub(r"\[\s*\]", " ", text)
    text = re.sub(r"「\s*」", " ", text)

    return text


# ============================================================
# 4. REMOVE MATCHING ARTIST FROM TITLE
# ============================================================

def remove_matching_artist_metadata(
    title,
    spotify_artist,
):
    if not title or not spotify_artist:
        return title

    text = title.strip()
    artist = spotify_artist.strip()

    escaped_artist = re.escape(artist)

    prefix_patterns = [
        rf"^(?:\[[^\]]*\]\s*)*{escaped_artist}\s*(?:\([^()]*\))?\s*[-–—|:_]\s*",
        rf"^(?:\[[^\]]*\]\s*)*{escaped_artist}\s*(?:,|&|\band\b|\bx\b|\bft\b\.?|\bfeat(?:uring)?\b\.?)[^-–—|:_]*[-–—|:_]\s*",
        rf"^(?:\[[^\]]*\]\s*)*[^-–—|:_()]*\(\s*{escaped_artist}\s*\)\s*[-–—|:_]\s*",
        rf"^(?:\[[^\]]*\]\s*)*{escaped_artist}\s*(?:\([^()]*\)|\s+[가-힣]+(?:\s+\d+)?)?\s*(?=['\"‘“])",
        rf"^(?:\[[^\]]*\]\s*)*{escaped_artist}\s+(?=[A-Za-z0-9가-힣])",
    ]

    for pattern in prefix_patterns:
        new_text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE,
        )
        if new_text != text and new_text.strip():
            text = new_text
            break

    suffix_pattern = (
        rf"\s*[-–—|:@]\s*"
        rf"{escaped_artist}"
        rf"(?=\s*$|\s*[\(\[])"
    )

    text = re.sub(
        suffix_pattern,
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text


def remove_feature_credits(title, spotify_title=None):
    if not title:
        return ""

    if spotify_title and any(
        re.search(p, spotify_title, flags=re.IGNORECASE)
        for p in FEATURE_CREDIT_PATTERNS
    ):
        return title

    text = title

    for bracket_re in [r"\(([^()]*)\)", r"\[([^\[\]]*)\]"]:
        matches = list(re.finditer(bracket_re, text))
        for match in reversed(matches):
            content = match.group(1)
            has_feature = any(
                re.search(p, content, flags=re.IGNORECASE)
                for p in FEATURE_CREDIT_PATTERNS
            )
            has_version = any(
                re.search(vp, content, flags=re.IGNORECASE)
                for vp, _ in VERSION_MODIFIER_PATTERNS
            )
            if has_feature and not has_version:
                text = text[:match.start()] + " " + text[match.end():]

    for p in FEATURE_CREDIT_PATTERNS:
        text = re.sub(
            rf"\s+{p}\s+[^\(\[\)\]]*(?=\s*$|\s*[\(\[])",
            " ",
            text,
            flags=re.IGNORECASE,
        )

    return text


# ============================================================
# 5. FULL NORMALIZED TITLE
# ============================================================

def canonicalize_language_versions(text):
    if not text:
        return ""
    text = re.sub(
        r"\b(?:japanese\s+ver(?:sion)?\.?|japan\s+ver(?:sion)?\.?|jp\s+ver(?:sion)?\.?)\b",
        "japanese ver",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(?:english\s+ver(?:sion)?\.?|eng\s+ver(?:sion)?\.?)\b",
        "english ver",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(?:korean\s+ver(?:sion)?\.?|kr\s+ver(?:sion)?\.?)\b",
        "korean ver",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\|[^|]*(?:soundtrack|ost)\b.*$",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"[\(\[][^\(\)\[\]]*\b(?:soundtrack|ost)\b[^\(\)\[\]]*[\)\]]",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    return text


def normalize_title(
    title,
    spotify_artist=None,
):
    if not title:
        return ""

    text = canonicalize_language_versions(title)

    text = remove_youtube_metadata(
        text
    )

    if spotify_artist:
        text = remove_matching_artist_metadata(
            text,
            spotify_artist,
        )

    text = text.lower().strip()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize_title_tokens(
    title,
    spotify_artist=None,
):
    normalized = normalize_title(
        title,
        spotify_artist=spotify_artist,
    )

    if not normalized:
        return []

    return normalized.split()


# ============================================================
# 6. VERSION CONFLICT & MULTILINGUAL TITLE EXTRACTION
# ============================================================

def get_version_tags(title):
    if not title:
        return set()

    tags = set()
    for pattern, tag in VERSION_MODIFIER_PATTERNS:
        if re.search(pattern, title, flags=re.IGNORECASE):
            tags.add(tag)

    return tags


def extract_remix_qualifiers(title, spotify_artist=None):
    """
    Extract specific remixer/version tokens inside (... Remix) or [... Remix],
    e.g. "Song A (David Guetta Remix)" -> {"david", "guetta"},
         "Butter (Hotter Remix)" -> {"hotter"},
         "Save Your Tears (Remix)" -> set().
    """
    if not title:
        return set()

    cleaned = remove_youtube_metadata(title)
    if spotify_artist:
        cleaned = remove_matching_artist_metadata(cleaned, spotify_artist)

    artist_tokens = set(normalize_title_tokens(spotify_artist or ""))
    stop_tokens = {
        "remix", "version", "ver", "edit", "official", "audio",
        "video", "mv", "feat", "featuring", "ft", "with", "prod", "by",
    } | artist_tokens

    qualifiers = set()
    for bracket_re in [r"\(([^()]*)\)", r"\[([^\[\]]*)\]"]:
        for match in re.finditer(bracket_re, cleaned):
            content = match.group(1)
            if re.search(r"\bremix\b", content, flags=re.IGNORECASE):
                tokens = normalize_title_tokens(content)
                for tok in tokens:
                    if tok not in stop_tokens:
                        qualifiers.add(tok)

    return qualifiers


def has_version_conflict(spotify_title, youtube_title, spotify_artist=None):
    """
    Symmetric + Sub-type Version Conflict Checker:
    1. If Spotify requests a Live version ("live" in sp_tags), YouTube tags in
       LIVE_COMPATIBLE_TAGS ("live", "concert", "tour", "performance_ver") are treated
       as compatible ("live").
    2. If sp_tags != yt_tags -> Conflict!
    3. If BOTH are "remix", check remix qualifiers (e.g. "Hotter Remix" vs "Cooler Remix",
       or "David Guetta Remix" vs "Tiesto Remix", or plain "(Remix)" vs "(Tiesto Remix)").
    """
    if not spotify_title or not youtube_title:
        return False

    sp_tags = set(get_version_tags(spotify_title))
    yt_tags = set(get_version_tags(youtube_title))

    if "live" in sp_tags:
        sp_tags = {"live" if t in LIVE_COMPATIBLE_TAGS else t for t in sp_tags}
        yt_tags = {"live" if t in LIVE_COMPATIBLE_TAGS else t for t in yt_tags}

    if sp_tags != yt_tags:
        return True

    if "remix" in sp_tags and "remix" in yt_tags:
        sp_qual = extract_remix_qualifiers(spotify_title, spotify_artist=spotify_artist)
        yt_qual = extract_remix_qualifiers(youtube_title, spotify_artist=spotify_artist)
        # If Spotify specifies a remixer/sub-type (e.g. "Hotter" or "David Guetta"),
        # YouTube must contain those qualifier tokens
        if sp_qual and sp_qual != yt_qual:
            return True
        # If Spotify is plain "(Remix)" and YouTube specifies an unrelated DJ remix (e.g. "(Tiesto Remix)")
        sp_all_tokens = set(normalize_title_tokens(spotify_title))
        if not sp_qual and yt_qual and not yt_qual.issubset(sp_all_tokens):
            return True

    return False


def extract_version_suffix_tokens(title):
    """
    Extract normalized tokens from any parenthetical/bracketed version modifiers
    (e.g. "(Instrumental)" -> "instrumental", "(Taylor's Version)" -> "taylor s version",
    "(David Guetta Remix)" -> "david guetta remix") so they are preserved when
    building multilingual title variants.
    """
    if not title:
        return ""

    version_parts = []
    for bracket_re in [r"\(([^()]*)\)", r"\[([^\[\]]*)\]"]:
        for match in re.finditer(bracket_re, title):
            content = match.group(1)
            if any(
                re.search(vp, content, flags=re.IGNORECASE)
                for vp, _ in VERSION_MODIFIER_PATTERNS
            ):
                norm_part = normalize_title(content)
                if norm_part and norm_part not in version_parts:
                    version_parts.append(norm_part)

    return " ".join(version_parts)


def append_version_suffix(variant_norm, version_suffix):
    if not variant_norm or not version_suffix:
        return variant_norm

    variant_tokens = variant_norm.split()
    for tok in version_suffix.split():
        if tok not in variant_tokens:
            variant_tokens.append(tok)
    return " ".join(variant_tokens)


def strip_non_version_brackets(text):
    """
    Remove parenthetical/bracketed segments ONLY if they do NOT contain version modifiers.
    Preserves (Remix), (Instrumental), (Live), (Taylor's Version), etc.
    """
    if not text:
        return ""

    result = text
    for bracket_re in [r"\(([^()]*)\)", r"\[([^\[\]]*)\]"]:
        matches = list(re.finditer(bracket_re, result))
        for match in reversed(matches):
            content = match.group(1)
            has_version = any(
                re.search(vp, content, flags=re.IGNORECASE)
                for vp, _ in VERSION_MODIFIER_PATTERNS
            )
            if not has_version:
                result = result[:match.start()] + " " + result[match.end():]
    return result


def get_candidate_title_variants(
    youtube_title,
    spotify_artist=None,
    spotify_title=None,
):
    if not youtube_title:
        return []

    variants = []

    base_norm = normalize_title(youtube_title, spotify_artist=spotify_artist)
    if base_norm:
        variants.append(base_norm)

    cleaned = remove_youtube_metadata(youtube_title)
    if spotify_artist:
        cleaned = remove_matching_artist_metadata(cleaned, spotify_artist)
    cleaned = remove_feature_credits(cleaned, spotify_title=spotify_title)

    cleaned_norm = normalize_title(cleaned, spotify_artist=spotify_artist)
    if cleaned_norm and cleaned_norm not in variants:
        variants.append(cleaned_norm)

    if not has_version_conflict(
        spotify_title or "",
        youtube_title,
        spotify_artist=spotify_artist,
    ):
        version_suffix = extract_version_suffix_tokens(cleaned)

        for quote_pattern in [
            r"(?:^|(?<=\s))['‘]((?:\w['’]\w|[^'’])+?)['’]+(?=\s|$)",
            r"['‘]([^'’]+)['’]",
            r"[\"“]([^\"”]+)[\"”]",
            r"〈([^〉]+)〉",
        ]:
            for match in re.finditer(quote_pattern, cleaned):
                outside = (cleaned[:match.start()] + " " + cleaned[match.end():]).strip()
                if spotify_artist:
                    outside = remove_matching_artist_metadata(outside, spotify_artist)
                outside_no_ver = strip_non_version_brackets(outside)
                for vp, _ in VERSION_MODIFIER_PATTERNS:
                    outside_no_ver = re.sub(vp, " ", outside_no_ver, flags=re.IGNORECASE)
                outside_latin = re.sub(r"[가-힣\W_]+", " ", outside_no_ver).strip()
                if outside_latin and spotify_artist:
                    outside_latin = re.sub(
                        rf"\b{re.escape(spotify_artist)}\b",
                        " ",
                        outside_latin,
                        flags=re.IGNORECASE,
                    ).strip()
                if len(outside_latin) > 2:
                    continue

                inner = match.group(1)
                inner_norm = append_version_suffix(
                    normalize_title(inner, spotify_artist=spotify_artist),
                    version_suffix,
                )
                if inner_norm and inner_norm not in variants:
                    variants.append(inner_norm)

                for paren_match in re.finditer(r"\(([^()]+)\)", inner):
                    p_norm = append_version_suffix(
                        normalize_title(paren_match.group(1), spotify_artist=spotify_artist),
                        version_suffix,
                    )
                    if p_norm and p_norm not in variants:
                        variants.append(p_norm)
                outer = strip_non_version_brackets(inner)
                outer_norm = append_version_suffix(
                    normalize_title(outer, spotify_artist=spotify_artist),
                    version_suffix,
                )
                if outer_norm and outer_norm not in variants:
                    variants.append(outer_norm)

        for paren_match in re.finditer(r"\(([^()]+)\)", cleaned):
            p_text = paren_match.group(1)
            if any(re.search(vp, p_text, flags=re.IGNORECASE) for vp, _ in VERSION_MODIFIER_PATTERNS):
                continue
            p_norm = append_version_suffix(
                normalize_title(p_text, spotify_artist=spotify_artist),
                version_suffix,
            )
            if p_norm and p_norm != normalize_title(spotify_artist or "") and p_norm not in variants:
                variants.append(p_norm)

        outer_cleaned = strip_non_version_brackets(cleaned)
        outer_norm = append_version_suffix(
            normalize_title(outer_cleaned, spotify_artist=spotify_artist),
            version_suffix,
        )
        if outer_norm and outer_norm not in variants:
            variants.append(outer_norm)

        dual_script_match = re.match(
            r"^\s*([가-힣]+(?:\s+[가-힣]+)*)\s+([A-Za-z0-9\s'’&:!?-]+?)\s*$",
            outer_cleaned,
        )
        if dual_script_match:
            kor_part = append_version_suffix(
                normalize_title(dual_script_match.group(1)),
                version_suffix,
            )
            eng_part = append_version_suffix(
                normalize_title(dual_script_match.group(2), spotify_artist=spotify_artist),
                version_suffix,
            )
            if kor_part and kor_part not in variants:
                variants.append(kor_part)
            if eng_part and eng_part not in variants:
                variants.append(eng_part)

    return variants


def extract_bilingual_aliases(spotify_title, candidates, spotify_artist=None):
    aliases = set()
    sp_norm = normalize_title(spotify_title)
    if not sp_norm or not candidates:
        return aliases

    pair_patterns = [
        r"([A-Za-z0-9\s'’&:!?-]+?)\s*\(\s*([가-힣]+(?:\s+[가-힣]+)*)\s*\)",
        r"([가-힣]+(?:\s+[가-힣]+)*)\s*\(\s*([A-Za-z0-9\s'’&:!?-]+?)\s*\)",
    ]

    for candidate in candidates:
        yt_title = candidate.get("title") or candidate.get("youtube_title") or ""
        if not yt_title:
            continue

        cleaned = remove_youtube_metadata(yt_title)
        if spotify_artist:
            cleaned = remove_matching_artist_metadata(cleaned, spotify_artist)

        for pattern in pair_patterns:
            for match in re.finditer(pattern, cleaned):
                part_a = normalize_title(match.group(1), spotify_artist=spotify_artist)
                part_b = normalize_title(match.group(2), spotify_artist=spotify_artist)
                if not part_a or not part_b:
                    continue
                if part_a == sp_norm:
                    aliases.add(part_b)
                elif part_b == sp_norm:
                    aliases.add(part_a)

    return aliases


# ============================================================
# 7. REMOVE PARENTHETICAL / BRACKET / TRAILING METADATA
# ============================================================

def remove_parenthetical_metadata(title):
    if not title:
        return ""

    text = title

    pattern = r"\(([^()]*)\)"

    matches = list(
        re.finditer(
            pattern,
            text,
        )
    )

    for match in reversed(matches):
        content = match.group(1)

        is_metadata = any(
            re.search(
                metadata_pattern,
                content,
                flags=re.IGNORECASE,
            )
            for metadata_pattern
            in PARENTHETICAL_METADATA_PATTERNS
        )

        if is_metadata:
            text = (
                text[:match.start()]
                + " "
                + text[match.end():]
            )

    return text


def remove_bracket_metadata(title):
    if not title:
        return ""

    text = title

    pattern = r"\[([^\[\]]*)\]"

    matches = list(
        re.finditer(
            pattern,
            text,
        )
    )

    for match in reversed(matches):
        content = match.group(1)

        is_metadata = any(
            re.search(
                metadata_pattern,
                content,
                flags=re.IGNORECASE,
            )
            for metadata_pattern
            in BRACKET_METADATA_PATTERNS
        )

        if is_metadata:
            text = (
                text[:match.start()]
                + " "
                + text[match.end():]
            )

    return text


def remove_trailing_metadata(title):
    if not title:
        return ""

    text = title

    for pattern in TRAILING_METADATA_PATTERNS:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    return text


# ============================================================
# 8. CORE TITLE
# ============================================================

def get_core_title(
    title,
    spotify_artist=None,
):
    if not title:
        return ""

    text = remove_youtube_metadata(
        title
    )

    if spotify_artist:
        text = remove_matching_artist_metadata(
            text,
            spotify_artist,
        )

    text = remove_parenthetical_metadata(
        text
    )

    text = remove_bracket_metadata(
        text
    )

    text = remove_trailing_metadata(
        text
    )

    text = text.lower().strip()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def get_core_title_tokens(
    title,
    spotify_artist=None,
):
    core_title = get_core_title(
        title,
        spotify_artist=spotify_artist,
    )

    if not core_title:
        return []

    return core_title.split()


# ============================================================
# 9. TITLE CONFLICT
# ============================================================

def get_title_conflict_tokens(
    spotify_title,
    youtube_title,
    spotify_artist=None,
    bilingual_aliases=None,
):
    spotify_tokens = normalize_title_tokens(
        remove_feature_credits(spotify_title),
        spotify_artist=spotify_artist,
    )

    youtube_tokens = normalize_title_tokens(
        youtube_title,
        spotify_artist=spotify_artist,
    )

    if not spotify_tokens or not youtube_tokens:
        return set()

    spotify_set = set(spotify_tokens)
    youtube_set = set(youtube_tokens)

    if spotify_set.issubset(youtube_set):
        return set()

    if bilingual_aliases:
        for alias in bilingual_aliases:
            alias_tokens = set(normalize_title_tokens(alias))
            if alias_tokens and alias_tokens.issubset(youtube_set):
                return set()

    return youtube_set - spotify_set


def has_title_conflict(
    spotify_title,
    youtube_title,
    spotify_artist=None,
    bilingual_aliases=None,
):
    conflicts = get_title_conflict_tokens(
        spotify_title,
        youtube_title,
        spotify_artist=spotify_artist,
        bilingual_aliases=bilingual_aliases,
    )

    return len(conflicts) > 0