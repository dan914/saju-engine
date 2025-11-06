"""Minimal 60갑자 helpers for luck engines."""

from __future__ import annotations

SEXAGENARY = [
    "甲子",
    "乙丑",
    "丙寅",
    "丁卯",
    "戊辰",
    "己巳",
    "庚午",
    "辛未",
    "壬申",
    "癸酉",
    "甲戌",
    "乙亥",
    "丙子",
    "丁丑",
    "戊寅",
    "己卯",
    "庚辰",
    "辛巳",
    "壬午",
    "癸未",
    "甲申",
    "乙酉",
    "丙戌",
    "丁亥",
    "戊子",
    "己丑",
    "庚寅",
    "辛卯",
    "壬辰",
    "癸巳",
    "甲午",
    "乙未",
    "丙申",
    "丁酉",
    "戊戌",
    "己亥",
    "庚子",
    "辛丑",
    "壬寅",
    "癸卯",
    "甲辰",
    "乙巳",
    "丙午",
    "丁未",
    "戊申",
    "己酉",
    "庚戌",
    "辛亥",
    "壬子",
    "癸丑",
    "甲寅",
    "乙卯",
    "丙辰",
    "丁巳",
    "戊午",
    "己未",
    "庚申",
    "辛酉",
    "壬戌",
    "癸亥",
]


def pillar_to_index(pillar: str) -> int:
    """Return the index of the given pillar in the 60갑자 cycle."""

    return SEXAGENARY.index(pillar)


def index_to_pillar(idx: int) -> str:
    """Return the pillar at the given index (mod 60)."""

    return SEXAGENARY[idx % 60]


def next_pillar(pillar: str, step: int = 1) -> str:
    """Advance forward (or backward) within the 60갑자 cycle."""

    base = pillar_to_index(pillar)
    return index_to_pillar(base + step)
