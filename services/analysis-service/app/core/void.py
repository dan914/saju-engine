"""
공망(旬空) 계산 엔진 v1.1.0

KO-first 실무 구현.
- 공망(旬空) 계산은 일주(천간지지 2자) 기준의 60갑자 인덱스 → 旬 시작 인덱스(0/10/20/30/40/50) → 공망(지지 2자) 매핑으로 O(1) 처리.
- 입력은 전각 한자 2글자만 허용(공백/ASCII/혼입은 오류). 설명은 최소, 예외 메시지는 한글 우선.

공개 API:
    compute_void(day_pillar: str) -> list[str]
    apply_void_flags(branches: list[str], kong: list[str]) -> dict
    explain_void(day_pillar: str) -> dict

테스트/스키마/시그니처와 함께 사용됨. 정책 오버라이드 파일(policies/void_policy_v1.json)이 있으면 유효성 검증 후 적용.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# --- 인라인 시그니처 유틸리티 (infra.signatures 대체) ----------------------


def _canonical_json_signature(obj) -> str:
    """
    Compute SHA-256 signature of canonical JSON.
    Uses deterministic dict ordering (sort_keys=True).
    For strict RFC-8785 compliance, use canonicaljson library.
    """
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


# --- 상수(간지/테이블) -------------------------------------------------------
STEMS: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 60갑자 인덱스 (0..59)
JIAZI_60: List[str] = [
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

# 기본 정책 사양: 旬 시작 인덱스 → 공망(지지 2개)
_DEFAULT_POLICY_SPEC: Dict[int, List[str]] = {
    0: ["戌", "亥"],  # 甲子旬
    10: ["申", "酉"],  # 甲戌旬
    20: ["午", "未"],  # 甲申旬
    30: ["辰", "巳"],  # 甲午旬
    40: ["寅", "卯"],  # 甲辰旬
    50: ["子", "丑"],  # 甲寅旬
}
POLICY_VERSION: str = "void_calc_v1.1.0"


# --- 정책 로딩/검증 ----------------------------------------------------------
def _try_load_override() -> Dict[int, List[str]] | None:
    """
    선택적 정책 오버라이드 로더.
    탐색 경로: CWD/policies/void_policy_v1.json → repo-root 추정(/policies/void_policy_v1.json)
    실패/불일치 시 None 반환(내장 정책 사용). 로그는 남기지 않음(테스트 환경 단순화).
    """
    candidates = [
        Path("policies") / "void_policy_v1.json",
        Path("saju_codex_batch_all_v2_6_signed") / "policies" / "void_policy_v1.json",
        Path(__file__).resolve().parents[4]
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "void_policy_v1.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return _validate_and_canonicalize_policy(data)
        except Exception:
            # 경고 로그 생략(사양상 주석으로만 표기). 내장 정책으로 폴백.
            return None
    return None


def _validate_and_canonicalize_policy(data: dict) -> Dict[int, List[str]]:
    """정책 파일 유효성 검사 및 정규화: 키를 int로, 값은 공망 지지 2개 리스트로 강제."""
    if not isinstance(data, dict):
        raise ValueError("정책 파일은 객체여야 합니다.")
    # 허용 키 집합
    allowed_starts = {0, 10, 20, 30, 40, 50}
    result: Dict[int, List[str]] = {}
    for k, v in data.items():
        try:
            kk = int(k)
        except Exception as e:
            raise ValueError(f"정책 키는 정수여야 합니다: {k}") from e
        if kk not in allowed_starts:
            raise ValueError(f"허용되지 않은 旬 시작 인덱스: {kk}")
        if not (
            isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, str) for x in v)
        ):
            raise ValueError(f"공망 값은 길이 2 문자열 리스트여야 합니다: {k} -> {v}")
        a, b = v[0], v[1]
        if a not in BRANCHES or b not in BRANCHES:
            raise ValueError(f"지지는 12지지여야 합니다: {v}")
        result[kk] = [a, b]
    if set(result.keys()) != allowed_starts:
        raise ValueError("모든 6개 旬 시작 인덱스(0,10,20,30,40,50)가 포함되어야 합니다.")
    return result


_OVERRIDE_SPEC = _try_load_override()
POLICY_SPEC: Dict[int, List[str]] = _OVERRIDE_SPEC if _OVERRIDE_SPEC else dict(_DEFAULT_POLICY_SPEC)
POLICY_SIGNATURE: str = _canonical_json_signature(POLICY_SPEC)


# --- 내부 유틸 ---------------------------------------------------------------
_KNOWN_CHARS = set("".join(JIAZI_60))


def _normalize_and_validate_day_pillar(day_pillar: str) -> Tuple[str, int, int]:
    """
    입력 검증:
    - 문자열, 공백 없음, 길이=2
    - 60갑자 목록에 존재
    반환: (원본, day_index, xun_start)
    """
    if not isinstance(day_pillar, str):
        raise ValueError("일주는 문자열이어야 합니다.")
    if any(ch.isspace() for ch in day_pillar):
        raise ValueError("입력에 공백이 포함될 수 없습니다.")
    if len(day_pillar) != 2:
        raise ValueError("일주는 전각 한자 2글자여야 합니다.")
    # 빠른 문자 집합 체크(ASCII 혼입 방지) 후 테이블 조회
    if not all(ch in _KNOWN_CHARS for ch in day_pillar):
        raise ValueError(f"알 수 없는 문자 포함: {day_pillar}")
    try:
        idx = JIAZI_60.index(day_pillar)
    except ValueError as e:
        raise ValueError(f"알 수 없는 일주(Unknown day pillar): {day_pillar}") from e
    xun_start = (idx // 10) * 10
    return day_pillar, idx, xun_start


def _validate_branches_4(branches: Iterable[str]) -> List[str]:
    """4지지 검증"""
    arr = list(branches)
    if len(arr) != 4:
        raise ValueError("4지지는 길이 4의 리스트여야 합니다.")
    for b in arr:
        if not isinstance(b, str) or len(b) != 1 or b not in BRANCHES:
            raise ValueError(f"지지는 12지지 한 글자여야 합니다: {arr}")
    return arr


def _validate_kong_2(kong: Iterable[str]) -> Tuple[str, str]:
    """공망 2지지 검증"""
    arr = list(kong)
    if len(arr) != 2:
        raise ValueError("공망(kong)은 길이 2여야 합니다.")
    a, b = arr[0], arr[1]
    if a not in BRANCHES or b not in BRANCHES:
        raise ValueError("공망 지지는 12지지여야 합니다.")
    return a, b


# --- 공개 API ----------------------------------------------------------------
def compute_void(day_pillar: str) -> List[str]:
    """일주의 旬을 찾아 해당 공망(旬空) 2지지를 반환한다. 순서는 정책대로 고정."""
    _, _, xun_start = _normalize_and_validate_day_pillar(day_pillar)
    kong = POLICY_SPEC.get(xun_start)
    if not kong:
        # 이 상태는 정책 손상 외에는 발생하지 않음
        raise RuntimeError(f"旬 매핑을 찾을 수 없습니다: start={xun_start}")
    return [kong[0], kong[1]]


def apply_void_flags(branches: Iterable[str], kong: Iterable[str]) -> Dict[str, object]:
    """
    4지지(연/월/일/시)에 공망 플래그를 적용.
    반환: { "flags": [bool,bool,bool,bool], "hit_branches": [..] }
    """
    b4 = _validate_branches_4(branches)
    a, b = _validate_kong_2(kong)
    kset = {a, b}
    flags = [bi in kset for bi in b4]
    hits = [bi for bi in b4 if bi in kset]
    return {"flags": flags, "hit_branches": hits}


def explain_void(day_pillar: str) -> Dict[str, object]:
    """
    계산 근거를 포함한 설명(Trace) 반환.
    {"policy_version": "...","policy_signature": "...","day_index": int,"xun_start": int,"kong": ["…","…"]}
    """
    _, idx, xun_start = _normalize_and_validate_day_pillar(day_pillar)
    kong = compute_void(day_pillar)
    return {
        "policy_version": POLICY_VERSION,
        "policy_signature": POLICY_SIGNATURE,
        "day_index": idx,
        "xun_start": xun_start,
        "kong": kong,
    }
