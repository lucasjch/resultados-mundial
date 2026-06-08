# -*- coding: utf-8 -*-
# Tests unitarios para top_scorer.py

import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from top_scorer import (
    get_team_weights, distribute_goals, get_player_team,
    compute_top_scorers,
)

# ── get_team_weights ─────────────────────────────────────────────────

def test_get_team_weights_structure():
    weights = get_team_weights("Argentina")
    assert isinstance(weights, list)
    assert len(weights) > 0
    name, w, pos_w, goals, mins, pos = weights[0]
    assert isinstance(name, str)
    assert 0 < w <= 1
    assert pos_w in (0.0, 0.05, 0.4, 1.0)

def test_get_team_weights_normalized():
    weights = get_team_weights("Spain")
    total = sum(w for _, w, _, _, _, _ in weights)
    assert abs(total - 1.0) < 0.001

def test_get_team_weights_injured_excluded():
    from data import INJURED_OUT
    for team, injured in INJURED_OUT.items():
        if injured:
            weights = get_team_weights(team)
            weight_names = {w[0] for w in weights}
            for inj in injured:
                assert inj not in weight_names, f"{inj} should be excluded from {team}"
            break

def test_get_team_weights_no_gks():
    weights = get_team_weights("Brazil")
    for _, _, pos_w, _, _, pos in weights:
        assert pos_w > 0, f"Goalkeeper ({pos}) included in weights"

# ── distribute_goals ─────────────────────────────────────────────────

def test_distribute_goals_zero():
    result = distribute_goals("Argentina", 0)
    assert result == {}

def test_distribute_goals_sum():
    random.seed(42)
    result = distribute_goals("France", 4)
    assert sum(result.values()) == 4

def test_distribute_goals_all_players():
    random.seed(99)
    result = distribute_goals("Germany", 10)
    assert len(result) > 0
    assert all(v > 0 for v in result.values())

# ── get_player_team ──────────────────────────────────────────────────

def test_get_player_team_known():
    team = get_player_team("Lionel Messi")
    assert team == "Argentina" or team == "?"

def test_get_player_team_unknown():
    team = get_player_team("Nobody McNoName")
    assert team == "?"

# ── compute_top_scorers ──────────────────────────────────────────────

def _dummy_match(team_a, team_b, score_a, score_b):
    return {
        "team_a": team_a, "team_b": team_b,
        "score_a": score_a, "score_b": score_b,
        "venue": "Dallas",
    }

def test_compute_top_scorers_structure():
    group = [_dummy_match("Argentina", "Brazil", 3, 0)]
    ko = [_dummy_match("Argentina", "Germany", 2, 1)]
    top_list, goal_map = compute_top_scorers(group, ko, top_n=5)
    assert isinstance(top_list, list)
    assert isinstance(goal_map, dict)
    assert len(top_list) <= 5
    if top_list:
        name, team, goals = top_list[0]
        assert isinstance(name, str)
        assert isinstance(team, str)
        assert isinstance(goals, int)

def test_compute_top_scorers_reproducible():
    group = [_dummy_match("England", "France", 2, 1)]
    ko = []
    top1, _ = compute_top_scorers(group, ko, top_n=10)
    top2, _ = compute_top_scorers(group, ko, top_n=10)
    assert top1 == top2

def test_compute_top_scorers_total_goals():
    group = [_dummy_match("Spain", "Portugal", 5, 0)]
    ko = []
    top_list, goal_map = compute_top_scorers(group, ko, top_n=20)
    total = sum(goal_map.values())
    assert total == 5
