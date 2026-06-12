# -*- coding: utf-8 -*-
"""
Bracket oficial 2026: fase de grupos, R32, R16, QF, SF, 3 puesto, Final.

Incluye tiebreaker FIFA articulo 13 (H2H, GD, GF, Fair Play, ranking),
clasificacion de stakes MD3, y safety net KO con ranking FIFA.
"""

import re
from datetime import datetime
from prode_mundial.predictor import predict_match
from prode_mundial.data import GROUPS, CITY_COORDS, haversine, get_team
from prode_mundial.real_results import (
    compute_real_form, track_suspensions, apply_player_stats,
    update_goals_conceded_avg, update_aerial_factor, load_real_results
)

_RE_ASCII = re.compile(r'[^\x20-\x7e]')
def _safe(text):
    """Limpia caracteres no ASCII para terminal Windows."""
    return _RE_ASCII.sub('?', str(text))



def _venue_dist(venue_a, venue_b):
    """Distancia entre bases y sede usando haversine."""
    coords_a = CITY_COORDS.get(venue_a)
    coords_b = CITY_COORDS.get(venue_b)
    if not coords_a or not coords_b:
        return 0
    return haversine(coords_a[0], coords_a[1], coords_b[0], coords_b[1])

def compute_team_history(group_predictions):
    """Calcula ultima fecha/sede/km total por equipo tras grupos."""
    history = {}
    by_date = sorted(group_predictions, key=lambda p: p.get("date", "2026-06-10"))
    for p in by_date:
        a, b = p["team_a"], p["team_b"]
        venue, date = p["venue"], p.get("date", "2026-06-10")
        for team in [a, b]:
            if team not in history:
                history[team] = {"last_date": None, "last_venue": None, "total_travel": 0}
            prev = history[team]
            if prev["last_venue"] is not None:
                prev["total_travel"] += _venue_dist(prev["last_venue"], venue)
            prev["last_date"] = date
            prev["last_venue"] = venue
    return history

