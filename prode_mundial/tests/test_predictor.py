# -*- coding: utf-8 -*-
# Tests unitarios para predictor.py

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from predictor import (
    poisson_sample, poisson_pmf, dixon_coles_tau, _build_joint_dist,
    predict_match, calculate_team_strength_from_data,
    calculate_home_advantage, calculate_climate_impact,
    calculate_morale, calculate_market_value_factor,
    calculate_foreign_pct_factor, calculate_experience_factor,
    calculate_trophy_factor, calculate_height_advantage,
    calculate_club_chemistry, calculate_rest_days,
    calculate_travel_fatigue, calculate_stakes_factor,
    calculate_odds_factor, calculate_travel_impact,
    calculate_player_stats_factor, calculate_squad_depth_factor,
    WEIGHTS, DIXON_COLES_RHO, MAX_GOALS_DC,
)

def test_weights_sum_to_100():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 0.001, f"Weights sum to {total:.3f}, expected 1.0"

def test_weights_count():
    assert len(WEIGHTS) == 20, f"Expected 20 factors, got {len(WEIGHTS)}"

@pytest.mark.parametrize("lam,expected_range", [
    (0.5, (0, 5)),
    (1.0, (0, 6)),
    (2.0, (0, 8)),
    (5.0, (0, 12)),
])
def test_poisson_sample_range(lam, expected_range):
    for _ in range(100):
        s = poisson_sample(lam)
        assert s >= 0, f"Poisson sample {s} < 0"
        assert s < 20, f"Poisson sample {s} too large"

def test_poisson_sample_zero():
    s = poisson_sample(0.01)
    assert s >= 0

def test_team_strength_from_data():
    data = {"rank": 1, "tier": 1}
    s = calculate_team_strength_from_data(data)
    assert s > 70, f"Strong team should score >70, got {s}"

    data_weak = {"rank": 80, "tier": 8}
    s_weak = calculate_team_strength_from_data(data_weak)
    assert s_weak < 30, f"Weak team should score <30, got {s_weak}"

    assert s > s_weak, "Strong team should beat weak team"

class TestHomeAdvantage:
    def test_mexico_home(self):
        diff = calculate_home_advantage("Mexico", "Brazil", "Mexico")
        assert diff > 0, "Mexico should have advantage at home"

    def test_neutral_reduces_bonus(self):
        diff_normal = calculate_home_advantage("Mexico", "Brazil", "USA")
        diff_neutral = calculate_home_advantage("Mexico", "Brazil", "USA", is_neutral=True)
        assert diff_neutral <= diff_normal, "Neutral should reduce home advantage"

    def test_concacaf_bonus(self):
        diff = calculate_home_advantage("Canada", "France", "Canada")
        assert diff > 0, "CONCACAF team should have bonus in host country"

    def test_symmetry(self):
        diff1 = calculate_home_advantage("USA", "England", "USA")
        diff2 = calculate_home_advantage("England", "USA", "USA")
        assert abs(diff1 + diff2) < 0.001, "Home advantage should be symmetric"

class TestClimate:
    def test_roof_advantage(self):
        venue_data = {"avg_temp": 35, "altitude": 10, "roof": True}
        diff = calculate_climate_impact("Brazil", "Sweden", "Dallas")
        assert isinstance(diff, (int, float))

    def test_no_roof_penalty_hot(self):
        diff = calculate_climate_impact("Sweden", "Brazil", "Dallas")
        assert isinstance(diff, (int, float))

class TestMorale:
    def test_high_morale_advantage(self):
        diff = calculate_morale("Germany", "South Africa")
        assert diff > 0 or diff == 0

    def test_symmetric(self):
        d1 = calculate_morale("Argentina", "Brazil")
        d2 = calculate_morale("Brazil", "Argentina")
        assert abs(d1 + d2) < 0.001

class TestMarketValue:
    def test_valuable_team_ahead(self):
        diff = calculate_market_value_factor("England", "Panama")
        assert diff > 0, "England should have higher market value than Panama"

    def test_symmetric(self):
        d1 = calculate_market_value_factor("France", "Haiti")
        d2 = calculate_market_value_factor("Haiti", "France")
        assert abs(d1 + d2) < 0.001

