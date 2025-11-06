"""
Runtime validation guards for luck pillars policy.

Validates structural integrity beyond JSON schema:
- Sixty Jiazi cycle progression
- Direction matrix completeness
- Age series bounds
- Solar term reference type (jie/qi)
- Label keys presence
"""

from __future__ import annotations


class LuckPolicyError(Exception):
    """Raised when luck pillars policy validation fails."""

    pass


def validate_jiazi_cycle(jiazi_policy: dict) -> None:
    """
    Validate 60 Jiazi cycle progression.

    Args:
        jiazi_policy: Sixty Jiazi policy dict

    Raises:
        LuckPolicyError: On validation failure
    """
    cycle = jiazi_policy.get("cycle", [])

    if len(cycle) != 60:
        raise LuckPolicyError("Sixty Jiazi cycle must have length 60.")

    names = [f"{x['stem']}{x['branch']}" for x in cycle]
    if len(set(names)) != 60:
        raise LuckPolicyError("Sixty Jiazi names must be unique.")

    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"

    for i in range(60):
        cur = cycle[i]
        nxt = cycle[(i + 1) % 60]

        if stems.index(nxt["stem"]) != (stems.index(cur["stem"]) + 1) % 10:
            raise LuckPolicyError(f"Stem progression broken at index {i}.")

        if branches.index(nxt["branch"]) != (branches.index(cur["branch"]) + 1) % 12:
            raise LuckPolicyError(f"Branch progression broken at index {i}.")


def validate_direction_matrix(matrix: dict) -> None:
    """
    Validate direction matrix has all required entries.

    Args:
        matrix: Direction matrix dict

    Raises:
        LuckPolicyError: On validation failure
    """
    for gender in ("male", "female"):
        row = matrix.get(gender)
        if not row or not all(k in row for k in ("yang", "yin")):
            raise LuckPolicyError(f"Direction matrix missing entries for {gender}.")

        if row["yang"] not in ("forward", "backward") or row["yin"] not in ("forward", "backward"):
            raise LuckPolicyError("Direction values must be 'forward' or 'backward'.")


def validate_age_series(series: dict) -> None:
    """
    Validate age series bounds.

    Args:
        series: Age series dict

    Raises:
        LuckPolicyError: On validation failure
    """
    step = series.get("step_years", 10)
    count = series.get("count", 10)

    if not (1 <= step <= 20 and 1 <= count <= 12):
        raise LuckPolicyError("Age series out of bounds.")


def validate_start_age_reference(ref: dict) -> None:
    """
    Validate start age reference structure.

    Args:
        ref: Reference dict from start_age section

    Raises:
        LuckPolicyError: On validation failure
    """
    if ref.get("type") not in ("jie", "qi"):
        raise LuckPolicyError("start_age.reference.type must be 'jie' or 'qi'.")

    if ref.get("forward") != "next" or ref.get("backward") != "prev":
        raise LuckPolicyError("start_age.reference forward/backward must be 'next'/'prev'.")


def validate_labels(labels: dict) -> None:
    """
    Validate labels have all required keys for each language.

    Args:
        labels: Labels dict

    Raises:
        LuckPolicyError: On validation failure
    """
    for lang in ("ko", "en"):
        required = ("luck_pillar", "age", "ten_god", "lifecycle")
        if lang not in labels or not all(k in labels[lang] for k in required):
            raise LuckPolicyError(f"labels missing keys for {lang}: {required}")
