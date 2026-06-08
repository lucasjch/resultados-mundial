# -*- coding: utf-8 -*-
# Tests unitarios para bracket.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data import haversine
from bracket import (
    _venue_dist, _rest_days_since, _h2h_key, _sort_group,
    _ranking_winner, classify_stakes, simulate_group_stage,
    determine_qualified, build_round_of_32,
    simulate_knockout_round, compute_team_history,
    run_full_simulation, _h2h_matches, R32_BRACKET,
)

# ── _venue_dist ──────────────────────────────────────────────────────

def test_venue_dist_known():
    d = _venue_dist("New York", "Boston")
    assert d > 200, f"NY→Boston should be ~300km, got {d}"
    assert d < 400, f"NY→Boston should be ~300km, got {d}"

def test_venue_dist_zero():
    d = _venue_dist("Dallas", "Dallas")
    assert d == 0, f"Same venue should be 0km, got {d}"

def test_venue_dist_unknown():
    d = _venue_dist("Nowhere", "Boston")
    assert d == 0, "Unknown venue should return 0"

# ── _rest_days_since ─────────────────────────────────────────────────

def test_rest_days_none():
    assert _rest_days_since(None, "2026-07-01") == 5

def test_rest_days_same_day():
    assert _rest_days_since("2026-06-11", "2026-06-11") == 0

def test_rest_days_three():
    assert _rest_days_since("2026-06-08", "2026-06-11") == 3

def test_rest_days_five():
    assert _rest_days_since("2026-06-06", "2026-06-11") == 5

def test_rest_days_bad_date():
    assert _rest_days_since("not-a-date", "2026-06-11") == 5

# ── _h2h_key ─────────────────────────────────────────────────────────

def _setup_h2h():
    _h2h_matches.clear()
    _h2h_matches["X"] = {
        "TeamA": {"TeamB": [{"goals_a": 2, "goals_b": 1}]},
        "TeamB": {"TeamA": [{"goals_a": 1, "goals_b": 2}]},
    }
    return _h2h_matches

def test_h2h_key_winner():
    _setup_h2h()
    key = _h2h_key("TeamA", "X", {"TeamA", "TeamB"})
    assert key == (3, 1, 2), f"TeamA should have 3pts +1GD +2GF, got {key}"

def test_h2h_key_loser():
    _setup_h2h()
    key = _h2h_key("TeamB", "X", {"TeamA", "TeamB"})
    assert key == (0, -1, 1), f"TeamB should have 0pts -1GD +1GF, got {key}"

def test_h2h_key_irrelevant_opponent():
    _setup_h2h()
    key = _h2h_key("TeamA", "X", {"TeamA", "TeamC"})
    assert key == (0, 0, 0), "No H2H vs TeamC"

# ── _sort_group ──────────────────────────────────────────────────────

_REAL_GROUPS = None

def _get_test_teams():
    global _REAL_GROUPS
    if _REAL_GROUPS is None:
        from data import GROUPS
        _REAL_GROUPS = GROUPS
    return sorted(set(t for g in _REAL_GROUPS.values() for t in g))


def test_sort_group_by_pts():
    teams = _get_test_teams()[:4]
    s = {t: {"pts": 6 - i*1, "gd": 3 - i, "gf": 5 - i, "fp": 0, "w": 2-i, "d": i%2, "l": i, "ga": i}
         for i, t in enumerate(teams)}
    sorted_teams = _sort_group("A", s)
    assert sorted_teams[0][1]["pts"] >= sorted_teams[-1][1]["pts"]


def test_sort_group_tiebreaker_h2h():
    teams = _get_test_teams()[:4]
    s = {t: {"pts": 4, "gd": 0, "gf": 2, "fp": 0, "w": 1, "d": 1, "l": 1, "ga": 2}
         for t in teams[:3]}
    s[teams[3]] = {"pts": 0, "gd": -3, "gf": 1, "fp": 0, "w": 0, "d": 0, "l": 3, "ga": 5}
    _h2h_matches.clear()
    _h2h_matches["A"] = {
        teams[0]: {teams[1]: [{"goals_a": 2, "goals_b": 0}]},
        teams[1]: {teams[0]: [{"goals_a": 0, "goals_b": 2}]},
    }
    sorted_teams = _sort_group("A", s)
    assert sorted_teams[0][0] == teams[0]

# ── _ranking_winner ──────────────────────────────────────────────────

def test_ranking_winner():
    data_a = {"rank": 5}
    data_b = {"rank": 50}
    w, l = _ranking_winner("Brazil", "Haiti", data_a, data_b)
    assert w == "Brazil"
    assert l == "Haiti"

def test_ranking_winner_reverse():
    data_a = {"rank": 80}
    data_b = {"rank": 3}
    w, l = _ranking_winner("Panama", "France", data_a, data_b)
    assert w == "France"
    assert l == "Panama"

def test_ranking_winner_equal():
    data_a = {"rank": 20}
    data_b = {"rank": 20}
    w, l = _ranking_winner("TeamA", "TeamB", data_a, data_b)
    assert w in ("TeamA", "TeamB")

# ── classify_stakes ──────────────────────────────────────────────────

def test_stakes_qualified():
    st = {"A": {"pts": 6, "gd": 5, "gf": 8}, "B": {"pts": 3, "gd": 0, "gf": 2},
          "C": {"pts": 1, "gd": -2, "gf": 0}, "D": {"pts": 0, "gd": -3, "gf": 1}}
    s = classify_stakes(st)
    assert s["A"] == "qualified"

