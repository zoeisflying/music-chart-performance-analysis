from title_normalizer import (
    normalize_title,
    has_title_conflict,
    get_title_conflict_tokens,
)


def test_boy_with_luv_vs_boy_in_luv():
    spotify_title = "Boy With Luv"
    youtube_title = "[MV] BTS (방탄소년단) 'Boy In Luv'"

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist="BTS",
    )

    conflicts = get_title_conflict_tokens(
        spotify_title,
        youtube_title,
        spotify_artist="BTS",
    )

    assert conflict is True
    assert "in" in conflicts

    print("PASS: Boy With Luv vs Boy In Luv")


def test_vvs_feature_version():
    spotify_title = "VVS"
    youtube_title = "VVS (Feat. JUSTHIS) (Prod. GroovyRoom)"

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist="MIRANI",
    )

    assert conflict is False

    print("PASS: VVS vs VVS (Feat. JUSTHIS) (Prod. GroovyRoom)")


def test_save_your_tears_official_audio():
    spotify_title = "Save Your Tears"
    youtube_title = (
        "The Weeknd - Save Your Tears "
        "(Official Audio)"
    )

    normalized = normalize_title(
        youtube_title,
        spotify_artist="The Weeknd",
    )

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist="The Weeknd",
    )

    assert normalized == "save your tears"
    assert conflict is False

    print("PASS: Save Your Tears vs Official Audio")


def test_save_your_tears_remix():
    spotify_title = "Save Your Tears"
    youtube_title = (
        "The Weeknd - Save Your Tears "
        "(Remix)"
    )

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist="The Weeknd",
    )

    assert conflict is False

    print(
        "PASS: Save Your Tears vs Save Your Tears (Remix)"
    )


def test_same_title():
    spotify_title = "Blue & Grey"
    youtube_title = "Blue & Grey"

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
    )

    assert conflict is False

    print("PASS: Blue & Grey vs Blue & Grey")


def test_artist_and_youtube_metadata():
    spotify_title = "34+35"
    youtube_title = (
        "Ariana Grande - 34+35 "
        "(Official Video)"
    )

    normalized = normalize_title(
        youtube_title,
        spotify_artist="Ariana Grande",
    )

    conflict = has_title_conflict(
        spotify_title,
        youtube_title,
        spotify_artist="Ariana Grande",
    )

    assert normalized == "34 35"
    assert conflict is False

    print("PASS: 34+35 official video")


if __name__ == "__main__":
    print("===== TITLE CONFLICT TESTS =====")

    test_boy_with_luv_vs_boy_in_luv()
    test_vvs_feature_version()
    test_save_your_tears_official_audio()
    test_save_your_tears_remix()
    test_same_title()
    test_artist_and_youtube_metadata()

    print("===== ALL TESTS PASSED =====")