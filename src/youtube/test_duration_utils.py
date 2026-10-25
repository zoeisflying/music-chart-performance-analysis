from duration_utils import duration_difference_ratio


TEST_CASES = [
    # Spotify duration, YouTube duration, expected
    (180000, 180000, 0.0),
    (180000, 171000, 0.05),
    (180000, 162000, 0.10),
    (180000, 144000, 0.20),
    (180000, 90000, 0.50),
    (180000, 216000, 0.20),
]


for spotify_ms, youtube_ms, expected in TEST_CASES:
    actual = duration_difference_ratio(
        spotify_ms,
        youtube_ms
    )

    assert abs(actual - expected) < 1e-9, (
        f"Failed: "
        f"Spotify={spotify_ms}, "
        f"YouTube={youtube_ms}, "
        f"expected={expected}, "
        f"actual={actual}"
    )


# Invalid Spotify duration
assert duration_difference_ratio(0, 180000) is None
assert duration_difference_ratio(-1000, 180000) is None

# Invalid YouTube duration
assert duration_difference_ratio(180000, 0) is None
assert duration_difference_ratio(180000, -1000) is None


print("===== ALL DURATION TESTS PASSED =====")