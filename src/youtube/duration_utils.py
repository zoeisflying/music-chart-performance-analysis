def duration_difference_ratio(
    spotify_duration_ms,
    youtube_duration_ms
):
    if spotify_duration_ms <= 0 or youtube_duration_ms <= 0:
        return None

    return abs(
        spotify_duration_ms - youtube_duration_ms
    ) / spotify_duration_ms