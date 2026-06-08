# -*- coding: utf-8 -*-
"""Exportacion a CSV y JSON de los resultados de la simulacion."""

import csv
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def ensure_output_dir():
    """Crea directorio output si no existe."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_group_stage_csv(predictions, filepath=None):
    """Exporta partidos de grupos a CSV."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "fase_grupos.csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Grupo", "Fecha", "Hora", "Sede", "Pais",
            "Equipo Local", "Equipo Visitante",
            "Goles Local", "Goles Visitante",
            "Goles Esp. Local", "Goles Esp. Visitante",
            "Ganador", "Probabilidad Local(%)", "Probabilidad Empate(%)",
            "Probabilidad Visitante(%)", "Confianza(%)",
        ])
        for p in predictions:
            writer.writerow([
                p["round"].split()[-1] if "Group" in p["round"] else p["round"],
                p.get("date", ""),
                p.get("time", ""),
                p["venue"], p["venue_country"],
                p["team_a"], p["team_b"],
                p["score_a"], p["score_b"],
                p.get("expected_goals_a", ""), p.get("expected_goals_b", ""),
                p["winner"],
                p["prob_a_win"], p["prob_draw"], p["prob_b_win"],
                p["confidence"],
            ])
    print(f"  -> CSV exportado: {filepath}")

def export_group_stage_json(predictions, filepath=None):
    """Exporta partidos de grupos a JSON."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "fase_grupos.json")

    data = []
    for p in predictions:
        data.append({
            "round": p["round"],
            "date": p.get("date", ""),
            "time": p.get("time", ""),
            "venue": p["venue"],
            "venue_country": p["venue_country"],
            "team_a": p["team_a"],
            "team_b": p["team_b"],
            "score_a": p["score_a"],
            "score_b": p["score_b"],
            "expected_goals_a": p.get("expected_goals_a", ""),
            "expected_goals_b": p.get("expected_goals_b", ""),
            "winner": p["winner"],
            "probabilities": {
                "a_win": p["prob_a_win"],
                "draw": p["prob_draw"],
                "b_win": p["prob_b_win"],
            },
            "confidence": p["confidence"],
            "factors": p["factors"],
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> JSON exportado: {filepath}")

def export_group_tables_csv(group_results, filepath=None):
    """Exporta tabla de posiciones por grupo a CSV."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "tabla_posiciones.csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Grupo", "Posicion", "Equipo",
            "Puntos", "PG", "PE", "PP",
            "GF", "GC", "DG",
        ])
        for g, teams in group_results.items():
            for i, (team, data) in enumerate(teams):
                writer.writerow([
                    g, i + 1, team,
                    data["pts"], data["w"], data["d"], data["l"],
                    data["gf"], data["ga"], data["gd"],
                ])
    print(f"  -> CSV exportado: {filepath}")

