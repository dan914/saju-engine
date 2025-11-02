"""
합화오행 트랜스포머 v1.2.0

관계 분석 결과(relations)를 바탕으로 오행 분포(dist_raw)를 가중 이동하여 정규화합니다.
- 관계별 가중 이동(삼합/육합/천간합/충)
- 우선순위 적용(동일 order 내 첫 등장 우선)
- 이동은 보존적(총합 1.0 유지), 이후 정규화
- Trace: reason/target/moved_ratio/weight/order/policy_signature

공개 API:
    transform_wuxing(relations: dict, dist_raw: dict, policy: dict|None) -> (dict, list[dict])
    normalize_distribution(dist: dict) -> dict
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


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
ELEMENTS: List[str] = ["wood", "fire", "earth", "metal", "water"]

POLICY_VERSION: str = "combination_element_v1.2.0"

# 기본 정책 스펙(비율/우선순위)
_DEFAULT_POLICY_SPEC: Dict[str, Dict[str, float | int]] = {
    "sanhe": {"ratio": 0.20, "order": 1},  # 局成
    "liuhe": {"ratio": 0.10, "order": 2},  # 육합
    "stem_combo": {"ratio": 0.08, "order": 3},  # 천간합
    "clash": {"ratio": -0.10, "order": 4},  # 충(감소)
}


# --- 정책 로드/검증/서명 ------------------------------------------------------
def _try_load_override() -> Dict[str, Dict[str, float | int]] | None:
    """정책 오버라이드 파일 로딩(선택)"""
    candidates = [
        Path("policies") / "combination_policy_v1.json",
        Path("saju_codex_batch_all_v2_6_signed") / "policies" / "combination_policy_v1.json",
        Path(__file__).resolve().parents[4]
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "combination_policy_v1.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return _validate_policy(data)
        except Exception:
            return None
    return None


def _validate_policy(data: dict | None) -> Dict[str, Dict[str, float | int]]:
    """비율/우선순위를 검증하고 기본 정책에 병합한다."""
    spec = {
        k: {"ratio": float(v["ratio"]), "order": int(v["order"])}
        for k, v in _DEFAULT_POLICY_SPEC.items()
    }
    if not data:
        return spec
    for key, val in data.items():
        if key not in spec:
            raise ValueError(f"알 수 없는 정책 키: {key}")
        if not (isinstance(val, dict) and "ratio" in val and "order" in val):
            raise ValueError(f"정책 형식 오류: {key} -> {val}")
        r = float(val["ratio"])
        o = int(val["order"])
        if not (-1.0 <= r <= 1.0):
            raise ValueError(f"정책 비율 범위 오류: {key}.ratio={r}")
        if o < 1 or o > 9:
            raise ValueError(f"정책 우선순위 범위 오류: {key}.order={o}")
        spec[key] = {"ratio": r, "order": o}
    return spec


_OVERRIDE = _try_load_override()
POLICY_SPEC: Dict[str, Dict[str, float | int]] = _OVERRIDE if _OVERRIDE else _validate_policy(None)
POLICY_SIGNATURE: str = _canonical_json_signature(
    {"version": POLICY_VERSION, "policy": POLICY_SPEC}
)


# --- 정규화 유틸 -------------------------------------------------------------
def normalize_distribution(dist: Dict[str, float]) -> Dict[str, float]:
    """오행 분포를 0..1 클램프 후 합 1.0이 되도록 정규화한다(공정성 강화 버전).
    1) 1차 정규화 → 2) 잔차를 비례 분산 → 3) 음수 발생 시 0 클램프 후 단일 보정."""
    vals = {e: max(0.0, float(dist.get(e, 0.0))) for e in ELEMENTS}
    s = sum(vals.values())
    if s <= 0.0:
        base = 1.0 / len(ELEMENTS)
        return {e: base for e in ELEMENTS}
    out = {e: vals[e] / s for e in ELEMENTS}
    total = sum(out.values())
    resid = 1.0 - total
    if abs(resid) > 1e-12:
        # (a) 잔차를 현재 비중에 비례하여 분산
        for e in ELEMENTS:
            out[e] += resid * out[e]
        # (b) 음수 방지 및 재정렬
        for e in ELEMENTS:
            if out[e] < 0.0:
                out[e] = 0.0
        # (c) 미세 잔차가 남으면(드물게) 최대값 한 곳에만 최종 보정
        total2 = sum(out.values())
        resid2 = 1.0 - total2
        if abs(resid2) > 1e-12:
            max_e = max(out, key=lambda k: out[k])
            out[max_e] = max(0.0, min(1.0, out[max_e] + resid2))
    return out


# --- 내부: 관계 스캔 ---------------------------------------------------------
def _gather_targets(relations: dict, reason: str) -> List[str]:
    """
    입력 relations에서 해당 reason에 해당하는 타겟 element 후보를 원본 순서로 반환.
    sanhe: formed=True인 항목만
    liuhe: 단순 후보
    stem_combo: heavenly.stem_combos | heavenly.stem_combo
    clash: 감소 대상
    """
    results: List[str] = []

    def _from(path: Tuple[str, str]) -> List[dict]:
        top, key = path
        obj = relations.get(top, {}) if isinstance(relations, dict) else {}
        arr = obj.get(key, []) if isinstance(obj, dict) else []
        if isinstance(arr, dict):
            arr = [arr]
        return arr if isinstance(arr, list) else []

    if reason == "sanhe":
        for item in _from(("earth", "sanhe")):
            if isinstance(item, dict) and item.get("formed") and item.get("element") in ELEMENTS:
                results.append(item["element"])
            elif isinstance(item, dict) and item.get("element") not in (None, *ELEMENTS):
                raise ValueError(f"알 수 없는 요소(element): {item.get('element')}")
    elif reason == "liuhe":
        for item in _from(("earth", "liuhe")):
            if isinstance(item, dict) and item.get("element") in ELEMENTS:
                results.append(item["element"])
            elif isinstance(item, dict) and item.get("element") not in (None, *ELEMENTS):
                raise ValueError(f"알 수 없는 요소(element): {item.get('element')}")
    elif reason == "stem_combo":
        arr = _from(("heavenly", "stem_combos")) + _from(("heavenly", "stem_combo"))
        for item in arr:
            if isinstance(item, dict) and item.get("element") in ELEMENTS:
                results.append(item["element"])
            elif isinstance(item, dict) and item.get("element") not in (None, *ELEMENTS):
                raise ValueError(f"알 수 없는 요소(element): {item.get('element')}")
    elif reason == "clash":
        for item in _from(("earth", "clash")):
            if isinstance(item, dict) and item.get("element") in ELEMENTS:
                results.append(item["element"])
            elif isinstance(item, dict) and item.get("element") not in (None, *ELEMENTS):
                raise ValueError(f"알 수 없는 요소(element): {item.get('element')}")
    else:
        raise ValueError(f"알 수 없는 규칙(reason): {reason}")
    return results


# --- 내부: 이동 로직 ----------------------------------------------------------
def _apply_move(
    dist: Dict[str, float],
    target: str,
    ratio: float,
    reason: str,
    order: int,
    trace: List[Dict[str, object]],
) -> None:
    """
    비율>0: '타 요소들에서 총 ratio 만큼 비례 차감 → target에 가산'
    비율<0: 'target에서 총 |ratio| 만큼 차감 → 타 요소들에 비례 가산'
    가용량 부족 시 사용 가능한 범위 내에서만 이동(클램프)
    이동 후 즉시 정규화
    """
    if target not in ELEMENTS:
        raise ValueError(f"알 수 없는 요소(element): {target}")
    ratio = float(ratio)
    if ratio == 0.0:
        return
    # 현재 분포
    total_others = sum(v for e, v in dist.items() if e != target)
    moved = 0.0
    if ratio > 0.0:
        # 증가 이동
        if total_others <= 0.0:
            return
        req = min(ratio, total_others)
        for e in ELEMENTS:
            if e == target:
                continue
            share = dist[e] / total_others if total_others > 0 else 0.0
            delta = req * share
            take = min(delta, dist[e])
            dist[e] -= take
            moved += take
        dist[target] += moved
    else:
        # 감소 이동
        give_cap = min(abs(ratio), dist[target])
        if give_cap <= 0.0:
            return
        dist[target] -= give_cap
        remain_others = sum(v for e, v in dist.items() if e != target)
        if remain_others <= 0.0:
            # 모두 0인 특수 상황 → 균등 분배
            share = give_cap / (len(ELEMENTS) - 1)
            for e in ELEMENTS:
                if e == target:
                    continue
                dist[e] += share
        else:
            for e in ELEMENTS:
                if e == target:
                    continue
                share = dist[e] / remain_others
                dist[e] += give_cap * share
        moved = -give_cap
    # 정규화 및 Trace
    nd = normalize_distribution(dist)
    dist.clear()
    dist.update(nd)
    if abs(moved) > 1e-12:
        trace.append(
            {
                "reason": reason,
                "target": target,
                "moved_ratio": float(round(moved, 12)),
                "weight": ratio,
                "order": int(order),
                "policy_signature": POLICY_SIGNATURE,
            }
        )


# --- 공개 API ----------------------------------------------------------------
def transform_wuxing(
    relations: dict, dist_raw: dict, policy: Dict[str, Dict[str, float | int]] | None = None
) -> Tuple[Dict[str, float], List[Dict[str, object]]]:
    """
    관계(relations)에 따라 오행 분포(dist_raw)를 이동/정규화한다.
    order 오름차순으로 적용
    동일 order에서는 첫 등장 타겟만 적용
    """
    dist = normalize_distribution(dist_raw or {})
    # 정책 선택(함수 인자 우선 → 파일 오버라이드 → 기본)
    if policy is not None:
        spec = _validate_policy(policy)
    else:
        spec = POLICY_SPEC
    # 적용 순서 구성
    ordered = sorted(
        ((k, spec[k]["ratio"], spec[k]["order"]) for k in spec.keys()), key=lambda x: int(x[2])
    )
    trace: List[Dict[str, object]] = []
    for reason, ratio, order in ordered:
        targets = _gather_targets(relations or {}, reason)
        if not targets:
            continue
        # 동일 order에서는 첫 등장만 적용
        target = targets[0]
        _apply_move(dist, target, float(ratio), reason, int(order), trace)
    return dist, trace