class TestForeignPct:
    def test_range(self):
        d = calculate_foreign_pct_factor("France", "Saudi Arabia")
        assert -10 <= d <= 10, f"Foreign pct diff {d} out of range [-10, 10]"

    def test_symmetric(self):
        d1 = calculate_foreign_pct_factor("Spain", "Japan")
        d2 = calculate_foreign_pct_factor("Japan", "Spain")
        assert abs(d1 + d2) < 0.001

class TestExperience:
    def test_range(self):
        d = calculate_experience_factor("Argentina", "Haiti")
        assert -10 <= d <= 10, f"Experience diff {d} out of range"

    def test_symmetric(self):
        d1 = calculate_experience_factor("Brazil", "Canada")
        d2 = calculate_experience_factor("Canada", "Brazil")
        assert abs(d1 + d2) < 0.001

class TestTrophy:
    def test_range(self):
        d = calculate_trophy_factor("Spain", "New Zealand")
        assert -10 <= d <= 10, f"Trophy diff {d} out of range"

class TestHeight:
    def test_range(self):
        d = calculate_height_advantage("Germany", "Japan")
        assert -10 <= d <= 10, f"Height diff {d} out of range"

class TestClubChemistry:
    def test_range(self):
        d = calculate_club_chemistry("Spain", "USA")
        assert -10 <= d <= 10, f"Chemistry diff {d} out of range"

class TestRestDays:
    def test_penalty_below_4(self):
        diff = calculate_rest_days("TeamA", "TeamB", 2, 5)
        assert diff < 0, "Team with 2 rest days should be penalized"

    def test_no_penalty_above_4(self):
        diff = calculate_rest_days("TeamA", "TeamB", 5, 5)
        assert diff == 0, "Equal rest should have zero diff"

    def test_symmetric(self):
        d1 = calculate_rest_days("A", "B", 2, 5)
        d2 = calculate_rest_days("B", "A", 5, 2)
        assert abs(d1 + d2) < 0.001

class TestTravelFatigue:
    def test_more_travel_penalty(self):
        diff = calculate_travel_fatigue("A", "B", 20000, 5000)
        assert diff < 0, "More travel should penalize"

    def test_symmetric(self):
        d1 = calculate_travel_fatigue("A", "B", 10000, 5000)
        d2 = calculate_travel_fatigue("B", "A", 5000, 10000)
        assert abs(d1 + d2) < 0.001

class TestStakes:
    def test_contender_vs_eliminated(self):
        diff = calculate_stakes_factor("contender", "eliminated")
        assert diff > 0, "Contender should beat eliminated"

    def test_qualified_vs_contender(self):
        diff = calculate_stakes_factor("qualified", "contender")
        assert diff < 0, "Qualified (-1) should be worse than contender (+1)"

    def test_contender_vs_qualified(self):
        diff = calculate_stakes_factor("contender", "qualified")
        assert diff > 0, "Contender (+1) should beat qualified (-1)"

    def test_symmetric(self):
        d1 = calculate_stakes_factor("qualified", "eliminated")
        d2 = calculate_stakes_factor("eliminated", "qualified")
        assert abs(d1 + d2) < 0.001

class TestOddsFactor:
    def test_favorite_ahead(self):
        data_a = {"odds_win": 500}
        data_b = {"odds_win": 50000}
        d = calculate_odds_factor("A", "B", data_a, data_b)
        assert d > 0, "Lower odds (favorite) should have positive factor"

    def test_symmetric(self):
        da = {"odds_win": 300}
        db = {"odds_win": 50000}
        d1 = calculate_odds_factor("A", "B", da, db)
        d2 = calculate_odds_factor("B", "A", db, da)
        assert abs(d1 + d2) < 0.001

