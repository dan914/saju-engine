"""
원진(Yuanjin) 탐지기 v1.1.0

KO-first 원진 탐지기 v1.1
- 정책: 원진쌍 6세트(기본값 또는 오버라이드 파일)
- 입력: 4지지(연/월/일/시), 전각 1자 지지만 허용
- 판정: 집합적 포함 여부로 O(1) 탐지 → 쌍 내부/목록 결정적 정렬
- 트레이스: 정책 버전/시그니처, 히트쌍, present_branches, pair_count

공개 API:
    detect_yuanjin(branches: list[str]) -> list[list[str]]
    apply_yuanjin_flags(branches: list[str]) -> dict
    explain_yuanjin(branches: list[str]) -> dict
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


# --- 인라인 시그니처 유틸리티 (infra.signatures 대체) ----------------------
def _canonical_json_signature(obj) -> str:
    """
    Compute SHA-256 signature of canonical JSON.
    Uses deterministic dict ordering (sort_keys=True).
    For strict RFC-8785 compliance, use canonicaljson library.
    """
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


# --- 상수 --------------------------------------------------------------------
BRANCHES: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_BR_INDEX: Dict[str, int] = {b: i for i, b in enumerate(BRANCHES)}

# 기본 정책(원진 6쌍) — 순서는 무관, 정렬은 런타임 규칙에 따름
DEFAULT_YUANJIN_PAIRS: List[List[str]] = [
    ["子", "未"],
    ["丑", "午"],
    ["寅", "巳"],
    ["卯", "辰"],
    ["申", "亥"],
    ["酉", "戌"],
]
POLICY_VERSION: str = "yuanjin_v1.1.0"


# --- 내부 유틸 (정책 로드 전에 필요) ------------------------------------------
def _sort_pair(a: str, b: str) -> Tuple[str, str]:
    """쌍 내부를 BRANCHES 인덱스 기준으로 정렬."""
    return (a, b) if _BR_INDEX[a] <= _BR_INDEX[b] else (b, a)


# --- 정책 로드/검증/서명 ------------------------------------------------------
def _try_load_override() -> List[List[str]] | None:
    """
    선택적 정책 오버라이드 로더.
    탐색 경로 후보:
      ./policies/yuanjin_policy_v1.json
      <repo>/saju_codex_batch_all_v2_6_signed/policies/yuanjin_policy_v1.json
    실패 시 None(내장 정책 사용). 경고 로그는 테스트 단순화를 위해 생략.
    """
    candidates = [
        Path("policies") / "yuanjin_policy_v1.json",
        Path("saju_codex_batch_all_v2_6_signed") / "policies" / "yuanjin_policy_v1.json",
        Path(__file__).resolve().parents[4]
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "yuanjin_policy_v1.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return _validate_and_normalize_pairs(data)
        except Exception:
            return None
    return None


def _validate_and_normalize_pairs(data: object) -> List[List[str]]:
    """
    정책 파일 유효성 검사 및 정규화.
    입력 형식: 배열의 배열, 각 항목은 길이 2 문자열(12지지) 쌍
    중복/역순은 집합적으로 1회만 인정
    반환: 쌍 내부를 BRANCHES 인덱스 기준 오름차순으로 정렬한 후,
          목록 전체도 동일 기준으로 정렬된 6쌍 리스트
    """
    if not isinstance(data, list):
        raise ValueError("정책 파일 형식 오류: 최상위는 배열이어야 합니다.")
    norm_set: Set[Tuple[str, str]] = set()
    for item in data:
        if not (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and all(isinstance(x, str) for x in item)
        ):
            raise ValueError(f"정책 항목 형식 오류: {item}")
        a, b = item[0], item[1]
        if a not in BRANCHES or b not in BRANCHES:
            raise ValueError(f"정책 항목 지지 오류: {item}")
        # 쌍 내부 정렬
        a, b = _sort_pair(a, b)
        norm_set.add((a, b))
    if len(norm_set) != 6:
        raise ValueError("정책에는 정확히 6개의 원진쌍이 필요합니다.")
    # 목록 정렬
    norm_list = sorted(norm_set, key=lambda ab: (_BR_INDEX[ab[0]], _BR_INDEX[ab[1]]))
    return [list(ab) for ab in norm_list]


_OVERRIDE = _try_load_override()
_POLICY_PAIRS: List[List[str]] = (
    _OVERRIDE if _OVERRIDE else _validate_and_normalize_pairs(DEFAULT_YUANJIN_PAIRS)
)

# 서명을 위한 결정적 사양 객체
_POLICY_SPEC: Dict[str, List[List[str]]] = {"pairs": _POLICY_PAIRS}
POLICY_SIGNATURE: str = _canonical_json_signature(_POLICY_SPEC)


# --- 내부 유틸 ---------------------------------------------------------------
def _validate_branches_4(branches: Iterable[str]) -> List[str]:
    """4지지 입력 검증(길이 4, 전각 1자, 12지지)."""
    arr = list(branches)
    if len(arr) != 4:
        raise ValueError("4지지는 길이 4의 리스트여야 합니다.")
    for b in arr:
        if not (isinstance(b, str) and len(b) == 1 and b in BRANCHES):
            raise ValueError(f"지지는 12지지 한 글자여야 합니다: {arr}")
    return arr


# --- 공개 API ----------------------------------------------------------------
def detect_yuanjin(branches: Iterable[str]) -> List[List[str]]:
    """
    4지지에서 원진쌍을 검출.
    집합적 포함 판정(위치 무관)
    쌍 내부/목록 모두 결정적 정렬
    """
    b4 = _validate_branches_4(branches)
    present = set(b4)
    hits: List[Tuple[str, str]] = []
    for a, b in _POLICY_PAIRS:
        if a in present and b in present:
            hits.append(_sort_pair(a, b))
    # 목록 정렬
    hits_sorted = sorted(hits, key=lambda ab: (_BR_INDEX[ab[0]], _BR_INDEX[ab[1]]))
    return [list(ab) for ab in hits_sorted]


def apply_yuanjin_flags(branches: Iterable[str]) -> Dict[str, object]:
    """
    4지지(연/월/일/시)에 원진 플래그 적용.
    반환: { "flags": [..4..], "pairs": [["…","…"], ...] }
    """
    b4 = _validate_branches_4(branches)
    pairs = detect_yuanjin(b4)
    hit_set = {x for pair in pairs for x in pair}
    flags = [bi in hit_set for bi in b4]
    return {"flags": flags, "pairs": pairs}


def explain_yuanjin(branches: Iterable[str]) -> Dict[str, object]:
    """
    트레이스: 정책 버전/서명, present_branches, hits, pair_count
    """
    b4 = _validate_branches_4(branches)
    hits = detect_yuanjin(b4)
    return {
        "policy_version": POLICY_VERSION,
        "policy_signature": POLICY_SIGNATURE,
        "present_branches": b4,
        "hits": hits,
        "pair_count": len(hits),
    }
