import re
import requests


def get_spotify_duration(spotify_track_id):
    """
    Get track duration from Spotify Embed page.

    Parameters
    ----------
    spotify_track_id : str
        Spotify track ID.

    Returns
    -------
    int
        Duration in milliseconds.

    Raises
    ------
    ValueError
        If duration cannot be found.
    """

    url = (
        f"https://open.spotify.com/embed/track/"
        f"{spotify_track_id}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/153.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    html = response.text

    pattern = r'"duration"\s*:\s*(\d+)'

    matches = re.findall(pattern, html)

    valid_candidates = [
        int(value)
        for value in matches
        if 30_000 <= int(value) <= 15 * 60 * 1000
    ]

    if not valid_candidates:
        raise ValueError(
            f"Could not find valid duration for "
            f"Spotify track {spotify_track_id}"
        )

    return valid_candidates[0]