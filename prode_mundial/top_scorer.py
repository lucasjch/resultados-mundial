# -*- coding: utf-8 -*-
"""Distribucion de goles a jugadores para calculo de top goleador."""

import json, os, random, sys
from prode_mundial.data import INJURED_OUT, PENALTY_TAKERS, TOP_SCORER_CANDIDATES, _TOP_LEAGUE_CLUBS
from prode_mundial.friendlies_data import get_friendly_scorers

_PLAYERS = None

def _load_players():
    """Carga players.json desde output."""
    global _PLAYERS
    if _PLAYERS is not None:
        return _PLAYERS
    if getattr(sys, 'frozen', False):
        base = os.path.join(sys._MEIPASS, "prode_mundial")
    else:
        base = os.path.dirname(__file__)
    path = os.path.join(base, "output", "players.json")
    with open(path, encoding="utf-8") as f:
        _PLAYERS = json.load(f)
    return _PLAYERS

def _position_weight(pos):
    """Peso segun posicion: FW=1.0, MF=0.4, DF=0.05."""
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

def _league_boost(club_name):
    """Factor de calidad de liga: solo premia ligas top (nunca penaliza)."""
    if not club_name:
        return 1.0
    # Clean club name (remove loan suffixes like "<br>(on loan from ...)")
    clean = club_name.split("<br")[0].split("(")[0].split("{")[0].strip()
    if clean in _TOP_LEAGUE_CLUBS:
        return 1.3
    return 1.0

def _penalty_boost(team_name, player_name):
    """Factor por ser pateador de penales: #1=1.5, #2=1.2, #3=1.0."""
    takers = PENALTY_TAKERS.get(team_name, [])
    if not takers:
        return 1.0
    if player_name == takers[0]:
        return 1.5
    if len(takers) > 1 and player_name == takers[1]:
        return 1.2
    if len(takers) > 2 and player_name == takers[2]:
        return 1.0
    return 1.0

def _build_team_weights(team_name):
    """Construye pesos individuales de goles para un equipo."""
    players = _load_players()
    squad = players.get(team_name, [])
    if not squad:
        return []
    injured = INJURED_OUT.get(team_name, [])
    friendly_scorers = get_friendly_scorers(team_name)
    weights = []
    for p in squad:
        name = p.get("name", "")
        if name in injured:
            continue
        goals = p.get("goals_2026", 0) or 0
        assists = p.get("assists_2026", 0) or 0
        mins = p.get("minutes_2026", 0) or 0
        pos = p.get("position", "")
        pw = _position_weight(pos)
        if pw == 0 or mins < 450:
            continue
        club = p.get("current_club") or p.get("club_name", "")
        goals_per_90 = (goals + assists * 0.3) / mins * 90
        # Raw base from season stats
        raw = goals_per_90 * pw
        # League quality boost (solo premia top 5 ligas, nunca penaliza)
        raw *= _league_boost(club)
        # International experience boost (si hay datos)
        intl_caps = p.get("intl_caps", 0) or 0
        intl_goals = p.get("intl_goals", 0) or 0
        if intl_caps > 5 and intl_goals > 0:
            intl_ratio = intl_goals / max(intl_caps, 1)
            raw *= (1 + intl_ratio * 0.3)
        # Star candidate boost
        raw *= TOP_SCORER_CANDIDATES.get(name, 1.0)
        # Penalty taker boost
        raw *= _penalty_boost(team_name, name)
        # Exponential concentration (elimina piso +0.1)
        w = max(raw ** 1.8, 0.001)
        # Friendly goals boost (sube de 15% a 30%)
        friendly_goals = friendly_scorers.get(name, 0)
        if friendly_goals > 0:
            w *= (1 + friendly_goals * 0.30)
        weights.append((name, w, pw, goals, mins, pos))
    total = sum(w for _, w, _, _, _, _ in weights) or 1
    weighted = [(n, w / total, pw, g, m, pos) for n, w, pw, g, m, pos in weights]
    return weighted

_PLAYER_CACHE = {}

def get_team_weights(team_name):
    """Retorna pesos normalizados de jugadores de un equipo."""
    if team_name not in _PLAYER_CACHE:
        _PLAYER_CACHE[team_name] = _build_team_weights(team_name)
    return _PLAYER_CACHE[team_name]

def distribute_goals(team_name, num_goals):
    """Distribuye goles entre jugadores segun pesos."""
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
    """Construye mapa inverso jugador->equipo."""
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
    """Retorna equipo de un jugador."""
    global _PLAYER_TEAM_CACHE
    if _PLAYER_TEAM_CACHE is None:
        _PLAYER_TEAM_CACHE = _build_player_team_map()
    return _PLAYER_TEAM_CACHE.get(player_name, "?")

def compute_top_scorers(group_predictions, ko_predictions, top_n=20):
    """Calcula tabla de goleadores tras simulacion."""
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

    sorted_players = sorted(
        [(name, get_player_team(name), goals) for name, goals in player_goals.items()],
        key=lambda x: (-x[2], x[0])
    )
    return sorted_players[:top_n], player_goals
