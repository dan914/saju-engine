"""
Runtime validation guards for policy files.

Ensures policy integrity beyond JSON schema validation:
- Threshold ordering constraints
- Dependency signature verification
- Label assignment rules
"""

from __future__ import annotations

from dataclasses import dataclass


class PolicyValidationError(Exception):
    """Raised when policy validation fails at runtime."""

    pass


@dataclass(frozen=True)
class DependencySignature:
    """Dependency metadata for signature verification."""

    name: str
    version: str
    signature: str


def validate_threshold_order(policy: dict) -> None:
    """
    Enforce deficient < appropriate < developed < excessive and range [0,100].

    Args:
        policy: Elements distribution policy dict

    Raises:
        PolicyValidationError: On validation failure
    """
    th = policy.get("thresholds", {})
    required = ["deficient", "appropriate", "developed", "excessive"]

    if not all(k in th for k in required):
        raise PolicyValidationError("Missing thresholds keys.")

    d0, a, d, e = th["deficient"], th["appropriate"], th["developed"], th["excessive"]
    vals = [d0, a, d, e]

    if any((not isinstance(x, (int, float))) for x in vals):
        raise PolicyValidationError("Thresholds must be numeric.")

    if any((x < 0 or x > 100) for x in vals):
        raise PolicyValidationError("Thresholds must be within [0,100].")

    if not (d0 < a < d < e):
        raise PolicyValidationError(
            "Threshold order must satisfy: deficient < appropriate < developed < excessive."
        )


def validate_dependencies(policy: dict, dep_signatures: dict[str, DependencySignature]) -> None:
    """
    Ensure policy's declared dependency signatures match the actually loaded dependency signatures.

    Args:
        policy: Elements distribution policy dict
        dep_signatures: Dict mapping dependency name to actual loaded signature

    Raises:
        PolicyValidationError: On signature mismatch
    """
    deps = policy.get("dependencies", {})
    z_dep = deps.get("zanggan_policy")

    if not z_dep:
        raise PolicyValidationError("Missing zanggan_policy dependency.")

    declared = DependencySignature(
        name=z_dep.get("name", ""),
        version=z_dep.get("version", ""),
        signature=z_dep.get("signature", ""),
    )

    actual = dep_signatures.get(declared.name)

    if actual is None:
        raise PolicyValidationError(f"Dependency signature for '{declared.name}' not provided.")

    if (declared.version != actual.version) or (declared.signature != actual.signature):
        raise PolicyValidationError(
            f"Dependency mismatch for '{declared.name}': "
            f"declared({declared.version},{declared.signature}) "
            f"!= actual({actual.version},{actual.signature})"
        )


def normalize_and_label(percentages: dict[str, float], thresholds: dict) -> dict[str, str]:
    """
    Apply labeling before rounding, then return labels per element key.

    Args:
        percentages: Raw percentages for each element (木/火/土/金/水)
        thresholds: Threshold values from policy

    Returns:
        Dict mapping element to label key (excessive/developed/appropriate/deficient)
    """
    d0, a, d, e = (
        thresholds["deficient"],
        thresholds["appropriate"],
        thresholds["developed"],
        thresholds["excessive"],
    )

    labels = {}
    for k, v in percentages.items():
        # No rounding here; label on raw percentage
        if v >= e:
            labels[k] = "excessive"
        elif v >= d:
            labels[k] = "developed"
        elif v >= a:
            labels[k] = "appropriate"
        else:
            labels[k] = "deficient"

    return labels