def _rest_days_since(last_date, current_date):
    """Dias de descanso entre dos fechas de partido."""
    if not last_date:
        return 5
    try:
        ld = datetime.strptime(last_date, "%Y-%m-%d")
        cd = datetime.strptime(current_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return 5
    return (cd - ld).days

# Official Round of 32 pairings (from FIFA / match-later.com)
# Format: (type, param_a, param_b)
# type: "1v3" = group winner vs 3rd place, "2v2" = runner-up vs runner-up
R32_BRACKET = [
    # Match 01-16: (pairing_type, team_a_spec, team_b_spec, venue)
    # 1E vs 3rd from ABCDF
    {"a": ("winner", "E"), "b": ("third", ["A","B","C","D","F"]), "venue": "Boston"},
    # 1I vs 3rd from CDFGH
    {"a": ("winner", "I"), "b": ("third", ["C","D","F","G","H"]), "venue": "New York"},
    # 2A vs 2B
    {"a": ("runner", "A"), "b": ("runner", "B"), "venue": "Los Angeles"},
    # 1F vs 2C
    {"a": ("winner", "F"), "b": ("runner", "C"), "venue": "Monterrey"},
    # 2K vs 2L
    {"a": ("runner", "K"), "b": ("runner", "L"), "venue": "Toronto"},
    # 1H vs 2J
    {"a": ("winner", "H"), "b": ("runner", "J"), "venue": "Los Angeles"},
    # 1D vs 3rd from BEFIJ
    {"a": ("winner", "D"), "b": ("third", ["B","E","F","I","J"]), "venue": "San Francisco"},
    # 1G vs 3rd from AEHIJ
    {"a": ("winner", "G"), "b": ("third", ["A","E","H","I","J"]), "venue": "Seattle"},
    # 1C vs 2F
    {"a": ("winner", "C"), "b": ("runner", "F"), "venue": "Houston"},
    # 2E vs 2I
    {"a": ("runner", "E"), "b": ("runner", "I"), "venue": "Dallas"},
    # 1A vs 3rd from CEFHI
    {"a": ("winner", "A"), "b": ("third", ["C","E","F","H","I"]), "venue": "Mexico City"},
    # 1L vs 3rd from EHIJK
    {"a": ("winner", "L"), "b": ("third", ["E","H","I","J","K"]), "venue": "Atlanta"},
    # 1J vs 2H
    {"a": ("winner", "J"), "b": ("runner", "H"), "venue": "Miami"},
    # 2D vs 2G
    {"a": ("runner", "D"), "b": ("runner", "G"), "venue": "Dallas"},
    # 1B vs 3rd from EFGIJ
    {"a": ("winner", "B"), "b": ("third", ["E","F","G","I","J"]), "venue": "Vancouver"},
    # 1K vs 3rd from DEIJL
    {"a": ("winner", "K"), "b": ("third", ["D","E","I","J","L"]), "venue": "Kansas City"},
]

# Round of 16 pairings (winners of matches above) — official FIFA 2026
# ⚠️ R16_PAIRINGS uses hard-coded indices into r32_results (build_round_of_32 outputs).
# If R32_BRACKET order changes (new FIFA release), these indices will silently break.
# To fix: re-derive from the official bracket diagram, not the match list order.
R16_PAIRINGS = [
    (2, 8),   # R16-1: M03(2A/2B) vs M09(1C/2F) → Philadelphia
    (0, 3),   # R16-2: M01(1E/3rd) vs M04(1F/2C) → Houston
    (1, 9),   # R16-3: M02(1I/3rd) vs M10(2E/2I) → New York
    (10, 11), # R16-4: M11(1A/3rd) vs M12(1L/3rd) → Mexico City
    (6, 7),   # R16-5: M07(1D/3rd) vs M08(1G/3rd) → Dallas
    (4, 5),   # R16-6: M05(2K/2L) vs M06(1H/2J) → Seattle
    (14, 12), # R16-7: M15(1B/3rd) vs M13(1J/2H) → Atlanta
    (15, 13), # R16-8: M16(1K/3rd) vs M14(2D/2G) → Vancouver
]

R16_VENUES = [
    "Philadelphia", "Houston", "New York", "Mexico City",
    "Dallas", "Seattle", "Atlanta", "Vancouver",
]

QF_VENUES = ["Philadelphia", "Atlanta", "Miami", "New York"]
SF_VENUES = ["Dallas", "Atlanta"]
FINAL_VENUE = "New York"
THIRD_VENUE = "Miami"


def _get_team_ranking(team_name):
    """Retorna ranking FIFA de un equipo (o 100 como fallback)."""
    from prode_mundial.data import get_team
    return get_team(team_name).get("rank", 100)


def _h2h_key(team_name, group_name, tied_names):
    """Compute (h2h_pts, h2h_gd, h2h_gf) within tied teams only."""
    h2h = _h2h_matches.get(group_name, {})
    h2h_pts = h2h_gd = h2h_gf = 0
    for opponent, matches in h2h.get(team_name, {}).items():
        if opponent not in tied_names:
            continue
        for m in matches:
            g_diff = m["goals_a"] - m["goals_b"]
            h2h_gd += g_diff
            h2h_gf += m["goals_a"]
            if g_diff > 0:
                h2h_pts += 3
            elif g_diff == 0:
                h2h_pts += 1
    return h2h_pts, h2h_gd, h2h_gf


def _sort_group(group_name, standings):
    """Sort group standings using FIFA 2026 Article 13 cascade."""
    teams = [(name, data) for name, data in standings.items()]

    def sort_key(item):
        name, d = item
        return (-d["pts"], -d["gd"], -d["gf"], -d.get("fp", 0), _get_team_ranking(name))

    teams.sort(key=sort_key)

    pts_groups = {}
    for name, d in teams:
        pts_groups.setdefault(d["pts"], []).append(name)

    result = []
    for pts, tied_names in pts_groups.items():
        if len(tied_names) == 1:
            result.append((tied_names[0], standings[tied_names[0]]))
        else:
            tied = [(n, standings[n]) for n in tied_names]
            tied.sort(key=lambda x: _h2h_key(x[0], group_name, tied_names), reverse=True)
            result.extend(tied)

    return result

_h2h_matches = {}

def simulate_group_stage(predictions):
    """Procesa resultados de grupos, aplica tiebreaker FIFA 2026."""
    group_results = {}
    for g in GROUPS:
        group_results[g] = {t: {"pts": 0, "gd": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0, "fp": 0} for t in GROUPS[g]}

    global _h2h_matches
    _h2h_matches.clear()
    for p in predictions:
        g = p["round"].split()[-1]
        a, b = p["team_a"], p["team_b"]
        ga, gb = p["score_a"], p["score_b"]
        gd = ga - gb
        group_results[g][a]["gf"] += ga
        group_results[g][a]["ga"] += gb
        group_results[g][a]["gd"] += gd
        group_results[g][b]["gf"] += gb
        group_results[g][b]["ga"] += ga
        group_results[g][b]["gd"] -= gd

        fp_a = p.get("fp_delta_a", 0)
        fp_b = p.get("fp_delta_b", 0)
        group_results[g][a]["fp"] += fp_a
        group_results[g][b]["fp"] += fp_b

        if g not in _h2h_matches:
            _h2h_matches[g] = {}
        if a not in _h2h_matches[g]:
            _h2h_matches[g][a] = {}
        if b not in _h2h_matches[g]:
            _h2h_matches[g][b] = {}
        if b not in _h2h_matches[g][a]:
            _h2h_matches[g][a][b] = []
        if a not in _h2h_matches[g][b]:
            _h2h_matches[g][b][a] = []
        _h2h_matches[g][a][b].append({"goals_a": ga, "goals_b": gb})
        _h2h_matches[g][b][a].append({"goals_a": gb, "goals_b": ga})

        if ga > gb:
            group_results[g][a]["pts"] += 3
            group_results[g][a]["w"] += 1
            group_results[g][b]["l"] += 1
        elif gb > ga:
            group_results[g][b]["pts"] += 3
            group_results[g][b]["w"] += 1
            group_results[g][a]["l"] += 1
        else:
            group_results[g][a]["pts"] += 1
            group_results[g][b]["pts"] += 1
            group_results[g][a]["d"] += 1
            group_results[g][b]["d"] += 1

    sorted_results = {}
    for g in group_results:
        sorted_results[g] = _sort_group(g, group_results[g])

    return sorted_results


def determine_qualified(group_results):
    """Determina 1ros, 2dos y mejores 8 terceros."""
    group_winners = {}
    group_runners = {}
    third_placed = []

    for g in GROUPS:
        table = group_results[g]
        group_winners[g] = table[0][0]
        group_runners[g] = table[1][0]
        if len(table) >= 3:
            t3 = table[2][1]
            third_placed.append((g, table[2][0], t3["pts"], t3["gd"], t3["gf"], t3.get("fp", 0), _get_team_ranking(table[2][0])))

    third_placed.sort(key=lambda x: (-x[2], -x[3], -x[4], -x[5], x[6]))
    best_third = third_placed[:8]

    return group_winners, group_runners, [t[1] for t in best_third], best_third


def build_round_of_32(group_winners, group_runners, best_third, best_third_with_group):
    """Build R32 matches using the official fixed bracket.
    
    Each third-place team is assigned to at most one match slot.
    """
    # Build a lookup: team -> group for third-place teams
    third_team_to_group = {t[1]: t[0] for t in best_third_with_group}

    # Step 1: resolve all fixed slots first
    matches = []
    pending_third = []  # (index, side, candidate_groups, venue)
    for i, slot in enumerate(R32_BRACKET):
        team_a = None
        team_b = None

        typ_a, param_a = slot["a"]
        if typ_a == "winner":
            team_a = group_winners[param_a]
        elif typ_a == "runner":
            team_a = group_runners[param_a]
        else:
            pending_third.append((i, "a", param_a, slot["venue"]))

        typ_b, param_b = slot["b"]
        if typ_b == "runner":
            team_b = group_runners[param_b]
        else:
            pending_third.append((i, "b", param_b, slot["venue"]))

        matches.append((team_a, team_b, slot["venue"]))

    # Step 2: assign third-place teams greedily
    assigned = set()
    # Sort by fewest candidates first for better matching
    pending_third.sort(key=lambda x: len(x[2]))

    for match_idx, side, candidate_groups, venue in pending_third:
        chosen = None
        for g in candidate_groups:
            if g in third_team_to_group.values():
                # Find the team from this group
                for team, grp in third_team_to_group.items():
                    if grp == g and team not in assigned:
                        chosen = team
                        assigned.add(team)
                        break
            if chosen:
                break

        # Fallback: pick any unassigned third-place team
        if not chosen:
            for team in third_team_to_group:
                if team not in assigned:
                    chosen = team
                    assigned.add(team)
                    break

        a, b, _ = matches[match_idx]
        if side == "a":
            matches[match_idx] = (chosen, b, venue)
        else:
            matches[match_idx] = (a, chosen, venue)

    return matches


def _ranking_winner(team_a, team_b, data_a, data_b):
    """Desempate por ranking FIFA."""
    if data_a.get("rank", 100) < data_b.get("rank", 100):
        return team_a, team_b
    return team_b, team_a


def simulate_knockout_round(matches, team_history=None, match_date="2026-07-01", round_name="KO"):
    """Simula una ronda KO completa."""
    from prode_mundial.data import get_team
    UPSET_CONFIDENCE_THRESHOLD = 40
    results = []
    for item in matches:
        if len(item) == 3:
            team_a, team_b, venue = item
            rest_a = rest_b = None
            travel_a = travel_b = 0
        else:
            team_a, team_b, venue, rest_a, rest_b, travel_a, travel_b = item

        if team_history:
            ha = team_history.get(team_a, {})
            hb = team_history.get(team_b, {})
            if rest_a is None:
                rest_a = _rest_days_since(ha.get("last_date"), match_date)
            if rest_b is None:
                rest_b = _rest_days_since(hb.get("last_date"), match_date)
            travel_a = travel_a or ha.get("total_travel", 0)
            travel_b = travel_b or hb.get("total_travel", 0)

        result = predict_match(team_a, team_b, venue, is_neutral=True, allows_draw=False, round_name=round_name,
                               rest_days_a=rest_a, rest_days_b=rest_b,
                               travel_km_a=travel_a, travel_km_b=travel_b,
                               )

        if result["confidence"] < UPSET_CONFIDENCE_THRESHOLD and result["winner"] != "Empate":
            data_a = get_team(team_a)
            data_b = get_team(team_b)
            w, l = _ranking_winner(team_a, team_b, data_a, data_b)
            result["winner"] = w
            result["loser"] = l
            rank_diff = abs(data_a.get("rank", 100) - data_b.get("rank", 100))
            if rank_diff > 20:
                result["score_a"], result["score_b"] = (2, 1) if w == team_a else (1, 2)
            else:
                result["score_a"], result["score_b"] = (1, 0) if w == team_a else (0, 1)
            prob_key = "prob_a_win" if w == team_a else "prob_b_win"
            result["confidence"] = round(result.get(prob_key, 50), 1)
            result["result_type"] = "ranking_fallback"
            result["upset_corrected"] = True

        if result["winner"] == "Empate":
            data_a = get_team(team_a)
            data_b = get_team(team_b)
            w, l = _ranking_winner(team_a, team_b, data_a, data_b)
            result["winner"] = w
            result["loser"] = l
            result["result_type"] = "penales"

        results.append(result)
    return results


def _find_real_result(team_a, team_b, real_results):
    """Busca partido real entre team_a y team_b en real_results."""
    if not real_results:
        return None
    for rr in real_results:
        ra, rb = rr["team_a"], rr["team_b"]
        if (ra == team_a and rb == team_b) or (ra == team_b and rb == team_a):
            return rr
    return None


def _apply_real_result(rr, team_a, team_b, venue, date, time, group,
                       team_suspensions, team_extra_goals,
                       team_goals_conceded_delta, team_aerial_modifiers,
                       team_real_forms):
    """Procesa un resultado real: construye el dict result y actualiza estado."""
    from prode_mundial.data import VENUES
    rr_venue = rr.get("venue", venue)
    rr_venue_country = VENUES.get(rr_venue, {}).get("country", "USA")
    result = {
        "team_a": rr["team_a"],
        "team_b": rr["team_b"],
        "score_a": rr["score_a"],
        "score_b": rr["score_b"],
        "winner": rr["team_a"] if rr["score_a"] > rr["score_b"] else (rr["team_b"] if rr["score_b"] > rr["score_a"] else "Empate"),
        "loser": rr["team_b"] if rr["score_a"] > rr["score_b"] else (rr["team_a"] if rr["score_b"] > rr["score_a"] else "Empate"),
        "venue": rr_venue,
        "venue_country": rr_venue_country,
        "date": rr.get("date", date),
        "time": rr.get("time", time),
        "round": f"Group {group}",
        "result_type": "real",
        "confidence": 100.0,
        "expected_goals_a": rr.get("stats_a", {}).get("xG"),
        "expected_goals_b": rr.get("stats_b", {}).get("xG"),
        "prob_a_win": 100.0 if rr["score_a"] > rr["score_b"] else 0,
        "prob_b_win": 100.0 if rr["score_b"] > rr["score_a"] else 0,
        "prob_draw": 100.0 if rr["score_a"] == rr["score_b"] else 0,
        "factors": {},
    }

    # Init state tracking
    team_suspensions.setdefault(rr["team_a"], set())
    team_suspensions.setdefault(rr["team_b"], set())
    team_extra_goals.setdefault(rr["team_a"], {})
    team_extra_goals.setdefault(rr["team_b"], {})
    team_goals_conceded_delta.setdefault(rr["team_a"], 0)
    team_goals_conceded_delta.setdefault(rr["team_b"], 0)
    team_aerial_modifiers.setdefault(rr["team_a"], 1.0)
    team_aerial_modifiers.setdefault(rr["team_b"], 1.0)

    # Suspensions from this match
    sus = track_suspensions([rr])
    for t, pl in sus.items():
        team_suspensions[t].update(pl)

    # Extra goals/assists per team from stats
    for stats_side, tname in [(rr.get("stats_a", {}), rr["team_a"]), (rr.get("stats_b", {}), rr["team_b"])]:
        egs = {}
        for gd in stats_side.get("goals", []):
            pn = gd["player"]
            egs.setdefault(pn, {"goals": 0, "assists": 0})
            egs[pn]["goals"] += 1
            gd_assist = gd.get("assist")
            if gd_assist and gd_assist in egs:
                egs[gd_assist]["assists"] += 1
            elif gd_assist:
                egs.setdefault(gd_assist, {"goals": 0, "assists": 1})
                egs[gd_assist]["assists"] += 1
        for pn, eg in egs.items():
            if pn in team_extra_goals[tname]:
                team_extra_goals[tname][pn]["goals"] += eg["goals"]
                team_extra_goals[tname][pn]["assists"] += eg["assists"]
            else:
                team_extra_goals[tname][pn] = eg

        errs = stats_side.get("errors_leading_to_goal", 0)
        if errs:
            team_goals_conceded_delta[tname] -= errs * 0.1

        aer_w = stats_side.get("aerial_duels_won", 0)
        aer_t = stats_side.get("aerial_duels_total", 0)
        if aer_t > 0:
            team_aerial_modifiers[tname] = (aer_w / aer_t) * 2

    # Compute real form after processing both sides
    form_a = compute_real_form(rr, "stats_a")
    form_b = compute_real_form(rr, "stats_b")
    team_real_forms[rr["team_a"]] = form_a
    team_real_forms[rr["team_b"]] = form_b

    # Apply goals conceded override
    for tname, delta in team_goals_conceded_delta.items():
        if delta != 0:
            td = get_team(tname)
            current_avg = td.get("goals_conceded_avg", 1.2)
            td["goals_conceded_avg"] = max(0.3, current_avg + delta)

    # Apply aerial modifier override
    for tname, mod in team_aerial_modifiers.items():
        if mod != 1.0:
            td = get_team(tname)
            td["_aerial_modifier"] = mod

    return result


def classify_stakes(standings):
    """After MD2, classify each team's stakes for MD3 matches.

    standings: {team_name: {"pts": int, "gd": int, "gf": int}}
    Returns: {team_name: "qualified" | "contender" | "eliminated"}
    """
    sorted_teams = sorted(standings.items(), key=lambda x: (-x[1]["pts"], -x[1]["gd"], -x[1]["gf"]))
    second_pts = sorted_teams[1][1]["pts"]

    stakes = {}
    for team, data in standings.items():
        pts = data["pts"]
        max_possible = pts + 3

        if pts >= 6 and second_pts <= 3:
            stakes[team] = "qualified"
        elif max_possible < second_pts:
            stakes[team] = "eliminated"
        elif pts == 0 and second_pts >= 4:
            stakes[team] = "eliminated"
        else:
            stakes[team] = "contender"

    return stakes


def run_full_simulation(seed=42, quiet=False, progress_callback=None, real_results=None):
    """Orquesta simulacion completa: grupos + KO.
    
    Si real_results es una lista de dicts con resultados reales de MD1,
    se usan en lugar de predecir esos partidos.
    """
    import random
    from prode_mundial.data import FIXTURES, GROUPS

    random.seed(seed)

    if progress_callback:
        progress_callback(2, "Iniciando simulacion...")

    if not quiet:
        print("=" * 70)
        print("  PREDICCION MUNDIAL 2026 - PRODE COMPLETO")
        print("=" * 70)

        # ── Group stage ──────────────────────────────────────────────────
        print("\n>>> FASE DE GRUPOS:")
    group_predictions = []
    groups_list = sorted(GROUPS.keys())

    # Track real-results state per group (reset on each group)
    team_suspensions = {}
    team_extra_goals = {}
    team_real_forms = {}
    team_goals_conceded_delta = {}
    team_aerial_modifiers = {}

    for gi, g in enumerate(groups_list):
        group_matches = [f for f in FIXTURES if f[5] == g]

        # ── MD1 ──────────────────────────────────────────────────────
        md1_md2 = []
        for f in group_matches[:2]:
            team_a, team_b, venue, date, time, group = f
            rr = _find_real_result(team_a, team_b, real_results) if real_results else None
            if rr:
                result = _apply_real_result(rr, team_a, team_b, venue, date, time, group,
                                            team_suspensions, team_extra_goals,
                                            team_goals_conceded_delta, team_aerial_modifiers,
                                            team_real_forms)
            else:
                result = predict_match(team_a, team_b, venue, round_name=f"Group {group}",
                                       matchday=1)
                result["date"] = date
                result["time"] = time
            md1_md2.append(result)

        # ── MD2 ──────────────────────────────────────────────────────
        for f in group_matches[2:4]:
            team_a, team_b, venue, date, time, group = f
            rr = _find_real_result(team_a, team_b, real_results) if real_results else None
            if rr:
                result = _apply_real_result(rr, team_a, team_b, venue, date, time, group,
                                            team_suspensions, team_extra_goals,
                                            team_goals_conceded_delta, team_aerial_modifiers,
                                            team_real_forms)
            else:
                result = predict_match(team_a, team_b, venue, round_name=f"Group {group}",
                                       matchday=2,
                                       real_form_a=team_real_forms.get(team_a),
                                       real_form_b=team_real_forms.get(team_b),
                                       extra_goals_a=team_extra_goals.get(team_a),
                                       extra_goals_b=team_extra_goals.get(team_b),
                                       suspended_a=list(team_suspensions.get(team_a, set())),
                                       suspended_b=list(team_suspensions.get(team_b, set())))
                result["date"] = date
                result["time"] = time
            md1_md2.append(result)

        # Compute partial standings after 2 matchdays
        standings = {t: {"pts": 0, "gd": 0, "gf": 0} for t in GROUPS[g]}
        for p in md1_md2:
            a, b = p["team_a"], p["team_b"]
            ga, gb = p["score_a"], p["score_b"]
            standings[a]["gf"] += ga
            standings[a]["gd"] += ga - gb
            standings[b]["gf"] += gb
            standings[b]["gd"] += gb - ga
            if ga > gb:
                standings[a]["pts"] += 3
            elif gb > ga:
                standings[b]["pts"] += 3
            else:
                standings[a]["pts"] += 1
                standings[b]["pts"] += 1

        stakes = classify_stakes(standings)

        # ── MD3 ──────────────────────────────────────────────────────
        for f in group_matches[4:]:
            team_a, team_b, venue, date, time, group = f
            rr = _find_real_result(team_a, team_b, real_results) if real_results else None
            if rr:
                result = _apply_real_result(rr, team_a, team_b, venue, date, time, group,
                                            team_suspensions, team_extra_goals,
                                            team_goals_conceded_delta, team_aerial_modifiers,
                                            team_real_forms)
            else:
                result = predict_match(team_a, team_b, venue, round_name=f"Group {group}",
                                       stakes_a=stakes.get(team_a),
                                       stakes_b=stakes.get(team_b),
                                       md3_variance_boost=True, matchday=3,
                                       real_form_a=team_real_forms.get(team_a),
                                       real_form_b=team_real_forms.get(team_b),
                                       extra_goals_a=team_extra_goals.get(team_a),
                                       extra_goals_b=team_extra_goals.get(team_b),
                                       suspended_a=list(team_suspensions.get(team_a, set())),
                                       suspended_b=list(team_suspensions.get(team_b, set())))
                result["date"] = date
                result["time"] = time
            md1_md2.append(result)

        group_predictions.extend(md1_md2)

        if progress_callback:
            pct = 5 + (gi + 1) * 4
            progress_callback(pct, f"Simulando Grupo {g}...")

        if not quiet:
            for result in md1_md2:
                score_str = f"{_safe(result['team_a'])} {result['score_a']}-{result['score_b']} {_safe(result['team_b'])}"
                xg_a = result.get("expected_goals_a", "?")
                xg_b = result.get("expected_goals_b", "?")
                print(f"  Grupo {g}: {score_str} | xG: {xg_a}-{xg_b} | {_safe(result['winner'])} ({result['confidence']:.0f}%)")

    # ── Group tables ─────────────────────────────────────────────────
    group_results = simulate_group_stage(group_predictions)

    if not quiet:
        print("\n>>> TABLA DE POSICIONES:")
        for g in GROUPS:
            print(f"\n  Grupo {g}:")
            for i, (team, data) in enumerate(group_results[g]):
                print(f"  [{i+1}] {_safe(team):25s} {data['pts']:2d} pts  W:{data['w']} D:{data['d']} L:{data['l']}  GF:{data['gf']} GC:{data['ga']} GD:{data['gd']:+d}")

    # ── Qualified teams ──────────────────────────────────────────────
    if progress_callback:
        progress_callback(54, "Calculando mejores terceros...")
    group_winners, group_runners, best_third, third_details = determine_qualified(group_results)

    if not quiet:
        print("\n>>> MEJORES TERCEROS CLASIFICADOS:")
        for i, (g, team, pts, gd, gf, fp, rank) in enumerate(third_details):
            print(f"  {i+1}. Grupo {g}: {_safe(team)} ({pts} pts, GD:{gd:+d}, FP:{fp}, Rank:{rank})")

    # ── Team history (rest days, travel fatigue) ─────────────────────
    team_history = compute_team_history(group_predictions)
    KO_DATES = ["2026-06-29", "2026-07-04", "2026-07-09", "2026-07-13", "2026-07-16", "2026-07-17"]

    def _extend_matches(base_matches, round_date):
        """Convierte matches basicos a 7-tuplas con datos de descanso/fatiga."""
        extended = []
        for ta, tb, venue in base_matches:
            ha = team_history.get(ta, {})
            hb = team_history.get(tb, {})
            ra = _rest_days_since(ha.get("last_date"), round_date)
            rb = _rest_days_since(hb.get("last_date"), round_date)
            va = ha.get("total_travel", 0) + _venue_dist(ha.get("last_venue", "Dallas"), venue)
            vb = hb.get("total_travel", 0) + _venue_dist(hb.get("last_venue", "Dallas"), venue)
            extended.append((ta, tb, venue, ra, rb, va, vb))
        return extended

    def _update_history(results, round_date):
        """Propaga historial de equipos entre rondas KO."""
        for r in results:
            winner, loser = r["winner"], r["loser"]
            venue = r["venue"]
            for team in [winner, loser]:
                if team and team in team_history:
                    h = team_history[team]
                    if h["last_venue"]:
                        h["total_travel"] += _venue_dist(h["last_venue"], venue)
                    h["last_date"] = round_date
                    h["last_venue"] = venue

    # ── Re-seed for KO rounds (avoid deterministic path) ─────────────
    random.seed(seed + 99)

    # ── Round of 32 ──────────────────────────────────────────────────
    if progress_callback:
        progress_callback(58, "Simulando 32vos de final...")
    r32_raw = build_round_of_32(group_winners, group_runners, best_third, third_details)
    r32_matches = _extend_matches(r32_raw, KO_DATES[0])
    if not quiet:
        print("\n>>> RONDA DE 32AVOS:")
    r32_results = simulate_knockout_round(r32_matches, team_history, KO_DATES[0], round_name="R32")
    for r in r32_results:
        if not quiet:
            print(f"  {_safe(r['team_a'])} {r['score_a']}-{r['score_b']} {_safe(r['team_b'])} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {_safe(r['winner'])} ({r['confidence']:.0f}%)")
    _update_history(r32_results, KO_DATES[0])

    # ── Round of 16 ──────────────────────────────────────────────────
    if progress_callback:
        progress_callback(63, "Simulando octavos de final...")
    r16_raw = []
    for (i, j), venue in zip(R16_PAIRINGS, R16_VENUES):
        if i < len(r32_results) and j < len(r32_results):
            r16_raw.append((r32_results[i]["winner"], r32_results[j]["winner"], venue))
    r16_matches = _extend_matches(r16_raw, KO_DATES[1])
    if not quiet:
        print("\n>>> OCTAVOS DE FINAL:")
    r16_results = simulate_knockout_round(r16_matches, team_history, KO_DATES[1], round_name="R16")
    for r in r16_results:
        if not quiet:
            print(f"  {_safe(r['team_a'])} {r['score_a']}-{r['score_b']} {_safe(r['team_b'])} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {_safe(r['winner'])} ({r['confidence']:.0f}%)")
    _update_history(r16_results, KO_DATES[1])

    # ── Quarter Finals ───────────────────────────────────────────────
    if progress_callback:
        progress_callback(67, "Simulando cuartos de final...")
    qf_raw = []
    for i in range(4):
        idx = i * 2
        if idx + 1 < len(r16_results):
            qf_raw.append((r16_results[idx]["winner"], r16_results[idx + 1]["winner"], QF_VENUES[i] if i < len(QF_VENUES) else "New York"))
    qf_matches = _extend_matches(qf_raw, KO_DATES[2])
    if not quiet:
        print("\n>>> CUARTOS DE FINAL:")
    qf_results = simulate_knockout_round(qf_matches, team_history, KO_DATES[2], round_name="QF")
    for r in qf_results:
        if not quiet:
            print(f"  {_safe(r['team_a'])} {r['score_a']}-{r['score_b']} {_safe(r['team_b'])} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {_safe(r['winner'])} ({r['confidence']:.0f}%)")
    _update_history(qf_results, KO_DATES[2])

    # ── Semi Finals ──────────────────────────────────────────────────
    if progress_callback:
        progress_callback(71, "Simulando semifinales...")
    sf_raw = [
        (qf_results[0]["winner"], qf_results[1]["winner"], SF_VENUES[0]),
        (qf_results[2]["winner"], qf_results[3]["winner"], SF_VENUES[1]),
    ]
    sf_matches = _extend_matches(sf_raw, KO_DATES[3])
    if not quiet:
        print("\n>>> SEMIFINALES:")
    sf_results = simulate_knockout_round(sf_matches, team_history, KO_DATES[3], round_name="SF")
    for r in sf_results:
        if not quiet:
            print(f"  {_safe(r['team_a'])} {r['score_a']}-{r['score_b']} {_safe(r['team_b'])} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {_safe(r['winner'])} ({r['confidence']:.0f}%)")
    _update_history(sf_results, KO_DATES[3])

    # ── Third place ──────────────────────────────────────────────────
    sf_losers = []
    for r in sf_results:
        if r["winner"] == r["team_a"]:
            sf_losers.append(r["team_b"])
        else:
            sf_losers.append(r["team_a"])
    third_raw = [(sf_losers[0], sf_losers[1], THIRD_VENUE)]
    third_matches = _extend_matches(third_raw, KO_DATES[4])
    third_result = simulate_knockout_round(third_matches, team_history, KO_DATES[4], round_name="3°")[0]

    # ── Final ────────────────────────────────────────────────────────
    sf_winners = [r["winner"] for r in sf_results]
    final_raw = [(sf_winners[0], sf_winners[1], FINAL_VENUE)]
    final_matches = _extend_matches(final_raw, KO_DATES[5])
    final_result = simulate_knockout_round(final_matches, team_history, KO_DATES[5], round_name="Final")[0]

    if not quiet:
        print(f"  {_safe(third_result['team_a'])} {third_result['score_a']}-{third_result['score_b']} {_safe(third_result['team_b'])} (xG {third_result.get('expected_goals_a','?')}-{third_result.get('expected_goals_b','?')}) -> 3ro: {_safe(third_result['winner'])}")

        print("\n>>> FINAL:")
        print(f"  {_safe(final_result['team_a'])} {final_result['score_a']}-{final_result['score_b']} {_safe(final_result['team_b'])} (xG {final_result.get('expected_goals_a','?')}-{final_result.get('expected_goals_b','?')})")

        print(f"\n{'='*70}")
        print(f"  *** CAMPEON: {_safe(final_result['winner'])} ***")
        print(f"  SUBCAMPEON: {_safe(final_result['loser'])}")
        print(f"  3er PUESTO: {_safe(third_result['winner'])}")
        print(f"{'='*70}")

    if progress_callback:
        progress_callback(75, "Simulacion completada")

    all_ko = r32_results + r16_results + qf_results + sf_results + [third_result, final_result]

    return group_predictions, group_results, all_ko


if __name__ == "__main__":
    run_full_simulation()
