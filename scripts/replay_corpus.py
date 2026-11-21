"""Replay shared-domain corpus against public pll API. Implementation task S1."""


def replay_file(path) -> int:
    """Validate schema/artifact hashes, replay all cases and return checked result rows.

    Normalize Go errors/config fields as SPEC; exact except fixture-specific
    numerical tolerances. Raise ValueError for bad schema and AssertionError
    with case/operation reproduction for disagreement. Never mutate inputs.
    """
    raise NotImplementedError('S1: public API corpus replay')
