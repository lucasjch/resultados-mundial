# -*- coding: utf-8 -*-
# Motor de prediccion con factores ponderados

import math
import random
from data import get_team, get_venue, CITY_COORDS, BASE_CAMPS

# Pesos de cada factor
WEIGHTS = {
    "team_strength": 0.30,
    "market_value": 0.15,
    "home_advantage": 0.12,
    "climate": 0.10,
    "travel": 0.08,
    "history": 0.06,
    "morale": 0.06,
    "foreign_pct": 0.04,
    "age_penalty": 0.04,
    "fanbase": 0.05,
    "randomness": 0.10,
}

def calculate_team_strength(team_name):
    team = get_team(team_name)
    rank_score = max(0, 100 - team["rank"]) * 0.3
    # Replace odds_score with market_value_score
    mv_total = team.get("market_value_total", 0)
    market_value_score = min(20, mv_total / 12.5) * 0.25  # 12.5M = 1pt, 250M = 20pt
    tier_score = (8 - team["tier"]) * 10 * 0.20
    form_score = team["form_streak"] * 100 * 0.15
    goals_score = (team["goals_scored_avg"] - team["goals_conceded_avg"] + 2) * 10 * 0.10
    return rank_score + market_value_score + tier_score + form_score + goals_score

def calculate_home_advantage(team_a, team_b, venue_country):
    team_a_data = get_team(team_a)
    team_b_data = get_team(team_b)
    advantage_a = 0
    advantage_b = 0

    if team_a_data["home_continent"] and venue_country == team_a_data.get("confederation", "").replace("CONCACAF", "USA"):
        pass

    if team_a_data["confederation"] == "CONCACAF" and venue_country in ("USA", "Mexico", "Canada"):
        advantage_a += 8
    if team_b_data["confederation"] == "CONCACAF" and venue_country in ("USA", "Mexico", "Canada"):
        advantage_b += 8

    if team_a == "Mexico" and venue_country == "Mexico":
        advantage_a += 20
    elif team_a == "Mexico":
        advantage_a += 10
    if team_b == "Mexico" and venue_country == "Mexico":
        advantage_b += 20
    elif team_b == "Mexico":
        advantage_b += 10

    if team_a == "USA" and venue_country == "USA":
        advantage_a += 15
    elif team_a == "USA":
        advantage_a += 8
    if team_b == "USA" and venue_country == "USA":
        advantage_b += 15
    elif team_b == "USA":
        advantage_b += 8

    if team_a == "Canada" and venue_country == "Canada":
        advantage_a += 15
    elif team_a == "Canada":
        advantage_a += 5
    if team_b == "Canada" and venue_country == "Canada":
        advantage_b += 15
    elif team_b == "Canada":
        advantage_b += 5

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

def calculate_climate_impact(team_a, team_b, venue_name):
    venue = get_venue(venue_name)
    venue_temp = venue["avg_temp"]
    venue_altitude = venue["altitude"]
    has_roof = venue["roof"]

    team_a_data = get_team(team_a)
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

def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _base_to_venue_dist(team, venue_name):
    """Distance from team's base camp to match venue (km)."""
    base = BASE_CAMPS.get(team, "Dallas")
    base_coords = CITY_COORDS.get(base)
    venue_coords = CITY_COORDS.get(venue_name)
    if not base_coords or not venue_coords:
        return 0
    return _haversine(base_coords[0], base_coords[1], venue_coords[0], venue_coords[1])

def calculate_travel_impact(team_a, team_b, venue_name):
    da = _base_to_venue_dist(team_a, venue_name)
    db = _base_to_venue_dist(team_b, venue_name)
    diff = (db - da) / 1000
    return max(-6, min(6, diff))

def calculate_history_factor(team_a, team_b):
    team_a_data = get_team(team_a)
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

def calculate_morale(team_a, team_b):
    team_a_data = get_team(team_a)
    team_b_data = get_team(team_b)
    morale_a = team_a_data["form_streak"] * 15
    morale_b = team_b_data["form_streak"] * 15
    return morale_a - morale_b

def calculate_market_value_factor(team_a, team_b):
    a = get_team(team_a).get("market_value_total", 0)
    b = get_team(team_b).get("market_value_total", 0)
    # Log scale: difference in market value (capped)
    diff = (min(a, 500) - min(b, 500)) / 50  # 50M = 1pt diff, max ~10pt
    return max(-10, min(10, diff))

def calculate_foreign_pct_factor(team_a, team_b):
    a = get_team(team_a).get("foreign_pct", 0.8)
    b = get_team(team_b).get("foreign_pct", 0.8)
    return (a - b) * 10

def calculate_age_penalty_factor(team_a, team_b):
    optimal = 27
    a = get_team(team_a).get("avg_age", 27)
    b = get_team(team_b).get("avg_age", 27)
    penalty_a = abs(a - optimal) * 0.5
    penalty_b = abs(b - optimal) * 0.5
    return penalty_b - penalty_a  # positive = a has advantage

