# -*- coding: utf-8 -*-
from collections import Counter

def resolve(relations, policy, level: str, taese_branch=None, current_transit_branch=None):
    weights = policy['weights']['relations']
    opts = policy.get('options', {})
    mode = opts.get('exclude_taise_from_relations', False)
    filtered = []
    for kind, subtype, a, b in relations:
        if mode == 'same_axis_only' and taese_branch and current_transit_branch:
            if kind in ('hap','clash','square','punish','harm') and (
               (a == taese_branch and b == current_transit_branch) or (b == taese_branch and a == current_transit_branch)):
                continue
        filtered.append((kind, subtype, a, b))

    cnt = Counter([k for (k,_,_,_) in filtered])
    total = 0.0
    for k, c in cnt.items():
        key = (k if k!='clash' else 'chung')
        total += weights.get(key, 0.0) * c

    bonuses = weights.get('bonuses', {})
    if cnt.get('clash', 0) >= 2:
        total += bonuses.get('double_chung_same_axis', 0.0)

    if taese_branch and current_transit_branch:
        if cnt.get('clash', 0) >= 1:
            if level == 'daily':
                total += bonuses.get('synergy_taise_plus_day_branch_chung', 0.0)
            else:
                total += bonuses.get('synergy_taise_plus_other_branch_chung', 0.0)

    breakdown = dict(cnt)
    return breakdown, total