def export_knockout_csv(predictions, filepath=None):
    """Exporta llaves KO a CSV."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "eliminatorias.csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Ronda", "Fecha", "Hora", "Sede",
            "Equipo A", "Equipo B",
            "Goles A", "Goles B",
            "Goles Esp. A", "Goles Esp. B",
            "Ganador", "Prob A(%)", "Prob Emp(%)", "Prob B(%)", "Confianza(%)",
        ])
        for p in predictions:
            writer.writerow([
                p["round"], p.get("date", ""), p.get("time", ""),
                p["venue"],
                p["team_a"], p["team_b"],
                p["score_a"], p["score_b"],
                p.get("expected_goals_a", ""), p.get("expected_goals_b", ""),
                p["winner"],
                p["prob_a_win"], p["prob_draw"], p["prob_b_win"],
                p["confidence"],
            ])
    print(f"  -> CSV exportado: {filepath}")

def export_knockout_json(predictions, filepath=None):
    """Exporta llaves KO a JSON."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "eliminatorias.json")

    data = []
    for p in predictions:
        data.append({
            "round": p["round"],
            "date": p.get("date", ""),
            "time": p.get("time", ""),
            "venue": p["venue"],
            "team_a": p["team_a"],
            "team_b": p["team_b"],
            "score_a": p["score_a"],
            "score_b": p["score_b"],
            "expected_goals_a": p.get("expected_goals_a", ""),
            "expected_goals_b": p.get("expected_goals_b", ""),
            "winner": p["winner"],
            "probabilities": {
                "a_win": p["prob_a_win"],
                "draw": p["prob_draw"],
                "b_win": p["prob_b_win"],
            },
            "confidence": p["confidence"],
            "factors": p["factors"],
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> JSON exportado: {filepath}")

def export_full_prode_csv(group_predictions, group_results, ko_predictions, filepath=None):
    """Exporta prode completo en un solo CSV."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "prode_completo.csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow(["PREDICCION COMPLETA MUNDIAL 2026"])
        writer.writerow([])

        writer.writerow(["FASE DE GRUPOS"])
        writer.writerow(["Grupo", "Fecha", "Hora", "Sede", "Local", "Visitante", "Resultado", "Goles Esp. Local", "Goles Esp. Visit.", "Ganador", "Prob Local(%)", "Prob Emp(%)", "Prob Visit(%)", "Confianza"])
        for p in group_predictions:
            g = p["round"].split()[-1] if "Group" in p["round"] else p["round"]
            score = f"{p['score_a']}-{p['score_b']}"
            writer.writerow([g, p.get("date",""), p.get("time",""), p["venue"],
                           p["team_a"], p["team_b"], score,
                           p.get("expected_goals_a", ""), p.get("expected_goals_b", ""),
                           p["winner"],
                           p["prob_a_win"], p["prob_draw"], p["prob_b_win"],
                           f"{p['confidence']:.0f}%"])

        writer.writerow([])
        writer.writerow(["TABLA DE POSICIONES"])
        writer.writerow(["Grupo", "Pos", "Equipo", "Pts", "PG", "PE", "PP", "GF", "GC", "DG"])
        for g, teams in group_results.items():
            for i, (team, data) in enumerate(teams):
                writer.writerow([g, i+1, team, data["pts"], data["w"], data["d"], data["l"],
                               data["gf"], data["ga"], data["gd"]])

        writer.writerow([])
        writer.writerow(["ELIMINATORIAS"])
        writer.writerow(["Ronda", "Fecha", "Sede", "Partido", "Resultado", "Goles Esp. A", "Goles Esp. B", "Ganador", "Prob A(%)", "Prob Emp(%)", "Prob B(%)", "Confianza"])
        for p in ko_predictions:
            match_str = f"{p['team_a']} vs {p['team_b']}"
            score = f"{p['score_a']}-{p['score_b']}"
            writer.writerow([p["round"], p.get("date",""), p["venue"], match_str, score,
                           p.get("expected_goals_a", ""), p.get("expected_goals_b", ""),
                           p["winner"],
                           p["prob_a_win"], p["prob_draw"], p["prob_b_win"],
                           f"{p['confidence']:.0f}%"])

        writer.writerow([])
        writer.writerow(["RESULTADOS FINALES"])
        writer.writerow(["Campeon:", ko_predictions[-1]["winner"] if ko_predictions else "N/A"])
        writer.writerow(["Subcampeon:", ko_predictions[-1]["loser"] if ko_predictions else "N/A"])
        writer.writerow(["3er Puesto:", ko_predictions[-2]["winner"] if len(ko_predictions) >= 2 else "N/A"])

    print(f"\n  PRODE COMPLETO exportado: {filepath}")

def export_group_tables_json(group_results, filepath=None):
    """Exporta tabla de posiciones por grupo a JSON."""
    ensure_output_dir()
    if filepath is None:
        filepath = os.path.join(OUTPUT_DIR, "tabla_posiciones.json")
    data = {}
    for g, teams in group_results.items():
        rows = []
        for i, (team, d) in enumerate(teams):
            rows.append({
                "position": i + 1,
                "team": team,
                "pts": d["pts"],
                "w": d["w"],
                "d": d["d"],
                "l": d["l"],
                "gf": d["gf"],
                "ga": d["ga"],
                "gd": d["gd"],
            })
        data[g] = rows
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> JSON exportado: {filepath}")

def export_all(group_predictions, group_results, ko_predictions):
    """Exporta todos los formatos de salida."""
    export_group_stage_csv(group_predictions)
    export_group_stage_json(group_predictions)
    export_group_tables_csv(group_results)
    export_group_tables_json(group_results)
    export_knockout_csv(ko_predictions)
    export_knockout_json(ko_predictions)
    export_full_prode_csv(group_predictions, group_results, ko_predictions)