def calculate_fanbase_factor(team_a, team_b):
    a = get_team(team_a).get("global_fanbase", 2)
    b = get_team(team_b).get("global_fanbase", 2)
    return (a - b) * 1.5

def predict_match(team_a, team_b, venue_name, is_neutral=False, round_name="Group Stage"):
    venue = get_venue(venue_name)
    venue_country = venue["country"]

    strength_a = calculate_team_strength(team_a)
    strength_b = calculate_team_strength(team_b)
    strength_diff = (strength_a - strength_b) * WEIGHTS["team_strength"]

    mv_diff = calculate_market_value_factor(team_a, team_b) * WEIGHTS["market_value"]

    home_diff = calculate_home_advantage(team_a, team_b, venue_country) * WEIGHTS["home_advantage"]

    climate_diff = calculate_climate_impact(team_a, team_b, venue_name) * WEIGHTS["climate"]

    travel_diff = calculate_travel_impact(team_a, team_b, venue_name) * WEIGHTS["travel"]

    history_diff = calculate_history_factor(team_a, team_b) * WEIGHTS["history"]

    morale_diff = calculate_morale(team_a, team_b) * WEIGHTS["morale"]

    foreign_diff = calculate_foreign_pct_factor(team_a, team_b) * WEIGHTS["foreign_pct"]

    age_diff = calculate_age_penalty_factor(team_a, team_b) * WEIGHTS["age_penalty"]

    fan_diff = calculate_fanbase_factor(team_a, team_b) * WEIGHTS["fanbase"]

    random_factor = random.gauss(0, 7) * WEIGHTS["randomness"]

    total_diff = (strength_diff + mv_diff + home_diff + climate_diff +
                  travel_diff + history_diff + morale_diff + foreign_diff +
                  age_diff + fan_diff + random_factor)

    total_diff = max(-30, min(30, total_diff))

    team_a_data = get_team(team_a)
    team_b_data = get_team(team_b)

    expected_goals_a = team_a_data["goals_scored_avg"] + (total_diff / 30) * 1.2
    expected_goals_b = team_b_data["goals_conceded_avg"] - (total_diff / 30) * 0.8

    expected_goals_a = max(0.2, min(4.5, expected_goals_a))
    expected_goals_b = max(0.1, min(4.0, expected_goals_b))

    sims = 1000
    wins_a = 0
    wins_b = 0
    draws = 0
    goals_a_dist = []
    goals_b_dist = []

    for _ in range(sims):
        g_a = poisson_sample(expected_goals_a)
        g_b = poisson_sample(expected_goals_b)
        goals_a_dist.append(g_a)
        goals_b_dist.append(g_b)
        if g_a > g_b:
            wins_a += 1
        elif g_b > g_a:
            wins_b += 1
        else:
            draws += 1

    prob_a_win = wins_a / sims
    prob_b_win = wins_b / sims
    prob_draw = draws / sims

    most_likely_goals_a = max(set(goals_a_dist), key=goals_a_dist.count)
    most_likely_goals_b = max(set(goals_b_dist), key=goals_b_dist.count)

    dominant = max(prob_a_win, prob_b_win, prob_draw)
    confidence = dominant * 100

    if prob_a_win > prob_b_win and prob_a_win > prob_draw:
        winner = team_a
        loser = team_b
        result_type = "local"
    elif prob_b_win > prob_a_win and prob_b_win > prob_draw:
        winner = team_b
        loser = team_a
        result_type = "visitante"
    else:
        winner = "Empate"
        loser = ""
        result_type = "empate"

    factors_detail = {
        "strength": round(strength_diff, 1),
        "market_value": round(mv_diff, 1),
        "home": round(home_diff, 1),
        "climate": round(climate_diff, 1),
        "travel": round(travel_diff, 1),
        "history": round(history_diff, 1),
        "morale": round(morale_diff, 1),
        "foreign_pct": round(foreign_diff, 1),
        "age_penalty": round(age_diff, 1),
        "fanbase": round(fan_diff, 1),
        "random": round(random_factor, 1),
    }

    return {
        "team_a": team_a,
        "team_b": team_b,
        "venue": venue_name,
        "venue_country": venue_country,
        "round": round_name,
        "winner": winner,
        "loser": loser,
        "result_type": result_type,
        "score_a": most_likely_goals_a,
        "score_b": most_likely_goals_b,
        "expected_goals_a": round(expected_goals_a, 2),
        "expected_goals_b": round(expected_goals_b, 2),
        "prob_a_win": round(prob_a_win * 100, 1),
        "prob_b_win": round(prob_b_win * 100, 1),
        "prob_draw": round(prob_draw * 100, 1),
        "confidence": round(confidence, 1),
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
