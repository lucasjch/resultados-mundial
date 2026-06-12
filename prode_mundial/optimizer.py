# -*- coding: utf-8 -*-
"""Optimizador de picks para el PRODE: calcula valor esperado, diferenciacion y recomienda planilla."""

import csv
import json
import math
import os
import re
import sys
import time
from collections import Counter

_RE_ASCII = re.compile(r'[^\x20-\x7e]')
def _safe(text):
    """Limpia caracteres no ASCII para Windows."""
    return _RE_ASCII.sub('?', str(text))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def poisson_pmf(k, lam):
    """Funcion de masa de probabilidad Poisson."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

# ─── Player Tier System ──────────────────────────────────────────────────
# Clasifica jugadores en 6 tiers segun datos objetivos (caps, goles,
# trofeos, edad) para ponderar realisticamente al top goleador.

_PLAYER_TIERS_CACHE = None

_TIER_LABELS = ["Leyenda", "SuperEstrella", "Estrella", "Pro Player", "Juvenil", "Debutante"]
_TIER_MULTIPLIERS = {
    "Leyenda": 2.0,
    "SuperEstrella": 1.5,
    "Estrella": 1.2,
    "Pro Player": 1.0,
    "Juvenil": 0.4,
    "Debutante": 0.1,
}

def _load_all_players():
    """Carga todos los jugadores desde players.json."""
    global _PLAYER_TIERS_CACHE
    if _PLAYER_TIERS_CACHE is not None:
        return _PLAYER_TIERS_CACHE
    path = os.path.join(OUTPUT_DIR, "players.json")
    if not os.path.exists(path):
        _PLAYER_TIERS_CACHE = {}
        return _PLAYER_TIERS_CACHE
    with open(path, encoding="utf-8") as f:
        _PLAYER_TIERS_CACHE = json.load(f)
    return _PLAYER_TIERS_CACHE

def _find_player_data(player_name):
    """Busca datos de un jugador por nombre en players.json."""
    players = _load_all_players()
    for team_name, squad in players.items():
        for p in squad:
            if p.get("name", "") == player_name:
                p["team_name"] = team_name
                return p
    return {}

def classify_player(p):
    """Clasifica un jugador en un tier segun caps, goles, trofeos."""
    caps = p.get("intl_caps", 0) or 0
    intlg = p.get("intl_goals", 0) or 0
    age = p.get("age", 25) or 25
    club_apps = p.get("club_apps", 0) or 0
    club_goals = p.get("club_goals", 0) or 0
    g26 = p.get("goals_2026", 0) or 0
    mins26 = p.get("minutes_2026", 0) or 0
    trophy = p.get("trophy_count", 0) or 0

    has_wiki = (caps > 0 or club_apps > 0)

    if has_wiki:
        if (caps >= 150 and intlg >= 20) or (trophy >= 25 and caps >= 100):
            return "Leyenda"
        if (caps >= 40 and intlg >= 15) or (trophy >= 20 and caps >= 50):
            return "SuperEstrella"
        if age < 23 and caps < 20:
            return "Juvenil"
        if caps < 10:
            return "Debutante"
        if caps >= 20 or club_goals >= 50:
            return "Estrella"
        return "Pro Player"
    else:
        if trophy >= 20 or g26 >= 25:
            return "SuperEstrella"
        if g26 >= 10 or mins26 > 2000:
            return "Pro Player"
        return "Debutante"

def get_player_tier(player_name):
    """Retorna el tier y multiplicador de un jugador."""
    pdata = _find_player_data(player_name)
    if not pdata:
        return "Debutante", 0.1
    tier = classify_player(pdata)
    mult = _TIER_MULTIPLIERS.get(tier, 0.1)
    return tier, mult

# ─── Plausibility System ────────────────────────────────────────────────
# Determina qué tan plausible es que un equipo llegue a cierta ronda,
# considerando: tier, historial mundialista, garra, geopolítica.

_TIER_PLAUSIBILITY = {
    1: 1.0, 2: 0.95, 3: 0.75, 4: 0.45, 5: 0.25, 6: 0.10, 7: 0.05, 8: 0.0,
}

_ROUND_MULTIPLIER = {
    "champion": 0.70,
    "semifinalist": 0.85,
    "quarterfinalist": 0.95,
    "r16": 1.0,
}

_GARRA_BONUS = {
    "Argentina": 0.12,
    "Uruguay": 0.10,
    "Germany": 0.10,
    "France": 0.10,
    "Netherlands": 0.10,
    "Croatia": 0.05,
}

_GEOPOLITICAL_ZERO = {
    "champion": ["Iran"],
    "semifinalist": [],
    "quarterfinalist": [],
    "r16": [],
}

_GEOPOLITICAL_PENALTY = {
    "semifinalist": {"Iran": 0.2},
    "quarterfinalist": {"Iran": 0.4},
}

_FACTOR_BONUS = {
    "market_value": {500: 0.08, 300: 0.05},
    "experience": {40: 0.06, 25: 0.03},
    "player_stats": {3.0: 0.06, 1.5: 0.03},
}

_OPTIMIZER_CACHE_FILE = os.path.join(OUTPUT_DIR, "optimizer_cache.json")


def save_optimizer_data(mc_data, rankings):
    """Guarda datos MC en cache para carga rapida."""
    cache = {
        "champion": {t: mc_data["champion"].get(t, 0) for t in set(mc_data["champion"])},
        "runnerup": {t: mc_data["runnerup"].get(t, 0) for t in set(mc_data["runnerup"])},
        "semifinalist": {t: mc_data["semifinalist"].get(t, 0) for t in set(mc_data["semifinalist"])},
        "quarterfinalist": {t: mc_data["quarterfinalist"].get(t, 0) for t in set(mc_data["quarterfinalist"])},
        "total_sims": mc_data["total_sims"],
        "rankings": rankings,
    }
    with open(_OPTIMIZER_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"  Cache guardado: {_OPTIMIZER_CACHE_FILE}")


def load_optimizer_data():
    """Carga datos MC desde cache."""
    if not os.path.exists(_OPTIMIZER_CACHE_FILE):
        return None
    with open(_OPTIMIZER_CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)


def compute_percentiles(mc_data):
    """P10, P50, P90 por equipo por ronda (distribucion binomial)."""
    import math
    result = {}
    total = mc_data["total_sims"]
    for round_name in ["champion", "semifinalist", "quarterfinalist"]:
        raw = mc_data[round_name]
        teams = sorted(set(raw.keys()))
        pcts = {}
        for team in teams:
            k = raw.get(team, 0)
            p_hat = k / total if total > 0 else 0
            se = math.sqrt(p_hat * (1 - p_hat) / total) if total > 0 else 0
            pcts[team] = {
                "P10": round(max(0, (p_hat - 1.28 * se)) * 100, 2),
                "P50": round(p_hat * 100, 2),
                "P90": round(min(1, (p_hat + 1.28 * se)) * 100, 2),
            }
        result[round_name] = pcts
    return result

def get_plausibility(team_name, round_name):
    """Calcula que tan plausible es que un equipo llegue a cierta ronda."""
    from prode_mundial.data import get_team
    team = get_team(team_name)
    tier = team.get("tier", 5)
    wc = team.get("wc_history", "")

    base = _TIER_PLAUSIBILITY.get(tier, 0.25)

    if "campeon" in wc:
        base = min(1.0, base + 0.15)
    elif "final" in wc:
        base = min(1.0, base + 0.10)
    elif "semifinal" in wc:
        base = min(1.0, base + 0.05)

    base += _GARRA_BONUS.get(team_name, 0.0)

    mv = team.get("market_value_total", 0) or 0
    if mv >= 500:
        base = min(1.0, base + 0.08)
    elif mv >= 300:
        base = min(1.0, base + 0.05)
    elif mv >= 150:
        base = min(1.0, base + 0.02)

    avg_caps = team.get("avg_caps", 0) or 0
    if avg_caps >= 40:
        base = min(1.0, base + 0.06)
    elif avg_caps >= 25:
        base = min(1.0, base + 0.03)

    base *= _ROUND_MULTIPLIER.get(round_name, 1.0)

    if team_name in _GEOPOLITICAL_ZERO.get(round_name, []):
        return 0.0

    if round_name in _GEOPOLITICAL_PENALTY:
        penalty = _GEOPOLITICAL_PENALTY[round_name].get(team_name, 1.0)
        base *= penalty

    return max(0.0, min(1.0, base))

def apply_plausibility(counts, round_name, total_sims):
    """Aplica factor de plausibilidad a conteos de simulacion."""
    adjusted = {}
    for team, count in counts.items():
        p = get_plausibility(team, round_name)
        adjusted[team] = count * p
    return adjusted


# ─── X2 Analysis ────────────────────────────────────────────────────────
def analyze_x2(group_predictions=None):
    """Analiza valor esperado de multiplicadores X2 por partido."""
    if group_predictions is None:
        group_file = os.path.join(OUTPUT_DIR, "fase_grupos.json")
        if not os.path.exists(group_file):
            print("  ERROR: No se encuentra fase_grupos.json. Ejecutá main.py primero.")
            return []
        with open(group_file, encoding="utf-8") as f:
            matches = json.load(f)
    else:
        matches = group_predictions

    results = []
    for m in matches:
        if m.get("result_type") == "real":
            continue
        team_a = m["team_a"]
        team_b = m["team_b"]
        venue = m["venue"]
        score_a = m["score_a"]
        score_b = m["score_b"]
        la = m.get("expected_goals_a", None)
        lb = m.get("expected_goals_b", None)

        if la is None or lb is None:
            continue

        if "probabilities" in m:
            prob_a = m["probabilities"]["a_win"]
            prob_b = m["probabilities"]["b_win"]
            prob_d = m["probabilities"]["draw"]
        else:
            prob_a = m["prob_a_win"]
            prob_b = m["prob_b_win"]
            prob_d = m["prob_draw"]

        if score_a > score_b:
            p_result = prob_a
            predicted = f"{score_a}-{score_b}"
            winner = team_a
        elif score_b > score_a:
            p_result = prob_b
            predicted = f"{score_a}-{score_b}"
            winner = team_b
        else:
            p_result = prob_d
            predicted = f"{score_a}-{score_b}"
            winner = "Empate"

        p_exact = poisson_pmf(score_a, la) * poisson_pmf(score_b, lb)

        ev_without_x2 = 3 * p_exact + 1 * (p_result / 100 - p_exact)
        ev_with_x2 = 6 * p_exact + 4 * (p_result / 100 - p_exact)
        ev_gain = ev_with_x2 - ev_without_x2

        results.append({
            "round": m["round"],
            "date": m.get("date", ""),
            "venue": venue,
            "team_a": team_a,
            "team_b": team_b,
            "score_a": score_a,
            "score_b": score_b,
            "predicted": predicted,
            "winner": winner,
            "p_result_pct": round(p_result, 1),
            "p_exact_pct": round(p_exact * 100, 2),
            "ev_without_x2": round(ev_without_x2, 3),
            "ev_with_x2": round(ev_with_x2, 3),
            "ev_gain": round(ev_gain, 3),
        })

    results.sort(key=lambda x: -x["ev_gain"])
    return results


# ─── Monte Carlo ────────────────────────────────────────────────────────
def run_monte_carlo(iterations=1000, seed_offset=0):
    """Ejecuta simulaciones Monte Carlo para probabilidades de rondas."""
    from io import StringIO
    from contextlib import redirect_stdout
    from prode_mundial.bracket import run_full_simulation

    champion_counts = Counter()
    semifinalist_counts = Counter()
    quarterfinalist_counts = Counter()
    runnerup_counts = Counter()
    thirdplace_counts = Counter()

    print(f"  Corriendo {iterations} simulaciones Monte Carlo...")
    start = time.time()

    for i in range(iterations):
        seed = seed_offset + i + 1

        with redirect_stdout(StringIO()):
            try:
                _, _, all_ko = run_full_simulation(seed=seed)
            except Exception as e:
                continue

        if len(all_ko) < 32:
            continue

        champion = all_ko[-1]["winner"]
        runnerup = all_ko[-1]["loser"]
        third = all_ko[-2]["winner"]
        champion_counts[champion] += 1
        runnerup_counts[runnerup] += 1
        thirdplace_counts[third] += 1

        semifinalists = []
        for idx in range(4):
            qf_idx = 24 + idx
            if qf_idx < len(all_ko):
                w = all_ko[qf_idx]["winner"]
                semifinalists.append(w)
                semifinalist_counts[w] += 1

        quarterfinalists = []
        for idx in range(8):
            r16_idx = 16 + idx
            if r16_idx < len(all_ko):
                w = all_ko[r16_idx]["winner"]
                quarterfinalists.append(w)
                quarterfinalist_counts[w] += 1

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            eta = (elapsed / (i + 1)) * (iterations - i - 1)
            print(f"    Progreso: {i+1}/{iterations} ({elapsed:.0f}s transcurridos, ~{eta:.0f}s restantes)")

    total = iterations
    elapsed = time.time() - start
    print(f"  Monte Carlo completado en {elapsed:.0f}s")

    return {
        "champion": champion_counts,
        "runnerup": runnerup_counts,
        "thirdplace": thirdplace_counts,
        "semifinalist": semifinalist_counts,
        "quarterfinalist": quarterfinalist_counts,
        "total_sims": total,
    }


def get_monte_carlo_rankings(mc_data):
    """Procesa datos de Monte Carlo a rankings con plausibilidad."""
    total = mc_data["total_sims"]
    rankings = {}

    for round_name in ["champion", "semifinalist", "quarterfinalist", "runnerup", "thirdplace"]:
        raw = mc_data[round_name]

        if round_name in ("champion", "runnerup", "thirdplace"):
            adjusted = apply_plausibility(raw, round_name, total)
        elif round_name == "semifinalist":
            adjusted = apply_plausibility(raw, "semifinalist", total)
        elif round_name == "quarterfinalist":
            adjusted = apply_plausibility(raw, "quarterfinalist", total)
        else:
            adjusted = apply_plausibility(raw, "r16", total)

        total_adjusted = sum(adjusted.values())
        ranked = sorted(adjusted.items(), key=lambda x: -x[1])

        table = []
        for team, adj_count in ranked:
            raw_count = raw.get(team, 0)
            raw_pct = raw_count / total * 100
            adj_pct = adj_count / total_adjusted * 100 if total_adjusted > 0 else 0
            plaus = get_plausibility(team, round_name)
            table.append({
                "team": team,
                "raw_count": raw_count,
                "raw_pct": round(raw_pct, 2),
                "plausibility": round(plaus, 2),
                "adj_pct": round(adj_pct, 2),
            })

        rankings[round_name] = table

    return rankings


# ─── Top Scorer ──────────────────────────────────────────────────────────
def analyze_top_scorer(gp, kp, top_n=15):
    """Analiza top goleadores con ajuste por tier."""
    from prode_mundial.top_scorer import compute_top_scorers, get_player_team, distribute_goals, get_team_weights

    raw_scorers, all_goals = compute_top_scorers(gp, kp, top_n=60)

    scored_player_map = {}
    seen = set()
    for player, _team, raw_g in raw_scorers:
        if raw_g == 0:
            continue
        if player in seen:
            continue
        seen.add(player)
        team = get_player_team(player)
        tier, mult = get_player_tier(player)
        adj_g = round(raw_g * mult, 2)
        scored_player_map[player] = {
            "player": player,
            "team": team,
            "tier": tier,
            "tier_mult": mult,
            "raw_goals": raw_g,
            "adj_goals": adj_g,
        }

    adj_list = sorted(scored_player_map.values(), key=lambda x: -x["adj_goals"])

    result = []
    for rank, entry in enumerate(adj_list[:top_n], 1):
        entry["rank"] = rank
        result.append(entry)

    return result


# ─── Diferenciación ──────────────────────────────────────────────────────
_ESTIMATED_POPULARITY = {
    "Argentina": 0.90, "Brazil": 0.90, "France": 0.85, "Germany": 0.85,
    "England": 0.80, "Spain": 0.80, "Portugal": 0.65, "Netherlands": 0.60,
    "Belgium": 0.40, "Uruguay": 0.35, "Croatia": 0.30, "USA": 0.30,
    "Colombia": 0.25, "Mexico": 0.20, "Morocco": 0.15, "Japan": 0.15,
    "Senegal": 0.10, "Sweden": 0.10, "Ecuador": 0.08, "Switzerland": 0.08,
    "Turkey": 0.08, "Austria": 0.05, "Iran": 0.05,
}

def compute_differentiation_score(adj_pct, team_name, round_name):
    """Calcula puntaje ajustado por diferenciacion (popularidad)."""
    raw_score = adj_pct / 100.0
    popularity = _ESTIMATED_POPULARITY.get(team_name, 0.02)

    others_picking = popularity * 11

    if round_name == "champion":
        pts = 6
    elif round_name == "semifinalist":
        pts = 4
    else:
        pts = 1

    differentiation_boost = 1 + (1 - popularity) * 1.5
    adjusted_value = raw_score * differentiation_boost * pts

    return {
        "team": team_name,
        "raw_score_pct": round(adj_pct, 2),
        "estimated_popularity": round(popularity * 100, 0),
        "estimated_others_picking": round(others_picking, 1),
        "differentiation_boost": round(differentiation_boost, 2),
        "adjusted_value": round(adjusted_value, 3),
    }


def analyze_differentiation(rankings):
    """Analiza picks de campeon y semifinalistas con factor diferenciacion."""
    results = {"champion": [], "semifinalist": []}

    for round_name in ["champion", "semifinalist"]:
        for entry in rankings[round_name][:15]:
            team = entry["team"]
            adj_pct = entry["adj_pct"]
            score = compute_differentiation_score(adj_pct, team, round_name)
            results[round_name].append(score)

        results[round_name].sort(key=lambda x: -x["adjusted_value"])

    return results


# ─── Generate Planilla ───────────────────────────────────────────────────
def generar_planilla(x2_ranking, rankings, diff_analysis, top_scorers, gp, kp):
    """Genera planilla CSV con recomendaciones de picks."""
    planilla_path = os.path.join(OUTPUT_DIR, "prode_recomendado.csv")

    champ_top = diff_analysis["champion"][:5] if diff_analysis["champion"] else []
    champ_all = diff_analysis["champion"][:15] if diff_analysis["champion"] else []
    sf_top = diff_analysis["semifinalist"][:6] if diff_analysis["semifinalist"] else []

    safe_champ = champ_top[0]["team"] if champ_top else "N/A"
    value_champ = None
    for c in champ_all:
        pop = c["estimated_popularity"]
        prob = c["raw_score_pct"]
        if pop < 60 and prob > 3.0:
            value_champ = c
            break
    if not value_champ:
        for c in champ_top:
            if c["team"] != safe_champ:
                value_champ = c
                break

    safe_sf = [e["team"] for e in sf_top[:3]]
    alternatives = [e for e in sf_top if e["team"] not in safe_sf]

    def _not_picking(pop_pct):
        return 11 - round(11 * pop_pct / 100)

    with open(planilla_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["RECOMENDACION PRODE MUNDIAL 2026"])
        writer.writerow([])
        writer.writerow(["ESTRATEGIA"])
        writer.writerow(["Categoria", "Pick Seguro", "Pick Value", "Rivales sin pick", "Explicacion"])
        writer.writerow([
            "Campeon",
            safe_champ,
            value_champ["team"] if value_champ else safe_champ,
            _not_picking(value_champ["estimated_popularity"]) if value_champ else 0,
            "El pick seguro tiene mayor probabilidad. El value pick da ventaja si acierta porque menos rivales lo tienen."
        ])
        writer.writerow([
            "Semifinalistas",
            " + ".join(safe_sf[:2]),
            alternatives[0]["team"] if alternatives else "N/A",
            _not_picking(alternatives[0]["estimated_popularity"]) if alternatives else 0,
            "Mezclar picks obvios + value. Si aciertas el value, sumas puntos que nadie mas tiene."
        ])
        writer.writerow([])

        writer.writerow(["═══ MULTIPLICADORES X2 RECOMENDADOS ═══"])
        writer.writerow(["#", "Partido", "Resultado", "Ganador", "P(Resultado)", "P(Exacto)", "EV Ganancia"])
        for i, r in enumerate(x2_ranking[:3], 1):
            writer.writerow([
                i,
                f"{r['team_a']} vs {r['team_b']}",
                r["predicted"],
                r["winner"],
                f"{r['p_result_pct']}%",
                f"{r['p_exact_pct']}%",
                r["ev_gain"],
            ])

        writer.writerow([])
        writer.writerow(["═══ RECOMENDACION CAMPEON ═══"])
        writer.writerow(["Rank", "Equipo", "Probabilidad Ajustada", "Factor de Diferenciacion", "Valor Ajustado"])
        for i, entry in enumerate(diff_analysis["champion"][:5], 1):
            writer.writerow([
                i,
                entry["team"],
                f"{entry['raw_score_pct']}%",
                entry["differentiation_boost"],
                entry["adjusted_value"],
            ])

        writer.writerow([])
        writer.writerow(["═══ RECOMENDACION SEMIFINALISTAS (4 picks) ═══"])
        writer.writerow(["Prioridad", "Equipo", "Probabilidad Ajustada", "Factor de Diferenciacion", "Valor Ajustado"])
        for i, entry in enumerate(diff_analysis["semifinalist"][:6], 1):
            writer.writerow([
                i,
                entry["team"],
                f"{entry['raw_score_pct']}%",
                entry["differentiation_boost"],
                entry["adjusted_value"],
            ])

        writer.writerow([])
        writer.writerow(["═══ RECOMENDACION GOLEADOR ═══"])
        writer.writerow(["Rank", "Jugador", "Equipo", "Tier", "Goles Raw", "Goles Ajustados"])
        for s in top_scorers[:10]:
            adj_str = f"{s['adj_goals']:.1f}"
            if s['adj_goals'] == int(s['adj_goals']):
                adj_str = str(int(s['adj_goals']))
            writer.writerow([s["rank"], s["player"], s["team"], s["tier"], s["raw_goals"], adj_str])

        writer.writerow([])
        writer.writerow(["═══ TOP 10 X2 (completo) ═══"])
        writer.writerow(["Rank", "Partido", "Resultado", "P(Resultado)", "P(Exacto)", "EV Ganancia"])
        for i, r in enumerate(x2_ranking[:10], 1):
            writer.writerow([
                i,
                f"{r['team_a']} vs {r['team_b']}",
                r["predicted"],
                f"{r['p_result_pct']}%",
                f"{r['p_exact_pct']}%",
                r["ev_gain"],
            ])

        writer.writerow([])
        writer.writerow(["═══ PROBABILIDAD CAMPEON (plausibility ajustada) ═══"])
        writer.writerow(["Rank", "Equipo", "Raw %", "Plausibilidad", "Ajustada %"])
        for i, entry in enumerate(rankings["champion"][:15], 1):
            writer.writerow([
                i,
                entry["team"],
                f"{entry['raw_pct']}%",
                entry["plausibility"],
                f"{entry['adj_pct']}%",
            ])

        writer.writerow([])
        writer.writerow(["═══ PROBABILIDAD SEMIFINALISTA (plausibility ajustada) ═══"])
        writer.writerow(["Rank", "Equipo", "Raw %", "Plausibilidad", "Ajustada %"])
        for i, entry in enumerate(rankings["semifinalist"][:15], 1):
            writer.writerow([
                i,
                entry["team"],
                f"{entry['raw_pct']}%",
                entry["plausibility"],
                f"{entry['adj_pct']}%",
            ])

    print(f"\n  Planilla guardada en: {planilla_path}")


# ─── Main ────────────────────────────────────────────────────────────────
def main():
    """Punto de entrada del optimizador."""
    import argparse
    parser = argparse.ArgumentParser(description="Optimizador PRODE Mundial 2026")
    parser.add_argument("--load", action="store_true",
                        help="Cargar datos MC previos (saltar Monte Carlo)")
    parser.add_argument("--seed", type=int, default=256,
                        help="Seed para simulacion base (default: 256)")
    args = parser.parse_args()

    print("=" * 70)
    print("  OPTIMIZADOR PRODE MUNDIAL 2026")
    print("=" * 70)

    # ── Load base simulation ──
    print(f"\n>>> Cargando simulacion base (seed {args.seed})...")
    from prode_mundial.bracket import run_full_simulation
    from io import StringIO
    from contextlib import redirect_stdout

    with redirect_stdout(StringIO()):
        gp, gr, kp = run_full_simulation(seed=args.seed)

    print(f"  Partidos de grupos: {len(gp)}")
    print(f"  Partidos KO: {len(kp)}")
    champion = kp[-1]["winner"]
    runnerup = kp[-1]["loser"]
    third = kp[-2]["winner"]
    print(f"  Campeon: {champion} | Sub: {runnerup} | 3ro: {third}")

    # ── X2 Analysis ──
    print("\n>>> ANALISIS DE MULTIPLICADORES X2...")
    x2_ranking = analyze_x2(group_predictions=gp)
    if x2_ranking:
        print(f"\n  Top 10 partidos para X2 (por valor esperado):")
        print(f"  {'Rank':5s} {'Partido':45s} {'Resultado':10s} {'P(R)':8s} {'P(E)':8s} {'EV+':8s}")
        print(f"  {'-'*84}")
        for i, r in enumerate(x2_ranking[:10], 1):
            match = f"{r['team_a']} vs {r['team_b']}"
            print(f"  {i:<5d} {match:45s} {r['predicted']:10s} {r['p_result_pct']:>6.1f}% {r['p_exact_pct']:>6.2f}% {r['ev_gain']:>7.3f}")

        print(f"\n  >>> RECOMENDACION: PONER X2 EN ESTOS 3 PARTIDOS:")
        for i, r in enumerate(x2_ranking[:3], 1):
            print(f"    X2 #{i}: {_safe(r['team_a'])} vs {_safe(r['team_b'])} ({_safe(r['predicted'])}, P={r['p_result_pct']}%)")

    # ── Monte Carlo ──
    if args.load:
        loaded = load_optimizer_data()
        if loaded and loaded["total_sims"] >= 100:
            print("\n>>> CARGANDO DATOS MC DESDE CACHE...")
            mc_data = {
                "champion": Counter(loaded["champion"]),
                "runnerup": Counter(loaded["runnerup"]),
                "semifinalist": Counter(loaded["semifinalist"]),
                "quarterfinalist": Counter(loaded["quarterfinalist"]),
                "total_sims": loaded["total_sims"],
            }
            print(f"  Cache cargado: {loaded['total_sims']} sims")
            rankings = loaded.get("rankings") or get_monte_carlo_rankings(mc_data)
        else:
            print("\n>>> Cache no valido. Ejecutando Monte Carlo...")
            mc_data = run_monte_carlo(iterations=1000)
            rankings = get_monte_carlo_rankings(mc_data)
            save_optimizer_data(mc_data, rankings)
    else:
        print("\n>>> ANALISIS MONTE CARLO...")
        mc_data = run_monte_carlo(iterations=1000)
        rankings = get_monte_carlo_rankings(mc_data)
        save_optimizer_data(mc_data, rankings)

    percentiles = compute_percentiles(mc_data)

    print(f"\n  >>> PROBABILIDADES DE CAMPEON (ajustadas por plausibilidad):")
    print(f"  {'Rank':5s} {'Equipo':25s} {'Raw %':8s} {'Plaus':8s} {'Adj %':8s}")
    print(f"  {'-'*54}")
    for i, entry in enumerate(rankings["champion"][:10], 1):
        print(f"  {i:<5d} {_safe(entry['team']):25s} {entry['raw_pct']:>6.2f}% {entry['plausibility']:>6.2f}  {entry['adj_pct']:>6.2f}%")

    print(f"\n  >>> PERCENTILES (P10/P50/P90) POR RONDA:")
    for rnd_display in ["champion", "semifinalist", "quarterfinalist"]:
        rnd_short = {"champion": "Campeon", "semifinalist": "Semifinalista", "quarterfinalist": "Cuartos"}[rnd_display]
        print(f"\n  {rnd_short} (P10/P50/P90):")
        pcts = percentiles[rnd_display]
        top3 = sorted(pcts.items(), key=lambda x: -x[1]["P50"])[:5]
        print(f"  {'Equipo':25s}  {'P10':8s}  {'P50':8s}  {'P90':8s}")
        print(f"  {'-'*50}")
        for team, p in top3:
            print(f"  {_safe(team):25s}  {p['P10']:>6.2f}%  {p['P50']:>6.2f}%  {p['P90']:>6.2f}%")

    print(f"\n  >>> PROBABILIDADES DE SEMIFINALISTA (ajustadas por plausibilidad):")
    print(f"  {'Rank':5s} {'Equipo':25s} {'Raw %':8s} {'Plaus':8s} {'Adj %':8s}")
    print(f"  {'-'*54}")
    for i, entry in enumerate(rankings["semifinalist"][:10], 1):
        print(f"  {i:<5d} {_safe(entry['team']):25s} {entry['raw_pct']:>6.2f}% {entry['plausibility']:>6.2f}  {entry['adj_pct']:>6.2f}%")

    # ── Diferenciación ──
    print("\n>>> ESTRATEGIA DE DIFERENCIACION...")
    diff = analyze_differentiation(rankings)

    print(f"\n  Mejores picks de CAMPEON considerando diferenciacion:")
    print(f"  {'Rank':5s} {'Equipo':25s} {'Prob%':8s} {'Popularidad':12s} {'Valor Ajust':12s}")
    print(f"  {'-'*62}")
    for i, entry in enumerate(diff["champion"][:5], 1):
        print(f"  {i:<5d} {_safe(entry['team']):25s} {entry['raw_score_pct']:>6.1f}% {entry['estimated_popularity']:>5.0f}%      {entry['adjusted_value']:>8.3f}")

    print(f"\n  Mejores picks de SEMIFINALISTA considerando diferenciacion:")
    print(f"  {'Rank':5s} {'Equipo':25s} {'Prob%':8s} {'Popularidad':12s} {'Valor Ajust':12s}")
    print(f"  {'-'*62}")
    for i, entry in enumerate(diff["semifinalist"][:6], 1):
        print(f"  {i:<5d} {_safe(entry['team']):25s} {entry['raw_score_pct']:>6.1f}% {entry['estimated_popularity']:>5.0f}%      {entry['adjusted_value']:>8.3f}")

    # ── Top Scorer ──
    print("\n>>> ANALISIS DE GOLEADOR...")
    top_scorers = analyze_top_scorer(gp, kp, top_n=15)
    print(f"\n  Top 10 goleadores (ajustado por tier):")
    print(f"  {'Rank':5s} {'Jugador':35s} {'Tier':15s} {'Goles Raw':9s} {'Goles Adj':9s}")
    print(f"  {'-'*75}")
    for s in top_scorers[:10]:
        adj_str = f"{s['adj_goals']:.1f}"
        if s['adj_goals'] == int(s['adj_goals']):
            adj_str = str(int(s['adj_goals']))
        print(f"  {s['rank']:<5d} {_safe(s['player']):35s} {_safe(s['tier']):15s} {s['raw_goals']:>4d}      {adj_str:>5s}")

    # ── Generate planilla ──
    print("\n>>> GENERANDO PLANILLA RECOMENDADA...")
    generar_planilla(x2_ranking, rankings, diff, top_scorers, gp, kp)

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  RESUMEN DE RECOMENDACIONES")
    print("=" * 70)

    champ_top = diff["champion"][:5] if diff["champion"] else []
    champ_all = diff["champion"][:15] if diff["champion"] else []
    sf_top = diff["semifinalist"][:6] if diff["semifinalist"] else []

    safe_champ = champ_top[0]["team"] if champ_top else "N/A"
    value_champ = None
    for c in champ_all:
        pop = c["estimated_popularity"]
        prob = c["raw_score_pct"]
        if pop < 60 and prob > 3.0:
            value_champ = c
            break
    if not value_champ:
        for c in champ_top:
            if c["team"] != safe_champ:
                value_champ = c
                break

    def others_not_picking(pop_pct):
        return 11 - round(11 * pop_pct / 100)

    print(f"\n  >>> X2 (3 multiplicadores - MATEMATICO, no cambiar):")
    for i, r in enumerate(x2_ranking[:3], 1):
        print(f"    {i}. {_safe(r['team_a']):20s} vs {_safe(r['team_b']):20s} -> {_safe(r['predicted']):5s} (confianza: {r['p_result_pct']}%)")

    print(f"\n  >>> CAMPEON:")
    print(f"    Pick seguro: {_safe(safe_champ):20s} ({champ_top[0]['raw_score_pct']}%)")
    if value_champ:
        not_pick = others_not_picking(value_champ["estimated_popularity"])
        print(f"    Pick value:  {_safe(value_champ['team']):20s} ({value_champ['raw_score_pct']}%, pop: {value_champ['estimated_popularity']}%)")
        if value_champ["team"] != safe_champ:
            print(f"    -> Si acierta, ~{not_pick} rivales NO lo tienen (ventaja)")
    if value_champ and value_champ["team"] == safe_champ:
        print(f"    Alternativa: Cualquiera del top 5 da buen VE.")

    print(f"\n  >>> SEMIFINALISTAS (4 picks):")
    safe_sf = [e["team"] for e in sf_top[:3]]
    alternatives = [e for e in sf_top if e["team"] not in safe_sf]
    print(f"    Pick seguro: {', '.join(_safe(t) for t in safe_sf)}")
    if alternatives:
        val_team = alternatives[0]["team"]
        val_pop = alternatives[0]["estimated_popularity"]
        print(f"    Pick value:  {_safe(val_team):20s} (prob: {alternatives[0]['raw_score_pct']}%, pop: {val_pop}%)")
        print(f"    Sugerencia: {', '.join(_safe(t) for t in safe_sf[:2])} + {_safe(val_team)} + otro value")
    print(f"    Estrategia: Mezcla 3 picks obvios + 1 value. Si acertás el value, ganás puntos que nadie mas tiene.")

    print(f"\n  >>> GOLEADOR:")
    if top_scorers:
        s = top_scorers[0]
        adj_str = f"{s['adj_goals']:.1f}"
        if s['adj_goals'] == int(s['adj_goals']):
            adj_str = str(int(s['adj_goals']))
        print(f"    Recomendado: {_safe(s['player']):30s} ({_safe(s['team']):15s}) - {adj_str:>3s} goles (tier: {_safe(s['tier'])})")
        if len(top_scorers) > 1:
            s2 = top_scorers[1]
            adj2 = f"{s2['adj_goals']:.1f}"
            if s2['adj_goals'] == int(s2['adj_goals']):
                adj2 = str(int(s2['adj_goals']))
            print(f"    Alternativa: {_safe(s2['player']):30s} ({_safe(s2['team']):15s}) - {adj2:>3s} goles (tier: {_safe(s2['tier'])})")

    print(f"\n{'='*70}")
    print("  Planilla completa guardada en: output/prode_recomendado.csv")
    print(f"{'='*70}")

    print(f"\n  PUNTOS ESPERADOS ESTIMADOS (solo X2):")
    x2_ev = sum(r["ev_gain"] for r in x2_ranking[:3])
    print(f"    X2: +{x2_ev:.2f} pts esperados sobre no usar X2")
    print(f"    Campeon: 6 pts si acertás")
    print(f"    Semifinalistas: hasta 16 pts")
    print(f"    Goleador: 4 pts si acertás")


if __name__ == "__main__":
    main()
