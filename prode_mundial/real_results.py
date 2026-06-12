# -*- coding: utf-8 -*-
"""Gestion de resultados reales: carga, forma, suspensiones, stats."""

import json
import os
from difflib import SequenceMatcher


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "output")
RESULTS_FILE = os.path.join(RESULTS_DIR, "real_results.json")


def load_real_results(path=RESULTS_FILE):
    """Carga resultados reales desde JSON."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_real_results(data, path=RESULTS_FILE):
    """Guarda resultados reales a JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compute_real_form(match, team_key):
    """Calcula real_form_score (-10 a +10) para un equipo en un partido."""
    stats = match.get(team_key, {})
    opp_key = "stats_b" if team_key == "stats_a" else "stats_a"
    opp_stats = match.get(opp_key, {})

    score_self = match["score_a"] if team_key == "stats_a" else match["score_b"]
    score_opp = match["score_b"] if team_key == "stats_a" else match["score_a"]

    if score_self > score_opp:
        result = 3
    elif score_self == score_opp:
        result = 0
    else:
        result = -3

    xg_self = stats.get("xG", 0)
    xg_opp = opp_stats.get("xG", 0)
    xg_denom = max(xg_self + xg_opp, 0.01)
    xg_diff = max(-2, min(2, (xg_self - xg_opp) / xg_denom * 2 * 0.8))

    shots_self = stats.get("total_shots", 0)
    shots_opp = opp_stats.get("total_shots", 0)
    total_shots = max(shots_self + shots_opp, 1)
    shot_ratio = (shots_self - shots_opp) / total_shots
    shot_diff = max(-1.5, min(1.5, shot_ratio * 3))

    poss = stats.get("possession", 50)
    poss_diff = (poss - 50) / 50 * 1.5

    acc = stats.get("passes_accurate", 0)
    tot = max(stats.get("passes_total", 1), 1)
    ft_acc = stats.get("passes_final_third_accurate", 0)
    ft_tot = max(stats.get("passes_final_third_total", 1), 1)
    passing_score = ((acc / tot) * 0.5 + (ft_acc / ft_tot) * 0.5) * 2 - 1
    passing_score = max(-1, min(1, passing_score))

    c_self = stats.get("corners", 0)
    c_opp = opp_stats.get("corners", 0)
    corner_diff = max(-0.5, min(0.5, (c_self - c_opp) / 6 * 0.5))

    a_won = stats.get("aerial_duels_won", 0)
    a_tot = max(stats.get("aerial_duels_total", 1), 1)
    aerial_diff = ((a_won / a_tot) - 0.5) * 2 * 0.5
    aerial_diff = max(-0.5, min(0.5, aerial_diff))

    err_self = stats.get("errors_leading_to_shot", 0) + stats.get("errors_leading_to_goal", 0)
    err_opp = opp_stats.get("errors_leading_to_shot", 0) + opp_stats.get("errors_leading_to_goal", 0)
    err_diff = max(-0.5, min(0.5, (err_opp - err_self) * 0.25))

    saves_self = stats.get("saves", 0)
    saves_opp = opp_stats.get("saves", 0)
    saves_diff = max(-0.5, min(0.5, (saves_opp - saves_self) / 4 * 0.5))

    total = (
        result * 0.25 +
        xg_diff * 0.20 +
        shot_diff * 0.15 +
        poss_diff * 0.10 +
        passing_score * 0.10 +
        corner_diff * 0.05 +
        aerial_diff * 0.05 +
        err_diff * 0.05 +
        saves_diff * 0.05
    )
    return max(-10, min(10, total))


def track_suspensions(matches):
    """
    Devuelve {team: [player_names]}.
    2 amarillas en distintos partidos → baja.
    1 roja directa → baja.
    """
    acc = {}
    for match in matches:
        for side, team_key in [("stats_a", "team_a"), ("stats_b", "team_b")]:
            team = match[team_key]
            for card in match.get(side, {}).get("yellow_cards", []):
                p = card["player"]
                acc.setdefault(team, {}).setdefault(p, {"yellows": 0, "reds": 0})
                acc[team][p]["yellows"] += 1
            for card in match.get(side, {}).get("red_cards", []):
                p = card["player"]
                acc.setdefault(team, {}).setdefault(p, {"yellows": 0, "reds": 0})
                acc[team][p]["reds"] += 1

    suspended = {}
    for team, players in acc.items():
        for pname, counts in players.items():
            if counts["reds"] >= 1 or counts["yellows"] >= 2:
                suspended.setdefault(team, []).append(pname)
    return suspended


def apply_player_stats(matches):
    """
    Devuelve {team: {player_name: {"goals": N, "assists": N}}}.
    Suma goles y asistencias reales para inyectar en player_stats.
    """
    extra = {}
    for match in matches:
        for side, team_key in [("stats_a", "team_a"), ("stats_b", "team_b")]:
            team = match[team_key]
            for goal in match.get(side, {}).get("goals", []):
                p = goal["player"]
                extra.setdefault(team, {}).setdefault(p, {"goals": 0, "assists": 0})
                extra[team][p]["goals"] += 1
                if goal.get("assist"):
                    a = goal["assist"]
                    extra[team].setdefault(a, {"goals": 0, "assists": 0})
                    extra[team][a]["assists"] += 1
    return extra


def update_goals_conceded_avg(match, team_a_data, team_b_data):
    """Ajusta goals_conceded_avg por errores defensivos reales."""
    for side, data in [("stats_a", team_a_data), ("stats_b", team_b_data)]:
        errors = match[side].get("errors_leading_to_shot", 0) + \
                 match[side].get("errors_leading_to_goal", 0)
        if errors > 0:
            data["goals_conceded_avg"] = min(
                4.0,
                data.get("goals_conceded_avg", 1.5) + errors * 0.1
            )


def update_aerial_factor(match, team_a_data, team_b_data):
    """Modula height_advantage según duelos aéreos reales."""
    for side, data in [("stats_a", team_a_data), ("stats_b", team_b_data)]:
        won = match[side].get("aerial_duels_won", 0)
        tot = max(match[side].get("aerial_duels_total", 1), 1)
        pct = won / tot
        data["_aerial_modifier"] = pct / 0.5
