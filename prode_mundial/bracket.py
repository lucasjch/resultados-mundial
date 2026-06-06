# -*- coding: utf-8 -*-
# Simulacion del bracket completo del Mundial 2026
# Formato oficial: 12 grupos, top2 + 8 mejores terceros -> R32 -> R16 -> QF -> SF -> Final

from predictor import predict_match, calculate_team_strength
from data import FIXTURES, GROUPS

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


def simulate_group_stage(predictions):
    group_results = {}
    for g in GROUPS:
        group_results[g] = {t: {"pts": 0, "gd": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0} for t in GROUPS[g]}

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
        st = sorted(group_results[g].items(), key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
        sorted_results[g] = st

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
            third_placed.append((g, table[2][0], table[2][1]["pts"], table[2][1]["gd"], table[2][1]["gf"]))

    third_placed.sort(key=lambda x: (x[2], x[3], x[4]), reverse=True)
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


def simulate_knockout_round(matches):
    results = []
    for team_a, team_b, venue in matches:
        result = predict_match(team_a, team_b, venue, is_neutral=True, round_name="KO")
        results.append(result)
    return results


def run_full_simulation(seed=42):
    import random
    from predictor import predict_match
    from data import FIXTURES, GROUPS

    random.seed(seed)

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

        score_str = f"{result['team_a']} {result['score_a']}-{result['score_b']} {result['team_b']}"
        print(f"  Grupo {group}: {score_str} | {result['winner']} ({result['confidence']:.0f}%)")

    # ── Group tables ─────────────────────────────────────────────────
    group_results = simulate_group_stage(group_predictions)

    print("\n>>> TABLA DE POSICIONES:")
    for g in GROUPS:
        print(f"\n  Grupo {g}:")
        for i, (team, data) in enumerate(group_results[g]):
            print(f"  [{i+1}] {team:25s} {data['pts']:2d} pts  W:{data['w']} D:{data['d']} L:{data['l']}  GF:{data['gf']} GC:{data['ga']} GD:{data['gd']:+d}")

    # ── Qualified teams ──────────────────────────────────────────────
    group_winners, group_runners, best_third, third_details = determine_qualified(group_results)

    print("\n>>> MEJORES TERCEROS CLASIFICADOS:")
    for i, (g, team, pts, gd, gf) in enumerate(third_details):
        print(f"  {i+1}. Grupo {g}: {team} ({pts} pts, GD:{gd:+d})")

    # ── Round of 32 ──────────────────────────────────────────────────
    r32_matches = build_round_of_32(group_winners, group_runners, best_third, third_details)
    print("\n>>> RONDA DE 32AVOS:")
    r32_results = simulate_knockout_round(r32_matches)
    for r in r32_results:
        print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} -> {r['winner']} ({r['confidence']:.0f}%)")

    # ── Round of 16 ──────────────────────────────────────────────────
    r16_matches = []
    for (i, j), venue in zip(R16_PAIRINGS, R16_VENUES):
        if i < len(r32_results) and j < len(r32_results):
            r16_matches.append((r32_results[i]["winner"], r32_results[j]["winner"], venue))

    print("\n>>> OCTAVOS DE FINAL:")
    r16_results = simulate_knockout_round(r16_matches)
    for r in r16_results:
        print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} -> {r['winner']} ({r['confidence']:.0f}%)")

    # ── Quarter Finals ───────────────────────────────────────────────
    qf_matches = []
    for i in range(4):
        idx = i * 2
        if idx + 1 < len(r16_results):
            qf_matches.append((r16_results[idx]["winner"], r16_results[idx + 1]["winner"], QF_VENUES[i] if i < len(QF_VENUES) else "New York"))

    print("\n>>> CUARTOS DE FINAL:")
    qf_results = simulate_knockout_round(qf_matches)
    for r in qf_results:
        print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} -> {r['winner']} ({r['confidence']:.0f}%)")

    # ── Semi Finals ──────────────────────────────────────────────────
    sf_matches = [
        (qf_results[0]["winner"], qf_results[1]["winner"], SF_VENUES[0]),
        (qf_results[2]["winner"], qf_results[3]["winner"], SF_VENUES[1]),
    ]

    print("\n>>> SEMIFINALES:")
    sf_results = simulate_knockout_round(sf_matches)
    for r in sf_results:
        print(f"  {r['team_a']} {r['score_a']}-{r['score_b']} {r['team_b']} -> {r['winner']} ({r['confidence']:.0f}%)")

    # ── Third place ──────────────────────────────────────────────────
    sf_losers = []
    for r in sf_results:
        if r["winner"] == r["team_a"]:
            sf_losers.append(r["team_b"])
        else:
            sf_losers.append(r["team_a"])
    third_match = [(sf_losers[0], sf_losers[1], THIRD_VENUE)]
    third_result = simulate_knockout_round(third_match)[0]

    # ── Final ────────────────────────────────────────────────────────
    sf_winners = [r["winner"] for r in sf_results]
    final_match = [(sf_winners[0], sf_winners[1], FINAL_VENUE)]
    final_result = simulate_knockout_round(final_match)[0]

    print("\n>>> TERCER PUESTO:")
    print(f"  {third_result['team_a']} {third_result['score_a']}-{third_result['score_b']} {third_result['team_b']} -> 3ro: {third_result['winner']}")

    print("\n>>> FINAL:")
    print(f"  {final_result['team_a']} {final_result['score_a']}-{final_result['score_b']} {final_result['team_b']}")

    print(f"\n{'='*70}")
    print(f"  *** CAMPEON: {final_result['winner']} ***")
    print(f"  SUBCAMPEON: {final_result['loser']}")
    print(f"  3er PUESTO: {third_result['winner']}")
    print(f"{'='*70}")

    all_ko = r32_results + r16_results + qf_results + sf_results + [third_result, final_result]

    return group_predictions, group_results, all_ko


if __name__ == "__main__":
    run_full_simulation()
