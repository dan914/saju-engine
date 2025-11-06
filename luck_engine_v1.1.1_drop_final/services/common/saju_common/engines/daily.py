# -*- coding: utf-8 -*-
from .utils.scoring import normalize, gate, score_sibsin, score_unseong12, score_taese, score_season
from .utils.relation_resolver import resolve as resolve_relations

class DailyLuckEngine:
    def __init__(self, policy):
        self.policy = policy

    def _score_day(self, ctx):
        pol = self.policy
        strength = ctx.strength_profile
        comps = {}
        comps['sibsin'] = score_sibsin(ctx.day_master, ctx.transit.day, pol, strength, pol['options']['include_hidden_stems'])
        rel_list = ctx.relations_for_day()
        rel_break, rel_total = resolve_relations(rel_list, pol, level='daily', taese_branch=ctx.taese.branch, current_transit_branch=ctx.transit.day.branch)
        comps['relations'] = rel_total
        comps['relations_breakdown'] = rel_break
        comps['unseong12'] = score_unseong12(ctx.day_master.element, ctx.transit.day.branch, pol)
        comps['taese'] = score_taese(ctx.taese.branch, ctx.transit.day.branch, pol, ctx.relation_type)
        comps['season'] = score_season(ctx.day_master.element, ctx.transit.month.branch if getattr(ctx.transit, 'month', None) else None, pol, strength, level='day')

        R_day = sum(v for k,v in comps.items() if k in ('sibsin','relations','unseong12','taese','season'))
        h = pol['hierarchy']; gates=h['gates']; low,high=h['gate_clip']
        daewoon_norm = ctx.upper_scores.get('daewoon_norm', 0.0)
        year_norm = ctx.upper_scores.get('year_norm', 0.0)
        month_norm = ctx.upper_scores.get('month_norm', 0.0)
        g_daewoon = gate(daewoon_norm, gates['alpha'], low, high)
        g_year = gate(year_norm, gates['beta'], low, high)
        g_month = gate(month_norm, gates['gamma'], low, high)
        g_total = g_daewoon * g_year * g_month
        compound_floor = float(pol['hierarchy'].get('compound_floor_daily', 0.0) or 0.0)
        if compound_floor > 0.0:
            g_total = max(g_total, compound_floor)

        raw = R_day * g_total
        norm = normalize(raw, pol['normalization']['scale']['day'], pol['normalization']['clip'], pol['normalization']['method'])

        return {
            "score": {"final": norm, "raw": raw, "norm_meta": pol["normalization"]},
            "components": comps,
            "hierarchy": {
                "g_total": g_total, "g_daewoon": g_daewoon, "g_year": g_year, "g_month": g_month,
                "daewoon_norm": daewoon_norm, "year_norm": year_norm, "month_norm": month_norm
            },
            "policy_version": pol["policy_version"],
            "reproducibility": ctx.meta
        }
