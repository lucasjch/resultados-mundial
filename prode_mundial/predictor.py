# -*- coding: utf-8 -*-
"""Motor de prediccion: 18 factores ponderados + Poisson (1500 sims) + Dixon-Coles tau.

Funciones principales:
    predict_match()      - Predice un partido completo con scores y factores.
    calculate_team_strength() - Evalua fortaleza del equipo basado en ranking FIFA y tier.
"""
# Motor de prediccion con factores ponderados
# Incluye correccion Dixon-Coles τ para bajos puntajes

import json
import math
import os
import random
from prode_mundial.data import (get_team, get_venue, CITY_COORDS, BASE_CAMPS, haversine)
from prode_mundial.friendlies_data import compute_friendly_form

PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "output", "players.json")
_PLAYERS_CACHE = None

DIXON_COLES_RHO = -0.15
MAX_GOALS_DC = 15

# Pesos de cada factor (suman 100%)
WEIGHTS = {
    "team_strength": 0.15,
    "player_stats": 0.11,
    "market_value": 0.10,
    "experience": 0.06,
    "home_advantage": 0.06,
    "rest_days": 0.06,
    "squad_depth": 0.06,
    "climate": 0.05,
    "foreign_pct": 0.03,
    "travel_fatigue": 0.04,
    "history": 0.04,
    "morale": 0.02,
    "friendly_form": 0.02,
    "trophy_pedigree": 0.04,
    "odds": 0.03,
    "height_advantage": 0.03,
    "club_chemistry": 0.03,
    "travel": 0.03,
    "stakes": 0.04,
}

_NORM_MAX = {
    "strength": 88,
    "home": 40,
    "climate": 25,
    "history": 20,
    "morale": 15,
    "odds": 1.0,
}

def _american_to_prob(odds):
    """Convierte cuotas americanas a probabilidad decimal."""
    if odds < 0:
        return -odds / (-odds + 100)
    return 100 / (odds + 100)

def calculate_odds_factor(team_a, team_b, team_a_data, team_b_data):
    """Diferencia de cuotas DraftKings entre dos equipos."""
    prob_a = _american_to_prob(team_a_data.get("odds_win", 10000))
    prob_b = _american_to_prob(team_b_data.get("odds_win", 10000))
    return max(-10, min(10, (prob_a - prob_b) * 10))

def _norm(value, theoretical_max):
    """Normaliza un valor al rango [-10, 10] dividiendo por su maximo teorico."""
    if theoretical_max <= 0:
        return 0.0
    return max(-10.0, min(10.0, value / theoretical_max * 10.0))

def _load_players():
    """Carga lazy el JSON de jugadores desde players.json."""
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
    """Evalua fortaleza del equipo basado en ranking FIFA y tier."""
    team = get_team(team_name)
    return calculate_team_strength_from_data(team)

def calculate_team_strength_from_data(team_data):
    """Calcula fortaleza desde un dict de datos de equipo."""
    rank_score = max(0, 100 - team_data["rank"]) * 0.6
    tier_score = (8 - team_data["tier"]) * 10 * 0.4
    return rank_score + tier_score



def calculate_player_stats_factor(team_a, team_b):
    """Diferencia de rendimiento individual (goles+asistencias) entre plantillas."""
    from prode_mundial.data import INJURED_OUT
    players = _load_players()
    if not players:
        return 0

    def _filtered_squad(team_name):
        squad = players.get(team_name, [])
        injured = INJURED_OUT.get(team_name, [])
        return [p for p in squad if p.get("name", "") not in injured]

    def team_weighted_avg(team_name):
        squad = _filtered_squad(team_name)
        if not squad:
            return 0
        total_weight = 0
        total_val = 0
        for p in squad:
            mins = p.get("minutes_2026", 0) or 0
            w = min(mins, 3000) / 3000
            w = max(w, 0.2)
            val = (p.get("goals_2026", 0) or 0) + (p.get("assists_2026", 0) or 0) * 0.5
            total_val += val * w
            total_weight += w
        return total_val / total_weight if total_weight else 0

    ga = team_weighted_avg(team_a)
    gb = team_weighted_avg(team_b)
    diff = ga - gb
    return max(-10, min(10, diff))

def calculate_home_advantage(team_a, team_b, venue_country, is_neutral=False,
                             team_a_data=None, team_b_data=None):
    """Ventaja de localia: pais sede, fanbase CONCACAF, diaspora."""
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
    """Impacto climatico: temperatura, altitud y techo del estadio."""
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
    """Distancia desde el base camp del equipo hasta la sede."""
    base = BASE_CAMPS.get(team, "Dallas")
    base_coords = CITY_COORDS.get(base)
    venue_coords = CITY_COORDS.get(venue_name)
    if not base_coords or not venue_coords:
        return 0
    return haversine(base_coords[0], base_coords[1], venue_coords[0], venue_coords[1])

