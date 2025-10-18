# -*- coding: utf-8 -*-
from app.core.master_orchestrator_real import MasterOrchestrator


class _StrengthOK:
    def evaluate(self, pillars=None, season=None, **kw):
        return {"phase":"왕","elements":{"wood":"high","fire":"normal","earth":"normal","metal":"low","water":"low"}}

class _RelationsOK:
    def evaluate(self, pillars=None, **kw):
        return {"flags":["combine"]}

class _ClimateOK:
    def evaluate(self, pillars=None, season=None, strength=None, **kw):
        return {"season":season,"flags":[],"balance_index":1}

class _YongshinOK:
    def select(self, day_master=None, strength=None, relations=None, climate=None, **kw):
        return {"primary":"화","confidence":0.8}

class _LuckOK:
    def compute(self, pillars=None, birth_dt=None, gender=None, **kw):
        return {"start_age":8,"direction":"forward","pillars":[]}

class _Korean:
    def enrich(self, data): return {"korean_labels":{"dummy":"ok"}}

class _School:
    def get_default(self): return {"id":"default"}

class _Reco:
    def filter(self, enriched, yongshin=None, structure=None): return []

def test_master_orchestrator_real_integration_with_injected_engines():
    orch = MasterOrchestrator(
        strength_engine=_StrengthOK(),
        relations_engine=_RelationsOK(),
        climate_engine=_ClimateOK(),
        yongshin_engine=_YongshinOK(),
        luck_engine=_LuckOK(),
        korean_enricher=_Korean(),
        school_manager=_School(),
        recommendation_guard=_Reco()
    )
    out = orch.analyze({"year":"庚辰","month":"丙午","day":"甲午","hour":"庚午"},
                       {"birth_dt":"1995-07-10T13:00:00","gender":"F","timezone":"Asia/Seoul"})
    assert out["status"] == "success"
    assert out["season"] == "여름"
    assert out["stage3"]["luck_flow"]["trend"] in ("rising","stable","declining")
