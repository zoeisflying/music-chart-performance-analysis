from source_evidence import (
    get_source_evidence,
)


def test_official_music_video():
    evidence = get_source_evidence(
        "BLACKPINK - How You Like That M/V",
        "BLACKPINK",
    )

    assert "music_video" in evidence

    print("PASS: M/V")


def test_mv():
    evidence = get_source_evidence(
        "BTS - Dynamite MV",
        "HYBE LABELS",
    )

    assert "music_video" in evidence

    print("PASS: MV")


def test_official_audio():
    evidence = get_source_evidence(
        "Save Your Tears (Official Audio)",
        "The Weeknd",
    )

    assert "official_audio" in evidence

    print("PASS: Official Audio")


def test_lyric_video():
    evidence = get_source_evidence(
        "What's Next (Official Lyric Video)",
        "Megan Thee Stallion",
    )

    assert "official_lyric_video" in evidence

    print("PASS: Official Lyric Video")


def test_topic_channel():
    evidence = get_source_evidence(
        "VVS",
        "MIRANI - Topic",
    )

    assert "topic_channel" in evidence

    print("PASS: Topic channel")


def test_explicit_official_channel():
    evidence = get_source_evidence(
        "Some Song",
        "Some Artist Official",
    )

    assert "official_channel" in evidence

    print("PASS: Explicit official channel")


def test_vevo_channel():
    evidence = get_source_evidence(
        "Some Song",
        "ArtistVEVO",
    )

    assert "official_channel" in evidence

    print("PASS: VEVO channel")


def test_no_false_positive():
    evidence = get_source_evidence(
        "Boy With Luv",
        "Random Lyrics Channel",
    )

    assert "official_channel" not in evidence

    print("PASS: No false official-channel evidence")

def test_official_live():
    evidence = get_source_evidence(
        "Ariana Grande - 34+35 (Official Live Performance) | Vevo",
        "Ariana Grande",
    )

    assert "official_live" in evidence

    print("PASS: Official Live Performance")


def test_visualizer():
    evidence = get_source_evidence(
        "Justin Bieber - As I Am (Visualizer) ft. Khalid",
        "Justin Bieber",
    )

    assert "visualizer" in evidence

    print("PASS: Visualizer")


if __name__ == "__main__":
    print("===== SOURCE EVIDENCE TESTS =====")

    test_official_music_video()
    test_mv()
    test_official_audio()
    test_lyric_video()
    test_topic_channel()
    test_explicit_official_channel()
    test_vevo_channel()
    test_no_false_positive()
    test_official_live()
    test_visualizer()

    print("===== ALL TESTS PASSED =====")