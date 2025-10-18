"""
Evidence Builder v1.0

Stage-1 엔진 산출물(void/yuanjin/wuxing_adjust)을 공통 스키마 단일 Evidence 객체로 수집
- 결정적 정렬, RFC-8785 근사 Canonical JSON + SHA-256 서명
- KO-first 주석, 간이 스키마 검증, 선택 섹션 생략 허용, Idempotent

공개 API:
    build_evidence(inputs: dict) -> dict
    add_section(ev: dict, section: dict) -> dict
    finalize_evidence(ev: dict) -> dict
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List


# --- 인라인 시그니처 유틸리티 (infra.signatures 대체) ----------------------
def _canonical_json_signature(obj) -> str:
    """
    Compute SHA-256 signature of canonical JSON.
    Uses deterministic dict ordering (sort_keys=True).
    For strict RFC-8785 compliance, use canonicaljson library.
    """
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


# Alias for compatibility
sha256_signature = _canonical_json_signature
canonical_dumps = lambda obj: json.dumps(
    obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
)


# --- 정책/상수 ---------------------------------------------------------------
POLICY_VERSION: str = "evidence_v1.0.0"
ALLOWED_TYPES: List[str] = [
    "void",
    "yuanjin",
    "wuxing_adjust",
    "shensha",
    "relation_hits",
    "strength",
]
REQUIRED_FIELDS: List[str] = [
    "type",
    "engine_version",
    "engine_signature",
    "source",
    "payload",
    "created_at",
]

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

POLICY_SPEC: Dict[str, Any] = {
    "version": POLICY_VERSION,
    "allowed_types": ALLOWED_TYPES,
    "required_fields": REQUIRED_FIELDS,
    "created_at_format": "YYYY-MM-DDTHH:MM:SSZ",
}
POLICY_SIGNATURE: str = sha256_signature(POLICY_SPEC)


# --- 헬퍼 --------------------------------------------------------------------
def _now_utc_iso() -> str:
    """UTC 초단위 ISO8601(Z) 타임스탬프."""
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_section_shape(section: Dict[str, Any]) -> Dict[str, Any]:
    """섹션 필수 필드/형식/enum을 간이 검증하고 정규화(불변성 유지)를 반환."""
    if not isinstance(section, dict):
        raise ValueError("섹션은 객체여야 합니다.")
    for f in REQUIRED_FIELDS:
        if f not in section:
            raise ValueError(f"섹션 필수 필드 누락: {f}")
    t = section["type"]
    if t not in ALLOWED_TYPES:
        raise ValueError(f"허용되지 않은 섹션 타입: {t}")
    if not isinstance(section["engine_version"], str) or not section["engine_version"]:
        raise ValueError("engine_version은 비어있지 않은 문자열이어야 합니다.")
    if not isinstance(section["engine_signature"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", section["engine_signature"]
    ):
        raise ValueError("engine_signature는 64자리 hex여야 합니다.")
    if not isinstance(section["source"], str) or not section["source"]:
        raise ValueError("source는 비어있지 않은 문자열이어야 합니다.")
    if not isinstance(section["payload"], dict):
        raise ValueError("payload는 객체여야 합니다.")
    created_at = section["created_at"]
    if not isinstance(created_at, str) or not ISO_Z_RE.fullmatch(created_at):
        raise ValueError("created_at은 UTC ISO8601(Z) 형식이어야 합니다.")
    # 불변 객체 생성(필드만 복사)
    out = {k: section[k] for k in REQUIRED_FIELDS}
    return out


def _canonical_section_signature(section: Dict[str, Any]) -> str:
    """섹션의 캐노니컬 서명(자기참조 필드 제외)."""
    base = _validate_section_shape(section)
    return sha256_signature(base)


def _canonical_evidence_signature(ev: Dict[str, Any]) -> str:
    """Evidence 전체의 캐노니컬 서명(evidence_signature 제외)."""
    base = {
        "evidence_version": ev["evidence_version"],
        "sections": ev.get("sections", []),
    }
    return sha256_signature(base)


def _normalize_inputs(inputs: Dict[str, Any], created_at: str) -> List[Dict[str, Any]]:
    """
    엔진별 원시 출력 → Evidence 섹션으로 정규화.
    void: explain_void()의 핵심 필드만 복사
    yuanjin: explain_yuanjin()의 핵심 필드만 복사
    wuxing_adjust: transform_wuxing()의 dist/trace
    """
    sections: List[Dict[str, Any]] = []
    # void
    if "void" in inputs and inputs["void"]:
        v = inputs["void"]
        for k in ["policy_version", "policy_signature", "day_index", "xun_start", "kong"]:
            if k not in v:
                raise ValueError(f"void 입력에 필수 키 누락: {k}")
        sec = {
            "type": "void",
            "engine_version": str(v["policy_version"]),
            "engine_signature": str(v["policy_signature"]),
            "source": "services/analysis-service/app/core/void.py",
            "payload": {
                "kong": list(v["kong"]),
                "day_index": int(v["day_index"]),
                "xun_start": int(v["xun_start"]),
            },
            "created_at": created_at,
        }
        sections.append(sec)
    # yuanjin
    if "yuanjin" in inputs and inputs["yuanjin"]:
        y = inputs["yuanjin"]
        for k in [
            "policy_version",
            "policy_signature",
            "present_branches",
            "hits",
            "pair_count",
        ]:
            if k not in y:
                raise ValueError(f"yuanjin 입력에 필수 키 누락: {k}")
        sec = {
            "type": "yuanjin",
            "engine_version": str(y["policy_version"]),
            "engine_signature": str(y["policy_signature"]),
            "source": "services/analysis-service/app/core/yuanjin.py",
            "payload": {
                "present_branches": list(y["present_branches"]),
                "hits": [list(p) for p in y["hits"]],
                "pair_count": int(y["pair_count"]),
            },
            "created_at": created_at,
        }
        sections.append(sec)
    # wuxing_adjust
    if "wuxing_adjust" in inputs and inputs["wuxing_adjust"]:
        w = inputs["wuxing_adjust"]
        if not isinstance(w, dict) or "dist" not in w or "trace" not in w:
            raise ValueError("wuxing_adjust 입력은 {'dist':{}, 'trace':[]} 형식이어야 합니다.")
        # 엔진 버전/시그니처(있으면 사용, 없으면 모듈에서 읽기→실패 시 fallback)
        engine_version = None
        engine_signature = None
        try:
            if "engine_version" in w and "engine_signature" in w:
                engine_version = str(w["engine_version"])
                engine_signature = str(w["engine_signature"])
            else:
                from app.core.combination_element import POLICY_SIGNATURE as _WS
                from app.core.combination_element import POLICY_VERSION as _WV

                engine_version, engine_signature = _WV, _WS
        except Exception:
            engine_version = engine_version or "combination_element_v1.2.0"
            engine_signature = engine_signature or sha256_signature({"fallback": "wuxing_adjust"})
        sec = {
            "type": "wuxing_adjust",
            "engine_version": engine_version,
            "engine_signature": engine_signature,
            "source": "services/analysis-service/app/core/combination_element.py",
            "payload": {
                "dist": dict(w["dist"]),
                "trace": list(w["trace"]),
            },
            "created_at": created_at,
        }
        sections.append(sec)
    return sections


# --- 공개 API ----------------------------------------------------------------
def add_section(ev: Dict[str, Any], section: Dict[str, Any]) -> Dict[str, Any]:
    """Evidence 객체에 섹션을 추가한다(중복 type 금지). section_signature를 부여한다."""
    if "evidence_version" not in ev:
        ev["evidence_version"] = POLICY_VERSION
    ev.setdefault("sections", [])
    # 중복 타입 금지
    if any(s.get("type") == section.get("type") for s in ev["sections"]):
        raise ValueError(f"섹션 타입 중복: {section.get('type')}")
    base = _validate_section_shape(section)
    sig = _canonical_section_signature(base)
    full = dict(base)
    full["section_signature"] = sig
    ev["sections"].append(full)
    return ev


def finalize_evidence(ev: Dict[str, Any]) -> Dict[str, Any]:
    """sections를 type 오름차순으로 정렬하고 evidence_signature를 계산한다."""
    if "sections" not in ev or not ev["sections"]:
        raise ValueError("sections가 비어 있습니다.")
    # 정렬(결정적)
    ev["sections"] = sorted(ev["sections"], key=lambda s: s["type"])
    # evidence_signature 부여
    ev["evidence_version"] = ev.get("evidence_version") or POLICY_VERSION
    ev["evidence_signature"] = _canonical_evidence_signature(ev)
    return ev


def build_evidence(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    엔진 원시 출력 묶음(inputs)을 Evidence로 수집.
    모든 섹션은 동일 created_at 타임스탬프를 공유(결정성 ↑)
    """
    created_at = _now_utc_iso()
    ev: Dict[str, Any] = {"evidence_version": POLICY_VERSION, "sections": []}
    sections = _normalize_inputs(inputs or {}, created_at)
    for sec in sections:
        add_section(ev, sec)
    return finalize_evidence(ev)
