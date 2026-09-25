from title_normalizer import normalize_title


TEST_CASES = [
    (
        "34+35",
        "34 35"
    ),
    (
        "34+35 (Official Video)",
        "34 35"
    ),
    (
        "Save Your Tears (Official Audio)",
        "save your tears"
    ),
    (
        "Song A (David Guetta Remix) - Official Video",
        "song a david guetta remix"
    ),
    (
        "Song A (Live) - Official Video",
        "song a live"
    ),
    (
        "Song A (Acoustic) - Official Audio",
        "song a acoustic"
    ),
    (
        "Song A (Slowed + Reverb)",
        "song a slowed reverb"
    ),
    (
        "Song A (Sped Up)",
        "song a sped up"
    ),
]


for original, expected in TEST_CASES:
    actual = normalize_title(original)

    assert actual == expected, (
        f"Failed:\n"
        f"Original: {original}\n"
        f"Expected: {expected}\n"
        f"Actual:   {actual}"
    )


# Empty / invalid input
assert normalize_title("") == ""
assert normalize_title(None) == ""


print("===== ALL TITLE NORMALIZATION TESTS PASSED =====")