# -*- coding: utf-8 -*-
# Motor de prediccion con factores ponderados

import json
import math
import os
import random
from data import (get_team, get_venue, CITY_COORDS, BASE_CAMPS,
                  VENUE_TIMEZONES, HOME_TIMEZONES, SQUAD_DEPTH, haversine)

PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "output", "players.json")
_PLAYERS_CACHE = None

# Pesos de cada factor (suman 100%, randomness es aditivo)
WEIGHTS = {
    "team_strength": 0.18,
    "market_value": 0.11,
    "player_stats": 0.11,
    "odds": 0.05,
    "home_advantage": 0.08,
    "climate": 0.06,
    "travel": 0.03,
    "history": 0.04,
    "morale": 0.04,
    "age_penalty": 0.03,
    "foreign_pct": 0.05,
    "rest_days": 0.07,
    "squad_depth": 0.07,
    "travel_fatigue": 0.05,
    "jet_lag": 0.03,
}

_NORM_MAX = {
    "strength": 88,
    "home": 40,
    "climate": 25,
    "history": 20,
    "morale": 15,
    "age": 8,
    "odds": 1.0,
}

def _american_to_prob(odds):
    if odds < 0:
        return -odds / (-odds + 100)
    return 100 / (odds + 100)

def calculate_odds_factor(team_a, team_b, team_a_data, team_b_data):
    prob_a = _american_to_prob(team_a_data.get("odds_win", 10000))
    prob_b = _american_to_prob(team_b_data.get("odds_win", 10000))
    return max(-10, min(10, (prob_a - prob_b) * 10))

def _norm(value, theoretical_max):
    if theoretical_max <= 0:
        return 0.0
    return max(-10.0, min(10.0, value / theoretical_max * 10.0))

def _load_players():
    global _PLAYERS_CACHE
    if _PLAYERS_CACHE is not None:
        return _PLAYERS_CACHE
    if not os.path.exists(PLAYERS_FILE):
        _PLAYERS_CACHE = {}
        return _PLAYERS_CACHE
    with open(PLAYERS_FILE, encoding="utf-8") as f:
        _PLAYERS_CACHE = json.load(f)
    return _PLAYERS_CACHE

def calculate_team_strength(team_name):
    team = get_team(team_name)
    return calculate_team_strength_from_data(team)

def calculate_team_strength_from_data(team_data):

    rank_score = max(0, 100 - team_data["rank"]) * 0.6
    tier_score = (8 - team_data["tier"]) * 10 * 0.4
    return rank_score + tier_score



def calculate_player_stats_factor(team_a, team_b):
    from data import INJURED_OUT
    players = _load_players()
    if not players:
        return 0

    def _filtered_squad(team_name):
        squad = players.get(team_name, [])
        injured = INJURED_OUT.get(team_name, [])
        return [p for p in squad if p.get("name", "") not in injured]

    def team_avg_goals(team_name):
        squad = _filtered_squad(team_name)
        if not squad:
            return 0
        total_goals = sum(p.get("goals_2026", 0) for p in squad)
        return total_goals / len(squad)

    def team_avg_assists(team_name):
        squad = _filtered_squad(team_name)
        if not squad:
            return 0
        total_assists = sum(p.get("assists_2026", 0) for p in squad)
        return total_assists / len(squad)

    ga = team_avg_goals(team_a) + team_avg_assists(team_a) * 0.5
    gb = team_avg_goals(team_b) + team_avg_assists(team_b) * 0.5
    diff = ga - gb
    return max(-10, min(10, diff))