def calculate_travel_impact(team_a, team_b, venue_name):
    """Diferencia de distancia base camp->sede entre equipos."""
    da = _base_to_venue_dist(team_a, venue_name)
    db = _base_to_venue_dist(team_b, venue_name)
    diff = (db - da) / 1000
    return max(-6, min(6, diff))

def calculate_history_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia en historial mundialista entre equipos."""
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
    """Diferencia de moral basada en racha de resultados reciente."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    morale_a = team_a_data["form_streak"] * 15
    morale_b = team_b_data["form_streak"] * 15
    return morale_a - morale_b

def calculate_friendly_form_factor(team_a, team_b):
    """Diferencia de forma en amistosos recientes."""
    fa = compute_friendly_form(team_a)
    fb = compute_friendly_form(team_b)
    return max(-10, min(10, fa - fb))

def calculate_market_value_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia de valor de plantilla (escala log)."""
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
    """Diferencia de porcentaje de jugadores en ligas extranjeras."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("foreign_pct", 0.8)
    b = team_b_data.get("foreign_pct", 0.8)
    return (a - b) * 10

def calculate_experience_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia de experiencia promedio (caps internacionales)."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("avg_caps", 15)
    b = team_b_data.get("avg_caps", 15)
    diff = (a - b) / 30
    return max(-10, min(10, diff))