def test_stakes_eliminated_max():
    st = {"A": {"pts": 6, "gd": 5, "gf": 8}, "B": {"pts": 4, "gd": 0, "gf": 2},
          "C": {"pts": 1, "gd": -2, "gf": 0}, "D": {"pts": 0, "gd": -3, "gf": 1}}
    s = classify_stakes(st)
    assert s["D"] == "eliminated"

def test_stakes_contender():
    st = {"A": {"pts": 6, "gd": 3, "gf": 5}, "B": {"pts": 3, "gd": 1, "gf": 3},
          "C": {"pts": 3, "gd": -1, "gf": 2}, "D": {"pts": 0, "gd": -3, "gf": 0}}
    s = classify_stakes(st)
    assert s["B"] == "contender"
    assert s["C"] == "contender"

def test_stakes_eliminated_zero():
    st = {"A": {"pts": 6, "gd": 5, "gf": 8}, "B": {"pts": 4, "gd": 0, "gf": 2},
          "C": {"pts": 0, "gd": -2, "gf": 0}, "D": {"pts": 0, "gd": -3, "gf": 1}}
    s = classify_stakes(st)
    assert s["C"] == "eliminated"

# ── simulate_group_stage ─────────────────────────────────────────────

def make_group_prediction(team_a, team_b, score_a, score_b, group="A"):
    return {
        "team_a": team_a, "team_b": team_b,
        "score_a": score_a, "score_b": score_b,
        "round": f"Group {group}", "venue": "Dallas",
    }

def test_simulate_group_stage_structure():
    from data import GROUPS
    # Use real group A teams
    r = GROUPS["A"]
    preds = [
        make_group_prediction(r[0], r[1], 2, 0, group="A"),
        make_group_prediction(r[2], r[3], 1, 1, group="A"),
        make_group_prediction(r[0], r[2], 3, 1, group="A"),
        make_group_prediction(r[1], r[3], 1, 0, group="A"),
        make_group_prediction(r[0], r[3], 2, 0, group="A"),
        make_group_prediction(r[1], r[2], 1, 2, group="A"),
    ]
    results = simulate_group_stage(preds)
    assert "A" in results
    assert len(results["A"]) == 4
    assert results["A"][0][1]["pts"] == 9

def test_simulate_group_stage_points():
    from data import GROUPS
    r = GROUPS["B"]
    preds = [
        make_group_prediction(r[0], r[1], 1, 0, group="B"),
        make_group_prediction(r[2], r[3], 0, 0, group="B"),
    ]
    results = simulate_group_stage(preds)
    # Canada 1-0 Bosnia, Qatar 0-0 Switzerland
    assert results["B"][0][1]["pts"] == 3
    assert results["B"][3][1]["pts"] == 0
    assert results["B"][1][1]["pts"] == 1
    assert results["B"][2][1]["pts"] == 1

# ── determine_qualified ──────────────────────────────────────────────

def test_determine_qualified_structure():
    group_results = {}
    from data import GROUPS
    for g in GROUPS:
        group_results[g] = [(t, {"pts": 6 - i*2, "gd": 3 - i, "gf": 5 - i, "fp": 0}) for i, t in enumerate(GROUPS[g])]
    winners, runners, third, third_det = determine_qualified(group_results)
    assert len(winners) == 12
    assert len(runners) == 12
    assert len(third) == 8

# ── build_round_of_32 ────────────────────────────────────────────────

def test_build_round_of_32_count():
    from data import GROUPS
    gw = {g: GROUPS[g][0] for g in GROUPS}
    gr = {g: GROUPS[g][1] for g in GROUPS}
    bt = [GROUPS[g][2] for g in list(GROUPS)[:8]]
    bt_det = [(g, GROUPS[g][2], 3, 0, 2, 0, 50) for g in list(GROUPS)[:8]]
    matches = build_round_of_32(gw, gr, bt, bt_det)
    assert len(matches) == 16

# ── simulate_knockout_round ──────────────────────────────────────────

def test_knockout_no_draws():
    matches = [("Argentina", "Haiti", "Miami"), ("Spain", "Panama", "Miami")]
    results = simulate_knockout_round(matches, round_name="R32")
    assert len(results) == 2
    for r in results:
        assert r["winner"] != "Empate"
        assert r["score_a"] >= 0
        assert r["score_b"] >= 0
        assert "confidence" in r

# ── compute_team_history ─────────────────────────────────────────────

def test_compute_team_history():
    preds = [
        {"team_a": "Mexico", "team_b": "Brazil", "venue": "Mexico City", "date": "2026-06-11"},
        {"team_a": "Mexico", "team_b": "France", "venue": "Guadalajara", "date": "2026-06-15"},
    ]
    h = compute_team_history(preds)
    assert "Mexico" in h
    assert h["Mexico"]["total_travel"] > 0
    assert h["Mexico"]["last_venue"] == "Guadalajara"

# ── run_full_simulation smoke test ───────────────────────────────────

def test_run_full_simulation_smoke():
    gp, gr, ko = run_full_simulation(seed=42, quiet=True)
    assert len(gp) == 72
    assert len(ko) == 16 + 8 + 4 + 2 + 1 + 1
