# -*- coding: utf-8 -*-
"""Utility functions for strength and yongshin evaluation.
Extracted from bundle v2 implementation.
"""
from typing import List, Tuple

STEM_TO_ELEM = {
    "甲":"wood","乙":"wood","丙":"fire","丁":"fire","戊":"earth","己":"earth",
    "庚":"metal","辛":"metal","壬":"water","癸":"water"
}
ELEM_TO_KO = {"wood":"목","fire":"화","earth":"토","metal":"금","water":"수"}
KO_TO_ELEM = {v:k for k,v in ELEM_TO_KO.items()}

BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 生(생) cycle: wood→fire→earth→metal→water→wood
GEN = {"wood":"fire","fire":"earth","earth":"metal","metal":"water","water":"wood"}
# 克(극) cycle: wood克earth, earth克water, water克fire, fire克metal, metal克wood
KE = {"wood":"earth","earth":"water","water":"fire","fire":"metal","metal":"wood"}

def parse_pillar(p: str) -> Tuple[str,str]:
    if not p or len(p) < 2: return (None, None)
    return p[0], p[1]

def elem_of_stem(stem: str) -> str:
    return STEM_TO_ELEM.get(stem)

def ko_of_elem(elem: str) -> str:
    return ELEM_TO_KO.get(elem, elem)

def elem_of_ko(ko: str) -> str:
    return KO_TO_ELEM.get(ko, ko)

def rel_of(e1: str, e2: str) -> str:
    """Relationship of e1 (day) to e2 (other) in Five Elements.
    returns one of: 'same','gen_to_other','gen_from_other','ke_to_other','ke_from_other'
    """
    if e1 == e2: return "same"
    if GEN[e1] == e2: return "gen_to_other"     # 我生
    if GEN[e2] == e1: return "gen_from_other"   # 生我
    if KE[e1] == e2:  return "ke_to_other"      # 我克
    if KE[e2] == e1:  return "ke_from_other"    # 克我
    return "none"

def ten_god_bucket(day_elem: str, other_elem: str) -> str:
    r = rel_of(day_elem, other_elem)
    if r == "gen_from_other": return "resource"   # 인성
    if r == "same":           return "companion"  # 비견/겁재
    if r == "gen_to_other":   return "output"     # 식상
    if r == "ke_to_other":    return "wealth"     # 재성
    if r == "ke_from_other":  return "official"   # 관성
    return "none"

# 관계(六合/三合/沖/害)
LIUHE = [("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")]
CHONG  = [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]
HAI   = [("子","未"),("丑","午"),("寅","巳"),("卯","辰"),("申","亥"),("酉","戌")]
SANHE = {
    "wood":  ["亥","卯","未"],
    "fire":  ["寅","午","戌"],
    "metal": ["巳","酉","丑"],
    "water": ["申","子","辰"]
}

def pairs_present(branches: List[str], pairs: List[tuple]) -> int:
    s = set(branches)
    return sum(1 for a,b in pairs if a in s and b in s)

def sanhe_present(branches: List[str]) -> int:
    cnt = 0
    s = set(branches)
    for grp in SANHE.values():
        if all(b in s for b in grp):
            cnt += 1
    return cnt
