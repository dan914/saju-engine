# -*- coding: utf-8 -*-
from math import tanh

def normalize(x: float, s: float, clip: float = 100.0, method: str = "tanh") -> float:
    if method == "tanh":
        return max(-clip, min(clip, 100.0 * tanh(x / (s or 1.0))))
    return max(-clip, min(clip, x))

def gate(x_norm: float, k: float, clip_low: float, clip_high: float) -> float:
    return max(clip_low, min(clip_high, 1.0 + k * (x_norm / 100.0)))

def score_sibsin(day_master, transit, policy, strength_profile, include_hidden=True):
    tg_w = policy['weights']['sibsin']['ten_gods']
    mul = policy['weights']['sibsin']['multipliers']['by_strength'][strength_profile]
    hs  = policy['weights']['sibsin']['multipliers']['hidden_stem']

    exposures = []
    if hasattr(transit, 'stem') and transit.stem:
        tg = day_master.ten_god_of(transit.stem)
        exposures.append((tg, 1.0))
    if include_hidden and hasattr(transit, 'branch') and getattr(transit.branch, 'hidden_stems', None):
        for (stem, role) in transit.branch.hidden_stems:
            tg = day_master.ten_god_of(stem)
            exposures.append((tg, hs.get(role, 0.0)))

    s = 0.0
    for tg, w in exposures:
        base = tg_w.get(tg, 0.0)
        m = mul.get(tg, 1.0)
        s += base * m * w
    return s

def score_unseong12(day_master_element, transit_branch, policy):
    phase = transit_branch.phase_of(day_master_element)
    return policy['weights']['unseong12'].get(phase, 0.0)

def score_taese(taese_branch, transit_branch, policy, relation_type_func):
    r = relation_type_func(taese_branch, transit_branch)
    key = f"{r}_taese"
    return policy['weights']['taese'].get(key, 0.0)

def score_season(day_master_element, month_branch, policy, strength_profile, level: str):
    season = policy['weights']['season']
    apply_levels = season.get('apply_levels', {'year': False, 'month': True, 'day': True})
    if not apply_levels.get(level, True):
        return 0.0
    if month_branch is None:
        return 0.0
    k = season['by_branch'][month_branch.key][day_master_element.key]
    mult = season['by_strength'][strength_profile]
    return float(k) * float(mult)
