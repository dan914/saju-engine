# -*- coding: utf-8 -*-
import json, os

BASE = os.path.dirname(os.path.dirname(__file__))

def load(path):
    with open(os.path.join(BASE, path), 'r', encoding='utf-8') as f:
        return json.load(f)

def test_daily_has_compound_floor():
    data = load('policy/luck_daily_policy_v1_1_1.json')
    assert data['hierarchy']['compound_floor_daily'] >= 0.55

def test_relations_synergy_keys_present():
    data = load('policy/luck_daily_policy_v1_1_1.json')
    b = data['weights']['relations']['bonuses']
    assert 'synergy_taise_plus_day_branch_chung' in b and 'synergy_taise_plus_other_branch_chung' in b
