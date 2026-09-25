from candidate_ranking import (
    dominates,
    rank_candidates,
)


def test_clear_dominance():
    candidate_a = {
        "title_similarity": 100.0,
        "identity_evidence": [
            "artist_in_title"
        ],
        "source_evidence": [
            "official_audio"
        ],
        "duration_difference_ratio": 0.01,
    }

    candidate_b = {
        "title_similarity": 80.0,
        "identity_evidence": [
            "artist_in_title"
        ],
        "source_evidence": [],
        "duration_difference_ratio": 0.05,
    }

    assert dominates(
        candidate_a,
        candidate_b,
    )


def test_identity_does_not_automatically_win():
    candidate_a = {
        "title_similarity": 100.0,
        "identity_evidence": [],
        "source_evidence": [],
        "duration_difference_ratio": 0.001,
    }

    candidate_b = {
        "title_similarity": 50.0,
        "identity_evidence": [
            "artist_in_title"
        ],
        "source_evidence": [],
        "duration_difference_ratio": 0.03,
    }

    # A is better in title and duration.
    # B is better in identity.
    #
    # Therefore neither candidate dominates
    # the other one.

    assert not dominates(
        candidate_a,
        candidate_b,
    )

    assert not dominates(
        candidate_b,
        candidate_a,
    )


def test_title_alone_does_not_decide():
    candidate_a = {
        "title_similarity": 100.0,
        "identity_evidence": [],
        "source_evidence": [],
        "duration_difference_ratio": 0.20,
    }

    candidate_b = {
        "title_similarity": 90.0,
        "identity_evidence": [
            "exact_channel_artist"
        ],
        "source_evidence": [
            "official_audio"
        ],
        "duration_difference_ratio": 0.01,
    }

    assert not dominates(
        candidate_a,
        candidate_b,
    )

    assert not dominates(
        candidate_b,
        candidate_a,
    )


def test_empty_candidates():
    assert rank_candidates([]) == []


def test_no_match_score_created():
    candidate = {
        "title_similarity": 100.0,
        "identity_evidence": [],
        "source_evidence": [],
        "duration_difference_ratio": 0.01,
    }

    result = rank_candidates(
        [candidate]
    )

    assert "match_score" not in result[0]


if __name__ == "__main__":
    test_clear_dominance()
    test_identity_does_not_automatically_win()
    test_title_alone_does_not_decide()
    test_empty_candidates()
    test_no_match_score_created()

    print(
        "===== CANDIDATE RANKING TEST PASSED ====="
    )