# -*- coding: utf-8 -*-
# Tests unitarios para data.py

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data import (
    GROUPS, FIXTURES, VENUES, CITY_COORDS, TEAMS,
    VENUE_TIMEZONES, HOME_TIMEZONES, BASE_CAMPS,
    get_team, get_venue, get_group_teams,
    get_group_fixtures, get_matchday, haversine,
    _CONF_CARD_RATES, _FANBASE, _MARKET_VALUE_ESTIMATES,
    _FOREIGN_PCT_ESTIMATES,
)

# ── Structure counts ─────────────────────────────────────────────────

def test_groups_count():
    assert len(GROUPS) == 12

def test_teams_per_group():
    for g, teams in GROUPS.items():
        assert len(teams) == 4, f"Group {g} has {len(teams)} teams"

def test_all_48_teams_have_data():
    enriched_keys = {"market_value_total", "market_value_avg", "avg_age", "avg_caps",
                     "avg_trophies", "avg_height", "club_pairs", "foreign_pct",
                     "global_fanbase", "yellow_rate", "red_rate"}
    for g in GROUPS:
        for team in GROUPS[g]:
            assert team in TEAMS, f"Team {team} missing from TEAMS"
            d = TEAMS[team]
            for key in enriched_keys:
                assert key in d, f"Team {team} missing key {key}"

def test_fixtures_count():
    assert len(FIXTURES) == 72, f"Expected 72 fixtures, got {len(FIXTURES)}"

def test_fixtures_per_group():
    for g in GROUPS:
        gf = [f for f in FIXTURES if f[5] == g]
        assert len(gf) == 6, f"Group {g} has {len(gf)} fixtures (expected 6)"

def test_venues_count():
    assert len(VENUES) == 16

def test_venue_timezones_all_venues():
    for venue in VENUES:
        assert venue in VENUE_TIMEZONES, f"{venue} missing from VENUE_TIMEZONES"

def test_home_timezones_all_teams():
    for g in GROUPS:
        for team in GROUPS[g]:
            assert team in HOME_TIMEZONES, f"{team} missing from HOME_TIMEZONES"

def test_base_camps_all_teams():
    for g in GROUPS:
        for team in GROUPS[g]:
            assert team in BASE_CAMPS, f"{team} missing BASE_CAMPS"

# ── haversine ────────────────────────────────────────────────────────

def test_haversine_zero():
    assert haversine(0, 0, 0, 0) == 0

def test_haversine_known():
    d = haversine(40.7128, -74.0060, 42.3601, -71.0589)
    assert 250 < d < 400

def test_haversine_symmetric():
    d1 = haversine(20, -100, 30, -80)
    d2 = haversine(30, -80, 20, -100)
    assert abs(d1 - d2) < 0.001

# ── get_team ─────────────────────────────────────────────────────────

def test_get_team_valid():
    d = get_team("Argentina")
    assert d["rank"] > 0
    assert d["tier"] > 0

def test_get_team_invalid():
    with pytest.raises(KeyError):
        get_team("NonExistentTeam")

# ── get_venue ────────────────────────────────────────────────────────

def test_get_venue():
    v = get_venue("Mexico City")
    assert "stadium" in v
    assert "capacity" in v
    assert "country" in v

def test_get_venue_invalid():
    with pytest.raises(KeyError):
        get_venue("Nowhere")

# ── get_group_teams / get_group_fixtures ─────────────────────────────

def test_get_group_teams():
    t = get_group_teams("A")
    assert len(t) == 4
    assert t == GROUPS["A"]

def test_get_group_fixtures():
    f = get_group_fixtures("B")
    assert len(f) == 6

# ── get_matchday ─────────────────────────────────────────────────────

def test_get_matchday_md1():
    gf = get_group_fixtures("C")
    for idx, f in enumerate(FIXTURES):
        if f[5] == "C":
            md = get_matchday(idx, FIXTURES)
            assert md == (gf.index(f) // 2) + 1, f"Fixture {idx} {f} MD mismatch"
            break

def test_get_matchday_md1_first():
    for idx, f in enumerate(FIXTURES):
        if f[5] == "D":
            md = get_matchday(idx, FIXTURES)
            assert md == 1
            return

def test_get_matchday_md3_last():
    for idx, f in reversed(list(enumerate(FIXTURES))):
        if f[5] == "E":
            md = get_matchday(idx, FIXTURES)
            assert md == 3
            return

# ── Card rates ───────────────────────────────────────────────────────

def test_all_confederations():
    expected = {"UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"}
    assert set(_CONF_CARD_RATES.keys()) == expected

def test_card_rates_values():
    for conf, rates in _CONF_CARD_RATES.items():
        assert 1.5 <= rates["yellow_rate"] <= 3.0
        assert 0.0 <= rates["red_rate"] <= 0.15

# ── Market value estimates ───────────────────────────────────────────

def test_market_value_estimates_all_teams():
    for g in GROUPS:
        for team in GROUPS[g]:
            assert team in _MARKET_VALUE_ESTIMATES, f"{team} missing MV estimate"

# ── Fanbase ──────────────────────────────────────────────────────────

def test_fanbase_range():
    for g in GROUPS:
        for team in GROUPS[g]:
            fb = _FANBASE.get(team, 0)
            assert 1 <= fb <= 10, f"{team} fanbase {fb} out of range"
