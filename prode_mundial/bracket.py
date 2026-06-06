# -*- coding: utf-8 -*-
# Simulacion del bracket completo del Mundial 2026
# Formato oficial: 12 grupos, top2 + 8 mejores terceros -> R32 -> R16 -> QF -> SF -> Final

from datetime import datetime
from predictor import predict_match
from data import FIXTURES, GROUPS, CITY_COORDS, haversine



def _venue_dist(venue_a, venue_b):
    coords_a = CITY_COORDS.get(venue_a)
    coords_b = CITY_COORDS.get(venue_b)
    if not coords_a or not coords_b:
        return 0
    return haversine(coords_a[0], coords_a[1], coords_b[0], coords_b[1])

def compute_team_history(group_predictions):
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
    from data import get_team
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
    if data_a.get("rank", 100) < data_b.get("rank", 100):
        return team_a, team_b
    return team_b, team_a


def simulate_knockout_round(matches, team_history=None, match_date="2026-07-01", round_name="KO"):
    from data import get_team
    UPSET_CONFIDENCE_THRESHOLD = 35
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


def run_full_simulation(seed=42, quiet=False):
    import random
    from predictor import predict_match
    from data import FIXTURES, GROUPS

    random.seed(seed)

    if not quiet:
        print("=" * 70)
        print("  PREDICCION MUNDIAL 2026 - PRODE COMPLETO")
        print("=" * 70)

        # ── Group stage ──────────────────────────────────────────────────
        print("\n>>> FASE DE GRUPOS:")
    group_predictions = []
    for f in FIXTURES:
        team_a, team_b, venue, date, time, group = f
        result = predict_match(team_a, team_b, venue, round_name=f"Group {group}")
        result["date"] = date
        result["time"] = time
        group_predictions.append(result)

        if not quiet:
            score_str = f"{result['team_a']} {result['score_a']}-{result['score_b']} {result['team_b']}"
            xg_a = result.get("expected_goals_a", "?")
            xg_b = result.get("expected_goals_b", "?")
            print(f"  Grupo {group}: {score_str} | xG: {xg_a}-{xg_b} | {result['winner']} ({result['confidence']:.0f}%)")

    # ── Group tables ─────────────────────────────────────────────────
    group_results = simulate_group_stage(group_predictions)

    if not quiet:
        print("\n>>> TABLA DE POSICIONES:")
        for g in GROUPS:
            print(f"\n  Grupo {g}:")
            for i, (team, data) in enumerate(group_results[g]):
                print(f"  [{i+1}] {team:25s} {data['pts']:2d} pts  W:{data['w']} D:{data['d']} L:{data['l']}  GF:{data['gf']} GC:{data['ga']} GD:{data['gd']:+d}")

    # ── Qualified teams ──────────────────────────────────────────────
    group_winners, group_runners, best_third, third_details = determine_qualified(group_results)

    if not quiet:
        print("\n>>> MEJORES TERCEROS CLASIFICADOS:")
        for i, (g, team, pts, gd, gf, fp, rank) in enumerate(third_details):
            print(f"  {i+1}. Grupo {g}: {team} ({pts} pts, GD:{gd:+d}, FP:{fp}, Rank:{rank})")

    # ── Team history (rest days, travel fatigue) ─────────────────────
    team_history = compute_team_history(group_predictions)
    KO_DATES = ["2026-06-29", "2026-07-04", "2026-07-09", "2026-07-13", "2026-07-16", "2026-07-17"]

    def _extend_matches(base_matches, round_date):
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

    # ── Round of 32 ──────────────────────────────────────────────────
    r32_raw = build_round_of_32(group_winners, group_runners, best_third, third_details)
    r32_matches = _extend_matches(r32_raw, KO_DATES[0])
    if not quiet:
        print("\n>>> RONDA DE 32AVOS:")
    r32_results = simulate_knockout_round(r32_matches, team_history, KO_DATES[0], round_name="R32")
    for r in r32_results:
        if not quiet:
            print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {r['winner']} ({r['confidence']:.0f}%)")
    _update_history(r32_results, KO_DATES[0])

    # ── Round of 16 ──────────────────────────────────────────────────
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
            print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {r['winner']} ({r['confidence']:.0f}%)")
    _update_history(r16_results, KO_DATES[1])

    # ── Quarter Finals ───────────────────────────────────────────────
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
            print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {r['winner']} ({r['confidence']:.0f}%)")
    _update_history(qf_results, KO_DATES[2])

    # ── Semi Finals ──────────────────────────────────────────────────
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
            print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} (xG {r.get('expected_goals_a','?')}-{r.get('expected_goals_b','?')}) -> {r['winner']} ({r['confidence']:.0f}%)")
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
        print(f"  {third_result['team_a']} {third_result['score_a']}-{third_result['score_b']} {third_result['team_b']} (xG {third_result.get('expected_goals_a','?')}-{third_result.get('expected_goals_b','?')}) -> 3ro: {third_result['winner']}")

        print("\n>>> FINAL:")
        print(f"  {final_result['team_a']} {final_result['score_a']}-{final_result['score_b']} {final_result['team_b']} (xG {final_result.get('expected_goals_a','?')}-{final_result.get('expected_goals_b','?')})")

        print(f"\n{'='*70}")
        print(f"  *** CAMPEON: {final_result['winner']} ***")
        print(f"  SUBCAMPEON: {final_result['loser']}")
        print(f"  3er PUESTO: {third_result['winner']}")
        print(f"{'='*70}")

    all_ko = r32_results + r16_results + qf_results + sf_results + [third_result, final_result]

    return group_predictions, group_results, all_ko


if __name__ == "__main__":
    run_full_simulation()
