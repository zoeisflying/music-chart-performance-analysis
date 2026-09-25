from identity_evidence import (
    artist_similarity,
    artist_name_in_text,
    get_identity_evidence,
)


print("===== IDENTITY EVIDENCE TEST =====")


# --------------------------------------------------
# Test 1: exact artist/channel
# --------------------------------------------------

result = get_identity_evidence(
    spotify_artist="BLACKPINK",
    youtube_title="BLACKPINK - How You Like That M/V",
    youtube_channel="BLACKPINK",
)

print("\nTest 1")
print(result)

assert "exact_channel_artist" in result
assert "artist_in_title" in result


# --------------------------------------------------
# Test 2: artist appears in title
# --------------------------------------------------

result = get_identity_evidence(
    spotify_artist="Ariana Grande",
    youtube_title="Ariana Grande - 34+35 (Official Video)",
    youtube_channel="Some Music Channel",
)

print("\nTest 2")
print(result)

assert "artist_in_title" in result
assert "exact_channel_artist" not in result


# --------------------------------------------------
# Test 3: different channel can still be valid
# --------------------------------------------------

result = get_identity_evidence(
    spotify_artist="ROSÉ",
    youtube_title="ROSÉ - Gone",
    youtube_channel="BLACKPINK",
)

print("\nTest 3")
print(result)

assert "artist_in_title" in result


# --------------------------------------------------
# Test 4: completely unrelated candidate
# --------------------------------------------------

result = get_identity_evidence(
    spotify_artist="Ariana Grande",
    youtube_title="BTS - Boy With Luv",
    youtube_channel="HYBE LABELS",
)

print("\nTest 4")
print(result)

assert result == []


# --------------------------------------------------
# Test 5: artist similarity itself
# --------------------------------------------------

similarity_exact = artist_similarity(
    "BLACKPINK",
    "BLACKPINK",
)

similarity_different = artist_similarity(
    "BLACKPINK",
    "BTS",
)

print("\nTest 5")
print("Exact similarity:", similarity_exact)
print("Different similarity:", similarity_different)

assert similarity_exact == 100.0
assert similarity_different < similarity_exact


# --------------------------------------------------
# Test 6: artist name detection
# --------------------------------------------------

assert artist_name_in_text(
    "Ariana Grande",
    "Ariana Grande Official",
)

assert not artist_name_in_text(
    "Ariana Grande",
    "The Weeknd Official",
)


print("\n===== ALL TESTS PASSED =====")