def calculate_home_advantage(team_a, team_b, venue_country, is_neutral=False,
                             team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    advantage_a = 0
    advantage_b = 0

    if team_a_data["confederation"] == "CONCACAF" and venue_country in ("USA", "Mexico", "Canada"):
        advantage_a += 8
    if team_b_data["confederation"] == "CONCACAF" and venue_country in ("USA", "Mexico", "Canada"):
        advantage_b += 8

    mexico_bonus_home = 20
    mexico_bonus_away = 5 if is_neutral else 10
    if team_a == "Mexico" and venue_country == "Mexico":
        advantage_a += mexico_bonus_home
    elif team_a == "Mexico":
        advantage_a += mexico_bonus_away
    if team_b == "Mexico" and venue_country == "Mexico":
        advantage_b += mexico_bonus_home
    elif team_b == "Mexico":
        advantage_b += mexico_bonus_away

    usa_bonus_home = 15
    usa_bonus_away = 4 if is_neutral else 8
    if team_a == "USA" and venue_country == "USA":
        advantage_a += usa_bonus_home
    elif team_a == "USA":
        advantage_a += usa_bonus_away
    if team_b == "USA" and venue_country == "USA":
        advantage_b += usa_bonus_home
    elif team_b == "USA":
        advantage_b += usa_bonus_away

    canada_bonus_home = 15
    canada_bonus_away = 2 if is_neutral else 5
    if team_a == "Canada" and venue_country == "Canada":
        advantage_a += canada_bonus_home
    elif team_a == "Canada":
        advantage_a += canada_bonus_away
    if team_b == "Canada" and venue_country == "Canada":
        advantage_b += canada_bonus_home
    elif team_b == "Canada":
        advantage_b += canada_bonus_away

    diaspora_a = team_a_data.get("diaspora_in_usa", 0)
    diaspora_b = team_b_data.get("diaspora_in_usa", 0)
    if venue_country == "USA":
        if diaspora_a > 1000000:
            advantage_a += 5
        elif diaspora_a > 500000:
            advantage_a += 3
        elif diaspora_a > 100000:
            advantage_a += 1
        if diaspora_b > 1000000:
            advantage_b += 5
        elif diaspora_b > 500000:
            advantage_b += 3
        elif diaspora_b > 100000:
            advantage_b += 1

    coi = [t for t in ("Argentina", "Brazil", "Colombia", "Ecuador", "Peru", "Paraguay", "Uruguay")]
    if team_a in coi and venue_country == "USA":
        advantage_a += 4
    if team_b in coi and venue_country == "USA":
        advantage_b += 4

    return advantage_a - advantage_b

def calculate_climate_impact(team_a, team_b, venue_name,
                             team_a_data=None, team_b_data=None):
    venue = get_venue(venue_name)
    venue_temp = venue["avg_temp"]
    venue_altitude = venue["altitude"]
    has_roof = venue["roof"]

    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)

    climate_a = 0
    climate_b = 0

    if not has_roof:
        temp_diff_a = venue_temp - team_a_data["avg_temp_home"]
        temp_diff_b = venue_temp - team_b_data["avg_temp_home"]

        if temp_diff_a > 15:
            climate_a -= 8
        elif temp_diff_a > 10:
            climate_a -= 5
        elif temp_diff_a > 5:
            climate_a -= 2
        elif temp_diff_a < -10:
            climate_a -= 3
        else:
            climate_a += 1

        if temp_diff_b > 15:
            climate_b -= 8
        elif temp_diff_b > 10:
            climate_b -= 5
        elif temp_diff_b > 5:
            climate_b -= 2
        elif temp_diff_b < -10:
            climate_b -= 3
        else:
            climate_b += 1

    if not has_roof and venue_altitude > 1500:
        alt_penalty = venue_altitude / 1000
        if team_a_data["altitude_home"] < 500:
            climate_a -= alt_penalty * 3
        elif team_a_data["altitude_home"] < 1000:
            climate_a -= alt_penalty * 1.5
        if team_b_data["altitude_home"] < 500:
            climate_b -= alt_penalty * 3
        elif team_b_data["altitude_home"] < 1000:
            climate_b -= alt_penalty * 1.5

    if has_roof:
        climate_a += 2
        climate_b += 2

    return climate_a - climate_b

def _base_to_venue_dist(team, venue_name):
    base = BASE_CAMPS.get(team, "Dallas")
    base_coords = CITY_COORDS.get(base)
    venue_coords = CITY_COORDS.get(venue_name)
    if not base_coords or not venue_coords:
        return 0
    return haversine(base_coords[0], base_coords[1], venue_coords[0], venue_coords[1])

def calculate_travel_impact(team_a, team_b, venue_name):
    da = _base_to_venue_dist(team_a, venue_name)
    db = _base_to_venue_dist(team_b, venue_name)
    diff = (db - da) / 1000
    return max(-6, min(6, diff))

def calculate_history_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)

    history_scores = {
        "campeon": 20, "final": 15, "semifinal": 12, "cuartos": 8,
        "octavos": 5, "fase_grupos": 2, "debut": 0,
    }

    def get_history_score(wc_str):
        if not wc_str:
            return 0
        best = 0
        for key, val in history_scores.items():
            if key in wc_str and val > best:
                best = val
        if "debut" in wc_str:
            best = 0
        return best

    score_a = get_history_score(team_a_data["wc_history"])
    score_b = get_history_score(team_b_data["wc_history"])
    return score_a - score_b

