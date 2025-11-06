# -*- coding: utf-8 -*-
"""
LuckCalculator v1.0 — Policy-driven decade luck (大運) generator

정책 준수:
- direction.rule: year_stem_yinyang_x_gender (matrix)
- start_age.method: solar_term_interval (3일=1년, half_up 소수1자리; 단, ctx에 값이 있으면 그대로 사용)
- generation.start_from_next_after_month: true → 월주 다음 갑자부터 대운1
- generation.age_series: step_years=10, count=10, display_decimals=0, display_round=floor
- generation.emit: {ten_god_for_stem, lifecycle_for_branch} → Hook로 주입 시 필드 추가

출력:
{
  "policy_version": "luck_pillars_v1",
  "direction": "forward" | "reverse",
  "start_age": <float>,                 # ctx 제공값 또는 정책 계산값
  "method": "<string>",                 # ctx.luck.method 또는 "solar_term_interval"
  "pillars": [
     {"pillar":"丙戌","start_age":7,"end_age":17,"decade":1, ...},
     ... (총 10개)
  ],
  "current_luck": {"pillar":"...","decade":<int>,"years_into_decade":<float>} | null,
  "policy_signature": "<sha256-hex>"
}
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# 60갑자 시퀀스 (결정적)
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
HEAVENLY = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_YINYANG = {
    "甲": "yang",
    "丙": "yang",
    "戊": "yang",
    "庚": "yang",
    "壬": "yang",
    "乙": "yin",
    "丁": "yin",
    "己": "yin",
    "辛": "yin",
    "癸": "yin",
}


def pillar_to_index(pillar: str) -> int:
    return SEXAGENARY.index(pillar)


def index_to_pillar(idx: int) -> str:
    return SEXAGENARY[idx % 60]


def stem_of(pillar: str) -> str:
    return pillar[0]


def branch_of(pillar: str) -> str:
    return pillar[1]


def build_pillar(stem: str, branch: str) -> str:
    return stem + branch


@dataclass
class BirthContext:
    sex: str  # "male" | "female"
    birth_ts: str  # ISO-8601 with TZ
    age_years_decimal: float
    luck: Dict[str, Any]  # {"direction"?, "start_age"?, "method"?, ...}
    solar_terms: Dict[str, str]  # {"next_jie_ts"?, "prev_jie_ts"?} (선택)


class LuckCalculator:
    def __init__(
        self,
        policy: Dict[str, Any],
        *,
        lifecycle_resolver: Optional[
            Callable[[str, str], Dict[str, Any]]
        ] = None,  # (stem,branch)-> {...}
        tengods_resolver: Optional[
            Callable[[str, str], str]
        ] = None,  # (day_stem, other_stem)-> "正官" ...
        day_stem_for_labels: Optional[str] = None,
    ):
        self.policy = policy
        self.lifecycle_resolver = lifecycle_resolver
        self.tengods_resolver = tengods_resolver
        self.day_stem_for_labels = day_stem_for_labels

    # ---------- Public ----------
    def evaluate(
        self, birth_ctx: Dict[str, Any], pillars: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        direction = self._resolve_direction(birth_ctx, pillars)
        start_age = self._resolve_start_age(birth_ctx, direction)  # float, ctx 우선

        # 앵커: 정책에 anchor가 없으면 month 고정
        anchor_key = self.policy.get("anchor", "month")
        anchor_pillar = build_pillar(pillars[anchor_key]["stem"], pillars[anchor_key]["branch"])

        # offset: 정책은 start_from_next_after_month 로 표현됨 (true → 1, false → 0)
        start_from_next = self.policy.get("generation", {}).get("start_from_next_after_month", True)
        offset = 1 if start_from_next else 0

        count = self.policy["generation"]["age_series"]["count"]
        step_years = self.policy["generation"]["age_series"]["step_years"]

        base_idx = pillar_to_index(anchor_pillar)
        seq = self._sequence(base_idx=base_idx, direction=direction, n=count, offset=offset)

        # 항목 구성 (표시용 나이: display_round 규칙 적용)
        pillars_out: List[Dict[str, Any]] = []
        for i, p in enumerate(seq, start=1):
            s_raw = start_age + step_years * (i - 1)
            e_raw = start_age + step_years * i
            s_disp = self._disp_round(s_raw)
            e_disp = self._disp_round(e_raw)

            item = {"pillar": p, "start_age": s_disp, "end_age": e_disp, "decade": i}

            # 선택 라벨링
            emit = self.policy["generation"]["emit"]
            if emit.get("ten_god_for_stem") and self.tengods_resolver and self.day_stem_for_labels:
                item["ten_god"] = self.tengods_resolver(self.day_stem_for_labels, stem_of(p))
            if emit.get("lifecycle_for_branch") and self.lifecycle_resolver:
                item["lifecycle"] = self.lifecycle_resolver(stem_of(p), branch_of(p))

            pillars_out.append(item)

        # 현재 대운(경계 판단은 raw로 계산; 표시값과 무관)
        current = self._current_decade(
            age=birth_ctx["age_years_decimal"], start_age=start_age, step=step_years, seq=seq
        )

        out = {
            "policy_version": "luck_pillars_v1",
            "direction": direction,
            "start_age": float(start_age),  # ctx 값을 변형하지 않고 그대로 유지
            "method": (birth_ctx.get("luck") or {}).get("method", "solar_term_interval"),
            "pillars": pillars_out,
            "current_luck": current,
        }
        out["policy_signature"] = self._sha256_canonical(out)
        return out

    # ---------- Internals ----------
    def _sequence(self, base_idx: int, direction: str, n: int, offset: int) -> List[str]:
        """
        기대: offset=1이면 '앵커 다음 갑자'가 대운1의 pillar (순행/역행 모두 지원).
        index(i) = base_idx + step * (offset + i - 1)
        """
        step = 1 if direction == "forward" else -1
        return [index_to_pillar(base_idx + step * (offset + i - 1)) for i in range(1, n + 1)]

    def _resolve_direction(
        self, birth_ctx: Dict[str, Any], pillars: Dict[str, Dict[str, str]]
    ) -> str:
        in_dir = (birth_ctx.get("luck") or {}).get("direction")
        if in_dir in ("forward", "reverse"):
            return in_dir

        year_stem = pillars["year"]["stem"]
        yinyang = STEM_YINYANG[year_stem]  # "yang"/"yin"
        gender = birth_ctx["sex"]  # "male"/"female"
        matrix = self.policy["direction"]["matrix"]
        val = matrix[gender][yinyang]  # "forward" | "backward"
        return "forward" if val == "forward" else "reverse"

    def _resolve_start_age(self, birth_ctx: Dict[str, Any], direction: str) -> float:
        luck = birth_ctx.get("luck") or {}
        if isinstance(luck.get("start_age"), (int, float)):
            return float(luck["start_age"])

        # 정책 계산 경로 (solar_term_interval)
        st_conf = self.policy["start_age"]
        assert st_conf["method"] == "solar_term_interval"

        ref = st_conf["reference"]
        ref_dir = ref["forward"] if direction == "forward" else ref["backward"]  # "next"/"prev"
        assert ref["type"] == "jie"

        st = birth_ctx.get("solar_terms") or {}
        key = "next_jie_ts" if ref_dir == "next" else "prev_jie_ts"
        jie_ts = st.get(key)
        if not jie_ts:
            # 안전장치: 데이터 미제공 시 0.0 반환 (운영에서는 필수 주입 권장)
            return 0.0

        birth_dt = datetime.fromisoformat(birth_ctx["birth_ts"])
        jie_dt = datetime.fromisoformat(jie_ts)

        # FIX: 역행(reverse) 대운 시 출생일 → 이전 절기까지의 거리 (양수)
        if direction == "forward":
            hours = (jie_dt - birth_dt).total_seconds() / 3600.0
        else:  # reverse/backward
            hours = (birth_dt - jie_dt).total_seconds() / 3600.0

        days = hours / self.policy["start_age"]["conversion"]["hours_per_day"]  # 24
        years = days / self.policy["start_age"]["conversion"]["days_per_year"]  # 3.0

        # 반올림 규칙 적용
        r = self.policy["start_age"]["rounding"]
        return self._round_policy(years, decimals=int(r["decimals"]), mode=r["mode"])

    @staticmethod
    def _round_policy(x: float, *, decimals: int, mode: str) -> float:
        f = 10**decimals
        val = x * f
        if mode == "half_up":
            return math.floor(val + 0.5) / f
        if mode == "floor":
            return math.floor(val) / f
        if mode == "ceil":
            return math.ceil(val) / f
        return round(x, decimals)

    def _disp_round(self, x: float) -> float:
        series = self.policy["generation"]["age_series"]
        decimals = int(series.get("display_decimals", 0))
        mode = series.get("display_round", "floor")
        f = 10**decimals
        val = x * f
        if mode == "floor":
            return math.floor(val) / f
        if mode == "ceil":
            return math.ceil(val) / f
        return math.floor(val + 0.5) / f

    def _current_decade(
        self, *, age: float, start_age: float, step: int, seq: List[str]
    ) -> Optional[Dict[str, Any]]:
        if age < start_age:
            return None
        # decade 번호 (1..len(seq)), 경계는 좌측 포함/우측 배타
        k = int((age - start_age) // step) + 1
        if k < 1 or k > len(seq):
            return None
        start_k = start_age + step * (k - 1)
        return {"pillar": seq[k - 1], "decade": k, "years_into_decade": round(age - start_k, 2)}

    @staticmethod
    def _sha256_canonical(obj_with_sig: Dict[str, Any]) -> str:
        o = copy.deepcopy(obj_with_sig)
        o.pop("policy_signature", None)
        data = json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(data).hexdigest()
