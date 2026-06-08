# -*- coding: utf-8 -*-
"""Tests para validation.py: estructura de datos y smoke test."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validation import (
    _HISTORICAL_MATCHES, _HISTORICAL_RANKINGS, _TOURNAMENT_VENUES,
    _build_teams_for_year, _rank_to_tier, _label_round,
)


def test_all_tournaments_present():
    assert len(_HISTORICAL_MATCHES) == 7
    for yr in ("1998", "2002", "2006", "2010", "2014", "2018", "2022"):
        assert yr in _HISTORICAL_MATCHES
        assert len(_HISTORICAL_MATCHES[yr]) == 64


def test_all_years_have_rankings():
    for yr in ("1998", "2002", "2006", "2010", "2014", "2018", "2022"):
        assert yr in _HISTORICAL_RANKINGS
        assert len(_HISTORICAL_RANKINGS[yr]) == 32


def test_match_format():
    for yr, matches in _HISTORICAL_MATCHES.items():
        for m in matches:
            assert len(m) == 5, f"{yr}: {m}"
            rnd, ta, tb, sa, sb = m
            assert isinstance(sa, int) and isinstance(sb, int)
            assert sa >= 0 and sb >= 0


def test_rank_to_tier():
    assert _rank_to_tier(1) == 1
    assert _rank_to_tier(5) == 1
    assert _rank_to_tier(6) == 2
    assert _rank_to_tier(30) == 4
    assert _rank_to_tier(61) == 7
    assert _rank_to_tier(80) == 8


def test_build_teams_structure():
    teams = _build_teams_for_year("2014")
    assert "Germany" in teams
    assert "Argentina" in teams
    d = teams["Brazil"]
    assert d["rank"] == 4
    assert d["tier"] == 1
    assert d["confederation"] == "CONMEBOL"


def test_label_round():
    assert _label_round("Group A") is False
    assert _label_round("Group H") is False
    assert _label_round("R16") is True
    assert _label_round("QF") is True
    assert _label_round("SF") is True
    assert _label_round("Final") is True
    assert _label_round("3rd") is True


def test_venues_all_years():
    assert len(_TOURNAMENT_VENUES) == 7
    for yr in ("1998", "2002", "2006", "2010", "2014", "2018", "2022"):
        assert yr in _TOURNAMENT_VENUES
        assert len(_TOURNAMENT_VENUES[yr]) >= 1


def test_smoke_run():
    from validation import run
    run()


def test_goalscoring_stats():
    for yr in ("1998", "2002", "2006", "2010", "2014", "2018", "2022"):
        for m in _HISTORICAL_MATCHES[yr]:
            assert m[3] >= 0 and m[4] >= 0