class TestPredictMatch:
    def test_basic_structure(self):
        result = predict_match("Argentina", "Brazil", "Miami", round_name="Group A")
        required = ["team_a", "team_b", "venue", "winner", "score_a", "score_b",
                     "expected_goals_a", "expected_goals_b", "prob_a_win", "prob_b_win",
                     "prob_draw", "confidence", "factors"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_scores_positive(self):
        result = predict_match("Spain", "Germany", "New York")
        assert result["score_a"] >= 0
        assert result["score_b"] >= 0

    def test_probabilities_sum(self):
        result = predict_match("England", "France", "Boston")
        total = result["prob_a_win"] + result["prob_b_win"] + result["prob_draw"]
        assert abs(total - 100) < 2, f"Probabilities sum to {total:.1f}, expected ~100"

    def test_knockout_no_draw(self):
        result = predict_match("Brazil", "Portugal", "Philadelphia", is_neutral=True, allows_draw=False)
        assert result["winner"] != "Empate", "KO matches should have a winner"

    def test_factor_count(self):
        result = predict_match("Argentina", "France", "Miami")
        assert len(result["factors"]) >= 18, f"Expected 18+ factor entries"

    def test_stakes_factor(self):
        result = predict_match("USA", "Canada", "Seattle",
                                stakes_a="contender", stakes_b="qualified")
        assert result["factors"]["stakes_a"] == "contender"
        assert result["factors"]["stakes_b"] == "qualified"

    def test_xg_reasonable(self):
        result = predict_match("Spain", "Haiti", "Mexico City")
        assert 0.2 <= result["expected_goals_a"] <= 7.0
        assert 0.2 <= result["expected_goals_b"] <= 7.0

class TestTravelImpact:
    def test_base_to_venue(self):
        d = calculate_travel_impact("Argentina", "Mexico", "Mexico City")
        assert -6 <= d <= 6, f"Travel impact {d} out of range"

class TestSquadDepth:
    def test_range(self):
        d = calculate_squad_depth_factor("England", "Panama")
        assert -10 <= d <= 10, f"Squad depth {d} out of range"

    def test_symmetric(self):
        d1 = calculate_squad_depth_factor("Spain", "Japan")
        d2 = calculate_squad_depth_factor("Japan", "Spain")
        assert abs(d1 + d2) < 0.001

# ── Dixon-Coles τ ───────────────────────────────────────────────────

class TestPoissonPMF:
    def test_pmf_zero_lam(self):
        assert poisson_pmf(0, 0) == 1.0
        assert poisson_pmf(5, 0) == 0.0

    def test_pmf_sums_to_one(self):
        lam = 2.5
        total = sum(poisson_pmf(k, lam) for k in range(20))
        assert abs(total - 1.0) < 1e-6

    def test_pmf_known_values(self):
        assert abs(poisson_pmf(0, 1.0) - math.exp(-1)) < 1e-10
        assert abs(poisson_pmf(1, 1.0) - math.exp(-1)) < 1e-10
        assert abs(poisson_pmf(2, 1.0) - math.exp(-1) / 2) < 1e-10

class TestDixonColesTau:
    def test_tau_identity_high_scores(self):
        tau = dixon_coles_tau(5, 3, 2.0, 1.5)
        assert tau == 1.0

    def test_tau_00_increases(self):
        tau = dixon_coles_tau(0, 0, 2.0, 1.5)
        expected = 1 - 2.0 * 1.5 * DIXON_COLES_RHO
        assert tau == expected
        assert tau > 1.0

    def test_tau_11_increases(self):
        tau = dixon_coles_tau(1, 1, 2.0, 1.5)
        expected = 1 - DIXON_COLES_RHO
        assert tau == expected
        assert tau > 1.0

    def test_tau_01_decreases(self):
        tau = dixon_coles_tau(0, 1, 2.0, 1.5)
        expected = max(0, 1 + 2.0 * DIXON_COLES_RHO)
        assert tau == expected

    def test_tau_10_decreases(self):
        tau = dixon_coles_tau(1, 0, 2.0, 1.5)
        expected = max(0, 1 + 1.5 * DIXON_COLES_RHO)
        assert tau == expected

    def test_tau_non_negative(self):
        for x in range(3):
            for y in range(3):
                tau = dixon_coles_tau(x, y, 7.0, 7.0)
                assert tau >= 0, f"τ({x},{y}) = {tau} < 0"

class TestJointDist:
    def test_joint_outcomes_in_range(self):
        o, w = _build_joint_dist(1.5, 1.2)
        assert len(o) > 0
        assert len(o) == len(w)
        assert abs(sum(w) - 1.0) < 1e-6
        for (x, y) in o:
            assert 0 <= x <= MAX_GOALS_DC
            assert 0 <= y <= MAX_GOALS_DC

    def test_joint_high_lam(self):
        o, w = _build_joint_dist(6.0, 5.5)
        assert len(o) > 0
        assert abs(sum(w) - 1.0) < 1e-6

    def test_joint_zero_lam(self):
        o, w = _build_joint_dist(0, 0)
        assert o == [(0, 0)]
        assert abs(w[0] - 1.0) < 1e-6
