from title_similarity import title_similarity


# Exact match
result = title_similarity(
    "34+35",
    "34+35"
)

assert result == 100.0, (
    f"Exact match failed: {result}"
)


# YouTube metadata should be ignored
result = title_similarity(
    "34+35",
    "Ariana Grande - 34+35 (Official Video)"
)

assert result > 0, (
    f"Metadata test failed: {result}"
)


# Exact version should remain part of the title
result = title_similarity(
    "Song A (David Guetta Remix)",
    "Song A (David Guetta Remix) - Official Video"
)

assert result == 100.0, (
    f"Version-preservation test failed: {result}"
)


# Different remix should not be identical
result = title_similarity(
    "Song A (David Guetta Remix)",
    "Song A (Tiesto Remix)"
)

assert result < 100.0, (
    f"Different-version test failed: {result}"
)


# Completely different songs
result = title_similarity(
    "Song A",
    "Completely Different Song"
)

assert result < 80.0, (
    f"Different-title test failed: {result}"
)


# Empty titles
assert title_similarity("", "Song A") is None
assert title_similarity("Song A", "") is None
assert title_similarity(None, "Song A") is None


print("===== ALL TITLE SIMILARITY TESTS PASSED =====")