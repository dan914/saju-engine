
"""Luck policy config loaders (supports v1.1.2 schema)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

from saju_common.policy_loader import load_policy_json


@dataclass(frozen=True)
class LuckPolicyConfig:
    """Normalized container for a single luck policy JSON."""

    policy_version: str
    weights: Mapping[str, object]
    hierarchy: Mapping[str, object]
    normalization: Mapping[str, object]
    options: Mapping[str, object]
    sect_profile: Optional[Mapping[str, object]] = None
    policy_assumptions: Sequence[str] = ()
    attribution: Optional[Mapping[str, object]] = None
    geokguk: Optional[Mapping[str, object]] = None
    hap_transform_model: Optional[Mapping[str, object]] = None
    category_overlays: Optional[Mapping[str, object]] = None
    transformation_role_coeff: Optional[Mapping[str, object]] = None
    profile: Optional[Mapping[str, object]] = None
    reco: Optional[Mapping[str, object]] = None
    alerts: Optional[Mapping[str, object]] = None
    ui: Optional[Mapping[str, object]] = None
    disclaimer: Optional[str] = None
    extras: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "LuckPolicyConfig":
        required = ("policy_version", "weights", "hierarchy", "normalization", "options")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Luck policy missing required keys: {', '.join(missing)}")

        optional_keys = {
            "sect_profile": "sect_profile",
            "policy_assumptions": "policy_assumptions",
            "attribution": "attribution",
            "geokguk": "geokguk",
            "hap_transform_model": "hap_transform_model",
            "category_overlays": "category_overlays",
            "transformation_role_coeff": "transformation_role_coeff",
            "profile": "profile",
            "reco": "reco",
            "alerts": "alerts",
            "ui": "ui",
            "disclaimer": "disclaimer",
        }

        recognized = set(required) | set(optional_keys)
        extras = {k: v for k, v in data.items() if k not in recognized}

        optional_values = {name: data.get(key) for key, name in optional_keys.items()}
        policy_assumptions = tuple(optional_values.get("policy_assumptions") or ())

        return cls(
            policy_version=str(data["policy_version"]),
            weights=data["weights"],
            hierarchy=data["hierarchy"],
            normalization=data["normalization"],
            options=data["options"],
            sect_profile=optional_values.get("sect_profile"),
            policy_assumptions=policy_assumptions,
            attribution=optional_values.get("attribution"),
            geokguk=optional_values.get("geokguk"),
            hap_transform_model=optional_values.get("hap_transform_model"),
            category_overlays=optional_values.get("category_overlays"),
            transformation_role_coeff=optional_values.get("transformation_role_coeff"),
            profile=optional_values.get("profile"),
            reco=optional_values.get("reco"),
            alerts=optional_values.get("alerts"),
            ui=optional_values.get("ui"),
            disclaimer=optional_values.get("disclaimer"),
            extras=extras,
        )


@dataclass(frozen=True)
class ActivityPolicyConfig:
    """Container for activity mapping JSON (good/caution day suggestions)."""

    mapping: Mapping[str, object]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "ActivityPolicyConfig":
        return cls(mapping=data)


@dataclass(frozen=True)
class LuckPolicyBundle:
    """Convenience wrapper bundling annual/monthly/daily policies with optional activity map."""

    annual: LuckPolicyConfig
    monthly: LuckPolicyConfig
    daily: LuckPolicyConfig
    activities: Optional[ActivityPolicyConfig] = None


def _load_policy_from_path(path: Path) -> LuckPolicyConfig:
    data = _read_json(path)
    return LuckPolicyConfig.from_mapping(data)


def _read_json(path: Path) -> Mapping[str, object]:
    import json

    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_luck_policy(filename: str) -> LuckPolicyConfig:
    """Load a luck policy using the shared policy loader search paths."""

    return LuckPolicyConfig.from_mapping(load_policy_json(filename))


def load_luck_policy_bundle(
    version: str = "v1_1_2",
    *,
    base_dir: Optional[Path] = None,
    activity_filename: Optional[str] = "activity/activity_map_v{version}.json",
) -> LuckPolicyBundle:
    """Load annual/monthly/daily policies (optionally from a custom directory).

    Args:
        version: Suffix used in filenames (underscores expected, e.g. "v1_1_2").
        base_dir: If provided, policies are loaded from this directory instead of
            the shared policy search paths.
        activity_filename: Relative filename for the optional activity mapping.
    """

    filenames = {
        "annual": f"luck_annual_policy_{version}.json",
        "monthly": f"luck_monthly_policy_{version}.json",
        "daily": f"luck_daily_policy_{version}.json",
    }

    if base_dir is not None:
        base_dir = base_dir.expanduser().resolve()
        policy_dir = base_dir
        annual_path = policy_dir / filenames["annual"]
        if not annual_path.exists():
            candidate = base_dir / 'policy'
            alt_path = candidate / filenames["annual"]
            if alt_path.exists():
                policy_dir = candidate
                annual_path = alt_path
        monthly_path = policy_dir / filenames["monthly"]
        daily_path = policy_dir / filenames["daily"]
        if not annual_path.exists() or not monthly_path.exists() or not daily_path.exists():
            missing = []
            if not annual_path.exists():
                missing.append(str(annual_path))
            if not monthly_path.exists():
                missing.append(str(monthly_path))
            if not daily_path.exists():
                missing.append(str(daily_path))
            raise FileNotFoundError('Luck policy files not found in base_dir; checked: ' + ', '.join(missing))

        annual = _load_policy_from_path(annual_path)
        monthly = _load_policy_from_path(monthly_path)
        daily = _load_policy_from_path(daily_path)

        activities = None
        if activity_filename:
            activity_rel = activity_filename.format(version=version)
            for candidate in (base_dir, policy_dir):
                activity_path = candidate / activity_rel
                if activity_path.exists():
                    activities = ActivityPolicyConfig.from_mapping(_read_json(activity_path))
                    break
        return LuckPolicyBundle(annual=annual, monthly=monthly, daily=daily, activities=activities)

    annual = load_luck_policy(filenames["annual"])
    monthly = load_luck_policy(filenames["monthly"])
    daily = load_luck_policy(filenames["daily"])

    activities = None
    if activity_filename:
        try:
            data = load_policy_json(activity_filename.format(version=version))
        except FileNotFoundError:
            activities = None
        else:
            activities = ActivityPolicyConfig.from_mapping(data)
    return LuckPolicyBundle(annual=annual, monthly=monthly, daily=daily, activities=activities)
