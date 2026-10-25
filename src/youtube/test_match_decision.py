from match_decision import decide_match


def make_candidate(
    candidate_id,
    title_similarity,
    identity_evidence,
    source_evidence,
    duration_difference_ratio,
    title_conflict=False,
    hard_invalid=False,
):
    return {
        "id": candidate_id,
        "title_similarity": title_similarity,
        "identity_evidence": identity_evidence,
        "source_evidence": source_evidence,
        "duration_difference_ratio": duration_difference_ratio,
        "title_conflict": title_conflict,
        "hard_invalid": hard_invalid,
    }


def test_no_candidates():
    result = decide_match([])

    assert result["status"] == "no_confident_match"
    assert result["selected_candidate"] is None

    print("PASS: no candidates")


def test_all_candidates_invalid():
    candidates = [
        make_candidate(
            candidate_id="A",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
            hard_invalid=True,
        ),
        make_candidate(
            candidate_id="B",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.02,
            title_conflict=True,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "no_confident_match"
    assert result["selected_candidate"] is None

    print("PASS: all candidates invalid")


def test_title_similarity_priority():
    candidates = [
        make_candidate(
            candidate_id="A",
            title_similarity=100,
            identity_evidence=["artist_in_title"],
            source_evidence=[],
            duration_difference_ratio=0.10,
        ),
        make_candidate(
            candidate_id="B",
            title_similarity=80,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "automatic"
    assert result["selected_candidate"]["id"] == "A"

    print("PASS: title similarity priority")


def test_source_priority_when_title_equal():
    candidates = [
        make_candidate(
            candidate_id="A",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=[],
            duration_difference_ratio=0.01,
        ),
        make_candidate(
            candidate_id="B",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.02,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "automatic"
    assert result["selected_candidate"]["id"] == "B"

    print("PASS: source priority when title equal")


def test_duration_priority_when_other_evidence_equal():
    candidates = [
        make_candidate(
            candidate_id="A",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.10,
        ),
        make_candidate(
            candidate_id="B",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "automatic"
    assert result["selected_candidate"]["id"] == "B"

    print("PASS: duration priority")


def test_equal_candidates_are_ambiguous():
    candidates = [
        make_candidate(
            candidate_id="A",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
        ),
        make_candidate(
            candidate_id="B",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "ambiguous"
    assert result["selected_candidate"] is None

    print("PASS: equal candidates are ambiguous")


def test_title_conflict_is_rejected():
    candidates = [
        make_candidate(
            candidate_id="wrong",
            title_similarity=100,
            identity_evidence=["exact_channel_artist"],
            source_evidence=["official_audio"],
            duration_difference_ratio=0.01,
            title_conflict=True,
        ),
        make_candidate(
            candidate_id="correct",
            title_similarity=80,
            identity_evidence=["artist_in_title"],
            source_evidence=[],
            duration_difference_ratio=0.05,
        ),
    ]

    result = decide_match(candidates)

    assert result["status"] == "automatic"
    assert result["selected_candidate"]["id"] == "correct"

    print("PASS: title conflict is rejected")


def run_all_tests():
    print("===== MATCH DECISION TESTS =====")

    test_no_candidates()
    test_all_candidates_invalid()
    test_title_similarity_priority()
    test_source_priority_when_title_equal()
    test_duration_priority_when_other_evidence_equal()
    test_equal_candidates_are_ambiguous()
    test_title_conflict_is_rejected()

    print("===== ALL MATCH DECISION TESTS PASSED =====")


if __name__ == "__main__":
    run_all_tests()