from rapidfuzz import fuzz

from title_normalizer import (
    normalize_title,
    remove_feature_credits,
    has_version_conflict,
    get_candidate_title_variants,
)


def title_similarity(
    spotify_title,
    youtube_title,
    spotify_artist=None,
    bilingual_aliases=None,
):
    spotify_normalized = normalize_title(
        spotify_title,
    )

    youtube_normalized = normalize_title(
        youtube_title,
        spotify_artist=spotify_artist,
    )

    if not spotify_normalized or not youtube_normalized:
        return None

    base_score = float(
        fuzz.ratio(
            spotify_normalized,
            youtube_normalized,
        )
    )

    # If there is an explicit version/recording conflict (e.g. original vs Remix/Live/Slowed/Dance Practice),
    # do not boost similarity via stripped variants; cap score below confident threshold.
    if has_version_conflict(spotify_title, youtube_title, spotify_artist=spotify_artist):
        return min(base_score, 75.0)

    target_titles = [spotify_normalized]
    stripped_sp = normalize_title(remove_feature_credits(spotify_title))
    if stripped_sp and stripped_sp not in target_titles:
        target_titles.append(stripped_sp)

    if bilingual_aliases:
        for alias in bilingual_aliases:
            alias_norm = normalize_title(alias)
            if alias_norm and alias_norm not in target_titles:
                target_titles.append(alias_norm)

    variants = get_candidate_title_variants(
        youtube_title,
        spotify_artist=spotify_artist,
        spotify_title=spotify_title,
    )

    best_score = base_score
    for target in target_titles:
        for variant in variants:
            score = float(fuzz.ratio(target, variant))
            if score > best_score:
                best_score = score

    return best_score