def calculate_trophy_factor(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia de trofeos promedio por jugador."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("avg_trophies", 1)
    b = team_b_data.get("avg_trophies", 1)
    diff = (a - b) / 5
    return max(-10, min(10, diff))

def calculate_height_advantage(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia de altura promedio (ventaja aerea)."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("avg_height", 1.80)
    b = team_b_data.get("avg_height", 1.80)
    diff = (a - b) / 0.05
    return max(-10, min(10, diff))

def calculate_club_chemistry(team_a, team_b, team_a_data=None, team_b_data=None):
    """Diferencia de pares del mismo club (coordinacion)."""
    if team_a_data is None:
        team_a_data = get_team(team_a)
    if team_b_data is None:
        team_b_data = get_team(team_b)
    a = team_a_data.get("club_pairs", 0)
    b = team_b_data.get("club_pairs", 0)
    return max(-10, min(10, a - b))

def calculate_rest_days(team_a, team_b, rest_a=None, rest_b=None):
    """Penaliza equipos con menos de 4 dias de descanso."""
    ra = rest_a if rest_a is not None else 5
    rb = rest_b if rest_b is not None else 5
    penalty_a = max(0, (4 - ra)) * 3
    penalty_b = max(0, (4 - rb)) * 3
    return max(-10, min(10, penalty_b - penalty_a))

def calculate_travel_fatigue(team_a, team_b, travel_km_a=0, travel_km_b=0):
    """Penaliza equipos con mayor kilometraje acumulado viajando."""
    fa = min(travel_km_a, 30000) / 3000
    fb = min(travel_km_b, 30000) / 3000
    return max(-10, min(10, fb - fa))

def calculate_squad_depth_factor(team_a, team_b):
    """Ventaja para equipos con mas suplentes de impacto (>500 min)."""
    players = _load_players()
    if not players:
        return 0
    def _depth(team_name):
        squad = players.get(team_name, [])
        if not squad:
            return 3
        non_starters = [p for p in squad if p.get("role", "squad") != "starter"]
        if not non_starters:
            return 0
        useful = sum(1 for p in non_starters if (p.get("minutes_2026", 0) or 0) > 500)
        return useful / max(len(non_starters), 1) * 10
    a = _depth(team_a)
    b = _depth(team_b)
    return max(-10, min(10, (a - b) * 2))

def calculate_stakes_factor(stakes_a, stakes_b):
    """Presion de 3ra fecha: clasificado, contendiente o eliminado."""
    values = {"qualified": -1, "contender": 1, "eliminated": -2}
    val_a = values.get(stakes_a, 0)
    val_b = values.get(stakes_b, 0)
    return (val_a - val_b) * 4


def simulate_match_cards(team_a_data, team_b_data):
    """Simula tarjetas amarillas y rojas via Poisson+Bernoulli."""
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


def poisson_pmf(k, lam):
    """Funcion de masa de probabilidad Poisson."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def dixon_coles_tau(x, y, lam_h, lam_a, rho=DIXON_COLES_RHO):
    """Correccion Dixon-Coles tau para resultados de bajo score."""
    if x == 0 and y == 0:
        return max(0, 1 - lam_h * lam_a * rho)
    elif x == 0 and y == 1:
        return max(0, 1 + lam_h * rho)
    elif x == 1 and y == 0:
        return max(0, 1 + lam_a * rho)
    elif x == 1 and y == 1:
        return max(0, 1 - rho)
    return 1.0


def _build_joint_dist(lam_h, lam_a, rho=DIXON_COLES_RHO, max_g=MAX_GOALS_DC):
    """Construye distribucion conjunta 16x16 con correccion tau."""
    pmf_h = [poisson_pmf(k, lam_h) for k in range(max_g + 1)]
    pmf_a = [poisson_pmf(k, lam_a) for k in range(max_g + 1)]
    outcomes = []
    weights = []
    for x in range(max_g + 1):
        px = pmf_h[x]
        for y in range(max_g + 1):
            p = px * pmf_a[y] * dixon_coles_tau(x, y, lam_h, lam_a, rho)
            if p > 0:
                outcomes.append((x, y))
                weights.append(p)
    total = sum(weights)
    weights = [w / total for w in weights]
    return outcomes, weights


def predict_match(team_a, team_b, venue_name, is_neutral=False, allows_draw=None, round_name="Group Stage",
                  rest_days_a=None, rest_days_b=None, travel_km_a=0, travel_km_b=0,
                  stakes_a=None, stakes_b=None, md3_variance_boost=False):
    """Predice resultado completo de un partido: scores, probabilidades, factores, tarjetas."""
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
    rest_diff = calculate_rest_days(team_a, team_b, rest_days_a, rest_days_b) * WEIGHTS["rest_days"]
    depth_diff = calculate_squad_depth_factor(team_a, team_b) * WEIGHTS["squad_depth"]
    fatigue_diff = calculate_travel_fatigue(team_a, team_b, travel_km_a, travel_km_b) * WEIGHTS["travel_fatigue"]
    exp_diff = calculate_experience_factor(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["experience"]
    trophy_diff = calculate_trophy_factor(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["trophy_pedigree"]
    height_diff = calculate_height_advantage(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["height_advantage"]
    chem_diff = calculate_club_chemistry(team_a, team_b, team_a_data, team_b_data) * WEIGHTS["club_chemistry"]
    stakes_diff = calculate_stakes_factor(stakes_a, stakes_b) * WEIGHTS["stakes"]
    friendly_diff = calculate_friendly_form_factor(team_a, team_b) * WEIGHTS["friendly_form"]

    total_diff = (strength_diff + mv_diff + ps_diff + odds_diff + home_diff + climate_diff +
                  travel_diff + history_diff + morale_diff + foreign_diff +
                  rest_diff + depth_diff + fatigue_diff +
                  exp_diff + trophy_diff + height_diff + chem_diff + stakes_diff + friendly_diff)

    deterministic_scaled = total_diff / 25

    base_a = (team_a_data["goals_scored_avg"] + team_b_data["goals_conceded_avg"]) / 2
    base_b = (team_b_data["goals_scored_avg"] + team_a_data["goals_conceded_avg"]) / 2

    det_goals_a = max(0.2, min(7.0, base_a * (1 + deterministic_scaled)))
    det_goals_b = max(0.2, min(7.0, base_b * (1 - deterministic_scaled)))

    SIMS = 1500
    sum_a = 0
    sum_b = 0
    wins_a = 0
    wins_b = 0
    draws = 0

    add_variance = md3_variance_boost and stakes_a and stakes_b and (
        (stakes_a == "contender" and stakes_b == "contender") or
        (stakes_a == "contender" or stakes_b == "contender")
    )

    if not add_variance:
        outcomes, joint_weights = _build_joint_dist(det_goals_a, det_goals_b)
        chosen = random.choices(range(len(outcomes)), weights=joint_weights, k=SIMS)
        for idx in chosen:
            g_a, g_b = outcomes[idx]
            sum_a += g_a
            sum_b += g_b
            if g_a > g_b:
                wins_a += 1
            elif g_b > g_a:
                wins_b += 1
            else:
                draws += 1
    else:
        for _ in range(SIMS):
            noise = random.gauss(0, 0.15)
            g_a = poisson_sample(max(0.2, min(7.0, det_goals_a + noise)))
            g_b = poisson_sample(max(0.2, min(7.0, det_goals_b - noise)))
            sum_a += g_a
            sum_b += g_b
            if g_a > g_b:
                wins_a += 1
            elif g_b > g_a:
                wins_b += 1
            else:
                draws += 1

    score_a = round(sum_a / SIMS)
    score_b = round(sum_b / SIMS)
    prob_a_win = wins_a / SIMS
    prob_b_win = wins_b / SIMS
    prob_draw = draws / SIMS

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
        "rest_days": round(rest_diff, 1),
        "squad_depth": round(depth_diff, 1),
        "travel_fatigue": round(fatigue_diff, 1),
        "experience": round(exp_diff, 1),
        "trophy_pedigree": round(trophy_diff, 1),
        "height_advantage": round(height_diff, 1),
        "club_chemistry": round(chem_diff, 1),
        "stakes": round(stakes_diff, 1),
        "friendly_form": round(friendly_diff, 1),
        "stakes_a": stakes_a,
        "stakes_b": stakes_b,
    }

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
        "probabilities": {
            "a_win": round(prob_a_win * 100, 1),
            "draw":  round(prob_draw * 100, 1),
            "b_win": round(prob_b_win * 100, 1),
        },
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
    """Genera un sample Poisson para un lambda dado."""
    L = math.exp(-lambda_val)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1
