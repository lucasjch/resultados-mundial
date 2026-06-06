# -*- coding: utf-8 -*-
# Visualizador de predicciones desde archivos de salida

import json
import os
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def _load_json(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _fmt_score(p):
    return f"{p['score_a']}-{p['score_b']}"

def _fmt_xg(p):
    return f"xG {p.get('expected_goals_a','?')}-{p.get('expected_goals_b','?')}"

def _fmt_result(p):
    conf = p.get("confidence", 0)
    if isinstance(conf, (int, float)):
        return f"{p['winner']} ({conf:.0f}%)"
    return str(p["winner"])

def _load_group_tables():
    from data import GROUPS
    data = _load_json("fase_grupos.json")
    if not data:
        return None
    tables = {}
    for g in GROUPS:
        matches = [p for p in data if p["round"] == f"Group {g}"]
        table = {}
        for p in matches:
            for team in [p["team_a"], p["team_b"]]:
                if team not in table:
                    table[team] = {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0}
            a, b = p["team_a"], p["team_b"]
            ga, gb = p["score_a"], p["score_b"]
            table[a]["gf"] += ga
            table[a]["ga"] += gb
            table[b]["gf"] += gb
            table[b]["ga"] += ga
            table[a]["gd"] = table[a]["gf"] - table[a]["ga"]
            table[b]["gd"] = table[b]["gf"] - table[b]["ga"]
            if ga > gb:
                table[a]["pts"] += 3
                table[a]["w"] += 1
                table[b]["l"] += 1
            elif gb > ga:
                table[b]["pts"] += 3
                table[b]["w"] += 1
                table[a]["l"] += 1
            else:
                table[a]["pts"] += 1
                table[b]["pts"] += 1
                table[a]["d"] += 1
                table[b]["d"] += 1
        sorted_teams = sorted(table.items(), key=lambda x: (-x[1]["pts"], -x[1]["gd"], -x[1]["gf"]))
        tables[g] = sorted_teams
    return tables

def show_all_groups():
    data = _load_json("fase_grupos.json")
    if not data:
        print(" No hay predicciones de fase de grupos.")
        print(" Ejecute primero una simulacion (opcion 1 o 2).")
        return
    groups = {}
    for p in data:
        g = p["round"].replace("Group ", "")
        groups.setdefault(g, []).append(p)
    for g in sorted(groups.keys()):
        show_group(g, data)

def show_group(letter, data=None):
    if data is None:
        data = _load_json("fase_grupos.json")
    if not data:
        print(" No hay predicciones de fase de grupos.")
        print(" Ejecute primero una simulacion (opcion 1 o 2).")
        return
    key = f"Group {letter.upper()}"
    matches = [p for p in data if p["round"] == key]
    if not matches:
        print(f" Grupo {letter.upper()} no encontrado.")
        return
    matches.sort(key=lambda m: m.get("date", ""))
    print(f"\n  GRUPO {letter.upper()}")
    print(f"  {'='*60}")
    for p in matches:
        print(f"  {p['team_a']:25s} {_fmt_score(p):5s} {p['team_b']:25s}")
        print(f"  {'':25s} {_fmt_xg(p):14s}  {_fmt_result(p)}")
        print()

def show_tabla_posiciones():
    tables = _load_group_tables()
    if not tables:
        print(" No hay predicciones de fase de grupos.")
        print(" Ejecute primero una simulacion (opcion 1 o 2).")
        return
    print()
    for g in sorted(tables.keys()):
        print(f"  GRUPO {g}")
        print(f"  {'':3s} {'Equipo':25s} {'Pts':>4s} {'W':>3s} {'D':>3s} {'L':>3s} {'GF':>3s} {'GC':>3s} {'GD':>4s}")
        print(f"  {'':3s} {'-'*25} {'-'*4} {'-'*3} {'-'*3} {'-'*3} {'-'*3} {'-'*3} {'-'*4}")
        for i, (team, d) in enumerate(tables[g]):
            print(f"  [{i+1}] {team:25s} {d['pts']:4d} {d['w']:3d} {d['d']:3d} {d['l']:3d} {d['gf']:3d} {d['ga']:3d} {d['gd']:+4d}")
        print()

def show_all_playoffs():
    data = _load_json("eliminatorias.json")
    if not data:
        print(" No hay predicciones de playoffs.")
        print(" Ejecute primero una simulacion (opcion 1 o 2).")
        return
    labels = {"R32": "RONDA DE 32AVOS", "R16": "OCTAVOS DE FINAL",
              "QF": "CUARTOS DE FINAL", "SF": "SEMIFINALES",
              "3°": "TERCER PUESTO", "Final": "FINAL"}
    for r in ["R32", "R16", "QF", "SF", "3°", "Final"]:
        matches = [p for p in data if p["round"] == r]
        if not matches:
            continue
        print(f"\n  {labels.get(r, r)}")
        print(f"  {'='*60}")
        for p in matches:
            print(f"  {p['team_a']:25s} {_fmt_score(p):5s} {p['team_b']:25s}")
            print(f"  {'':25s} {_fmt_xg(p):14s}  {_fmt_result(p)}")
            print()

def show_round(round_name):
    data = _load_json("eliminatorias.json")
    if not data:
        print(" No hay predicciones de playoffs.")
        print(" Ejecute primero una simulacion (opcion 1 o 2).")
        return
    labels = {"R32": "RONDA DE 32AVOS", "R16": "OCTAVOS DE FINAL",
              "QF": "CUARTOS DE FINAL", "SF": "SEMIFINALES",
              "3°": "TERCER PUESTO", "Final": "FINAL"}
    if round_name not in labels:
        print(f" Ronda '{round_name}' no valida. Opciones: {', '.join(labels.keys())}")
        return
    matches = [p for p in data if p["round"] == round_name]
    if not matches:
        print(f" No hay partidos para ronda '{round_name}'.")
        return
    print(f"\n  {labels[round_name]}")
    print(f"  {'='*60}")
    for p in matches:
        print(f"  {p['team_a']:25s} {_fmt_score(p):5s} {p['team_b']:25s}")
        print(f"  {'':25s} {_fmt_xg(p):14s}  {_fmt_result(p)}")
        print()

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(" Uso: python display.py [opcion]")
        print("")
        print(" Opciones:")
        print("  --grupos           Mostrar todos los grupos")
        print("  --grupo <A-L>      Mostrar un grupo especifico")
        print("  --tabla            Mostrar tabla de posiciones")
        print("  --playoffs         Mostrar todas las eliminatorias")
        print("  --ronda <round>    Mostrar una ronda (R32|R16|QF|SF|3°|Final)")
        sys.exit(1)

    if args[0] == "--grupos":
        show_all_groups()
    elif args[0] == "--grupo" and len(args) > 1:
        show_group(args[1])
    elif args[0] == "--tabla":
        show_tabla_posiciones()
    elif args[0] == "--playoffs":
        show_all_playoffs()
    elif args[0] == "--ronda" and len(args) > 1:
        show_round(args[1])
    else:
        print(f" Opcion no reconocida: {' '.join(args)}")
        sys.exit(1)