def calculate_morale(team_a, team_b, team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    morale_a = team_a_data["form_streak"] * 15
    morale_b = team_b_data["form_streak"] * 15
    return morale_a - morale_b

def calculate_market_value_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("market_value_total", 0)
    b = team_b_data.get("market_value_total", 0)
    # Log scale: difference in market value (capped)
    diff = (min(a, 500) - min(b, 500)) / 50  # 50M = 1pt diff, max ~10pt
    return max(-10, min(10, diff))

def calculate_foreign_pct_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("foreign_pct", 0.8)
    b = team_b_data.get("foreign_pct", 0.8)
    return (a - b) * 10

def calculate_age_penalty_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    optimal = 27
    a = team_a_data.get("avg_age", 27)
    b = team_b_data.get("avg_age", 27)
    penalty_a = abs(a - optimal) * 0.5
    penalty_b = abs(b - optimal) * 0.5
    return penalty_b - penalty_a  # positive = a has advantage

def calculate_rest_days(team_a, team_b, rest_a=None, rest_b=None):
    ra = rest_a if rest_a is not None else 5
    rb = rest_b if rest_b is not None else 5
    penalty_a = max(0, (4 - ra)) * 3
    penalty_b = max(0, (4 - rb)) * 3
    return max(-10, min(10, penalty_b - penalty_a))

def calculate_travel_fatigue(team_a, team_b, travel_km_a=0, travel_km_b=0):
    fa = min(travel_km_a, 30000) / 3000
    fb = min(travel_km_b, 30000) / 3000
    return max(-10, min(10, fb - fa))

def calculate_squad_depth_factor(team_a, team_b):
    a = SQUAD_DEPTH.get(team_a, 3)
    b = SQUAD_DEPTH.get(team_b, 3)
    return max(-10, min(10, (a - b) * 2))

def calculate_jet_lag(team_a, team_b, venue_name):
    venue_offset = VENUE_TIMEZONES.get(venue_name, -5)
    tz_a = HOME_TIMEZONES.get(team_a, venue_offset)
    tz_b = HOME_TIMEZONES.get(team_b, venue_offset)
    diff_a = abs(tz_a - venue_offset) * 0.7
    diff_b = abs(tz_b - venue_offset) * 0.7
    return max(-5, min(5, diff_b - diff_a))

def simulate_match_cards(team_a_data, team_b_data):
    yc_a = poisson_sample(team_a_data.get("yellow_rate", 2.0))
    yc_b = poisson_sample(team_b_data.get("yellow_rate", 2.0))
    rc_a = 1 if random.random() < team_a_data.get("red_rate", 0.05) else 0
    rc_b = 1 if random.random() < team_b_data.get("red_rate", 0.05) else 0

    def fp_loss(yellows, reds):
        loss = yellows * (-1)
        if reds == 1:
            loss += -4
        return loss

    return fp_loss(yc_a, rc_a), fp_loss(yc_b, rc_b), yc_a, yc_b, rc_a, rc_b


def predict_match(team_a, team_b, venue_name, is_neutral=False, allows_draw=None, round_name="Group Stage",
                  rest_days_a=None, rest_days_b=None, travel_km_a=0, travel_km_b=0, skip_sims=False):
    venue = get_venue(venue_name)
    venue_country = venue["country"]

    team_a_data = get_team(team_a)
    team_b_data = get_team(team_b)

    if allows_draw is None:
        allows_draw = not is_neutral

    strength_diff = _norm(
        calculate_team_strength_from_data(team_a_data) -
        calculate_team_strength_from_data(team_b_data),
        _NORM_MAX["strength"]
    ) * WEIGHTS["team_strength"]

    mv_diff = calculate_market_value_factor(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["market_value"]
    ps_diff = calculate_player_stats_factor(team_a, team_b) * WEIGHTS["player_stats"]
    odds_diff = _norm(
        calculate_odds_factor(team_a, team_b, team_a_data, team_b_data),
        _NORM_MAX["odds"]
    ) * WEIGHTS["odds"]
    home_diff = _norm(
        calculate_home_advantage(team_a, team_b, venue_country, is_neutral, team_a_data, team_b_data),
        _NORM_MAX["home"]
    ) * WEIGHTS["home_advantage"]
    climate_diff = _norm(
        calculate_climate_impact(team_a, team_b, venue_name, team_a_data, team_b_data),
        _NORM_MAX["climate"]
    ) * WEIGHTS["climate"]
    travel_diff = calculate_travel_impact(team_a, team_b, venue_name) * WEIGHTS["travel"]
    history_diff = _norm(
        calculate_history_factor(team_a, team_b, team_a_data, team_b_data),
        _NORM_MAX["history"]
    ) * WEIGHTS["history"]
    morale_diff = _norm(
        calculate_morale(team_a, team_b, team_a_data, team_b_data),
        _NORM_MAX["morale"]
    ) * WEIGHTS["morale"]
    foreign_diff = calculate_foreign_pct_factor(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["foreign_pct"]
    age_diff = _norm(
        calculate_age_penalty_factor(team_a, team_b, team_a_data, team_b_data),
        _NORM_MAX["age"]
    ) * WEIGHTS["age_penalty"]
    rest_diff = calculate_rest_days(team_a, team_b, rest_days_a, rest_days_b) * WEIGHTS["rest_days"]
    depth_diff = calculate_squad_depth_factor(team_a, team_b) * WEIGHTS["squad_depth"]
    fatigue_diff = calculate_travel_fatigue(team_a, team_b, travel_km_a, travel_km_b) * WEIGHTS["travel_fatigue"]
    jet_diff = calculate_jet_lag(team_a, team_b, venue_name) * WEIGHTS["jet_lag"]

    total_diff = (strength_diff + mv_diff + ps_diff + odds_diff + home_diff + climate_diff +
                  travel_diff + history_diff + morale_diff + foreign_diff + age_diff +
                  rest_diff + depth_diff + fatigue_diff + jet_diff)

    deterministic_scaled = total_diff / 25

    base_a = (team_a_data["goals_scored_avg"] + team_b_data["goals_conceded_avg"]) / 2
    base_b = (team_b_data["goals_scored_avg"] + team_a_data["goals_conceded_avg"]) / 2

    det_goals_a = max(0.2, min(7.0, base_a * (1 + deterministic_scaled)))
    det_goals_b = max(0.2, min(7.0, base_b * (1 - deterministic_scaled)))

    if skip_sims:
        score_a = poisson_sample(det_goals_a)
        score_b = poisson_sample(det_goals_b)
        prob_a_win = prob_b_win = prob_draw = 0.0
    else:
        score_a = round(det_goals_a)
        score_b = round(det_goals_b)
        sims = 1000
        wins_a = 0
        wins_b = 0
        draws = 0
        for _ in range(sims):
            g_a = poisson_sample(det_goals_a)
            g_b = poisson_sample(det_goals_b)
            if g_a > g_b:
                wins_a += 1
            elif g_b > g_a:
                wins_b += 1
            else:
                draws += 1
        prob_a_win = wins_a / sims
        prob_b_win = wins_b / sims
        prob_draw = draws / sims

    if score_a > score_b:
        winner = team_a
        loser = team_b
        result_type = "local"
        confidence = prob_a_win * 100
    elif score_b > score_a:
        winner = team_b
        loser = team_a
        result_type = "visitante"
        confidence = prob_b_win * 100
    elif not allows_draw:
        tiebreaker = (morale_diff + depth_diff + random.gauss(0, 1))
        if tiebreaker >= 0:
            winner = team_a
            loser = team_b
        else:
            winner = team_b
            loser = team_a
        result_type = "penales"
        confidence = max(prob_a_win, prob_b_win) * 100
    else:
        winner = "Empate"
        loser = ""
        result_type = "empate"
        confidence = prob_draw * 100

    factors_detail = {
        "strength": round(strength_diff, 1),
        "market_value": round(mv_diff, 1),
        "player_stats": round(ps_diff, 1),
        "odds": round(odds_diff, 1),
        "home": round(home_diff, 1),
        "climate": round(climate_diff, 1),
        "travel": round(travel_diff, 1),
        "history": round(history_diff, 1),
        "morale": round(morale_diff, 1),
        "foreign_pct": round(foreign_diff, 1),
        "age_penalty": round(age_diff, 1),
        "rest_days": round(rest_diff, 1),
        "squad_depth": round(depth_diff, 1),
        "travel_fatigue": round(fatigue_diff, 1),
        "jet_lag": round(jet_diff, 1),
    }

    fp_delta_a = fp_delta_b = yc_a = yc_b = rc_a = rc_b = 0
    if not skip_sims:
        fp_delta_a, fp_delta_b, yc_a, yc_b, rc_a, rc_b = simulate_match_cards(team_a_data, team_b_data)

    return {
        "team_a": team_a,
        "team_b": team_b,
        "venue": venue_name,
        "venue_country": venue_country,
        "round": round_name,
        "winner": winner,
        "loser": loser,
        "result_type": result_type,
        "score_a": score_a,
        "score_b": score_b,
        "expected_goals_a": round(det_goals_a, 2),
        "expected_goals_b": round(det_goals_b, 2),
        "prob_a_win": round(prob_a_win * 100, 1),
        "prob_b_win": round(prob_b_win * 100, 1),
        "prob_draw": round(prob_draw * 100, 1),
        "confidence": round(confidence, 1),
        "fp_delta_a": fp_delta_a,
        "fp_delta_b": fp_delta_b,
        "yc_a": yc_a,
        "yc_b": yc_b,
        "rc_a": rc_a,
        "rc_b": rc_b,
        "factors": factors_detail,
    }

def poisson_sample(lambda_val):
    L = math.exp(-lambda_val)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1
