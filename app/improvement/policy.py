"""
policy.py - decides whether to KEEP a proposed rule.

Keep it only if:
    1. the number of passing scenarios went UP, and
    2. no scenario that passed before is now failing (no "regressions").
"""


def should_keep_rule(results_before, results_after):
    """Returns (keep: bool, regressions: list of scenario ids that broke)."""
    passed_before = set()
    for result in results_before:
        if result["pass"]:
            passed_before.add(result["id"])

    regressions = []
    for result in results_after:
        if result["id"] in passed_before and not result["pass"]:
            regressions.append(result["id"])

    count_before = len(passed_before)
    count_after = sum(1 for result in results_after if result["pass"])
    improved = count_after > count_before

    keep = improved and len(regressions) == 0
    return keep, regressions
