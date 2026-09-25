from functools import cmp_to_key


IDENTITY_PRIORITY = {
    "exact_channel_artist": 2,
    "artist_in_channel": 1,
    "artist_in_title": 1,
}


def get_identity_priority(identity_evidence):
    if not identity_evidence:
        return 0

    return max(
        IDENTITY_PRIORITY.get(
            evidence,
            0,
        )
        for evidence in identity_evidence
    )


def get_title_similarity(candidate):
    value = candidate.get("title_similarity")

    if value is None:
        return -1.0

    return float(value)


def get_source_evidence_count(candidate):
    evidence = candidate.get(
        "source_evidence",
        [],
    )

    if evidence is None:
        return 0

    return len(evidence)


def get_duration_difference(candidate):
    value = candidate.get(
        "duration_difference_ratio"
    )

    if value is None:
        return float("inf")

    return float(value)


def get_identity_value(candidate):
    return get_identity_priority(
        candidate.get(
            "identity_evidence",
            [],
        )
    )


def dominates(candidate_a, candidate_b):
    """
    Return True when candidate_a is at least as good as
    candidate_b on every evidence dimension and strictly
    better on at least one dimension.

    Higher is better:
        title similarity
        identity evidence
        source evidence

    Lower is better:
        duration difference
    """

    a_title = get_title_similarity(candidate_a)
    b_title = get_title_similarity(candidate_b)

    a_identity = get_identity_value(candidate_a)
    b_identity = get_identity_value(candidate_b)

    a_source = get_source_evidence_count(candidate_a)
    b_source = get_source_evidence_count(candidate_b)

    a_duration = get_duration_difference(candidate_a)
    b_duration = get_duration_difference(candidate_b)

    at_least_as_good = (
        a_title >= b_title
        and a_identity >= b_identity
        and a_source >= b_source
        and a_duration <= b_duration
    )

    strictly_better = (
        a_title > b_title
        or a_identity > b_identity
        or a_source > b_source
        or a_duration < b_duration
    )

    return (
        at_least_as_good
        and strictly_better
    )


def rank_candidates(candidates):
    """
    Rank candidates using pairwise dominance.

    Candidates that are not dominated by another candidate
    form the first evidence layer.

    No weighted match score is calculated.
    """

    candidates = list(candidates)

    if not candidates:
        return []

    dominance_count = {
        id(candidate): 0
        for candidate in candidates
    }

    for candidate in candidates:
        for other in candidates:
            if candidate is other:
                continue

            if dominates(
                other,
                candidate,
            ):
                dominance_count[id(candidate)] += 1

    return sorted(
        candidates,
        key=lambda candidate: dominance_count[
            id(candidate)
        ],
    )