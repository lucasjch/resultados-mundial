# -*- coding: utf-8 -*-
# Distribuye los goles reales de cada partido entre los jugadores de cada
# equipo según su desempeño en la temporada 2025/26 y su posición.

import json, os, random

_PLAYERS = None

def _load_players():
    global _PLAYERS
    if _PLAYERS is not None:
        return _PLAYERS
    path = os.path.join(os.path.dirname(__file__), "output", "players.json")
    with open(path, encoding="utf-8") as f:
        _PLAYERS = json.load(f)
    return _PLAYERS

def _position_weight(pos):
    p = (pos or "").lower()
    if any(x in p for x in ("delantero", "forward", "striker", "extremo", "fw", "cf", "lw", "rw")):
        return 1.0
    if any(x in p for x in ("mediocampista", "midfield", "volante", "centrocampista", "mid", "cm", "cam", "cdm", "mf")):
        return 0.4
    if any(x in p for x in ("defensor", "defensa", "defender", "central", "lateral", "def", "cb", "lb", "rb", "df")):
        return 0.05
    if any(x in p for x in ("arquero", "goalkeeper", "portero", "gk")):
        return 0.0
    return 0.1

def _build_team_weights(team_name):
    players = _load_players()
    squad = players.get(team_name, [])
    if not squad:
        return []
    weights = []
    for p in squad:
        goals = p.get("goals_2026", 0) or 0
        mins = p.get("minutes_2026", 0) or 0
        pos = p.get("position", "")
        name = p.get("name", "")
        pw = _position_weight(pos)
        if pw == 0 or mins < 90:
            continue
        w = max(goals * pw + 0.1, 0.01)
        weights.append((name, w, pw, goals, mins, pos))
    total = sum(w for _, w, _, _, _, _ in weights) or 1
    weighted = [(n, w / total, pw, g, m, pos) for n, w, pw, g, m, pos in weights]
    return weighted

_PLAYER_CACHE = {}

def get_team_weights(team_name):
    if team_name not in _PLAYER_CACHE:
        _PLAYER_CACHE[team_name] = _build_team_weights(team_name)
    return _PLAYER_CACHE[team_name]

def distribute_goals(team_name, num_goals):
    weights = get_team_weights(team_name)
    if not weights or num_goals == 0:
        return {}
    goals = {}
    names = [w[0] for w in weights]
    probs = [w[1] for w in weights]
    for _ in range(num_goals):
        idx = random.choices(range(len(names)), weights=probs, k=1)[0]
        goals[names[idx]] = goals.get(names[idx], 0) + 1
    return goals

def _build_player_team_map():
    players = _load_players()
    result = {}
    for team_name, squad in players.items():
        for p in squad:
            name = p.get("name", "")
            if name:
                result[name] = team_name
    return result

_PLAYER_TEAM_CACHE = None

def get_player_team(player_name):
    global _PLAYER_TEAM_CACHE
    if _PLAYER_TEAM_CACHE is None:
        _PLAYER_TEAM_CACHE = _build_player_team_map()
    return _PLAYER_TEAM_CACHE.get(player_name, "?")

def compute_top_scorers(group_predictions, ko_predictions, top_n=20):
    random.seed(0)
    player_goals = {}

    for r in group_predictions + ko_predictions:
        a = r["team_a"]
        b = r["team_b"]
        ga = r["score_a"]
        gb = r["score_b"]
        for team, ngoals in [(a, ga), (b, gb)]:
            if ngoals == 0:
                continue
            dist = distribute_goals(team, ngoals)
            for player, g in dist.items():
                player_goals[player] = player_goals.get(player, 0) + g

    sorted_players = sorted(player_goals.items(), key=lambda x: (-x[1], x[0]))
    return sorted_players[:top_n], player_goals
