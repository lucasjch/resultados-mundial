# -*- coding: utf-8 -*-
# Orquestador principal - Prediccion Mundial 2026

import sys
import os
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bracket import run_full_simulation
from output import export_all
from top_scorer import compute_top_scorers, get_player_team

def main():
    seed = 256
    top_scorer_only = False

    for arg in sys.argv[1:]:
        if arg == "--top" or arg == "--goleadores":
            top_scorer_only = True
        elif arg == "--seed" or arg == "-s":
            continue
        else:
            try:
                seed = int(arg)
            except ValueError:
                pass

    if "--seed" in sys.argv or "-s" in sys.argv:
        idx = sys.argv.index("--seed") if "--seed" in sys.argv else sys.argv.index("-s")
        if idx + 1 < len(sys.argv):
            try:
                seed = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if not top_scorer_only:
        print("=" * 70)
        print("  PREDICCION MUNDIAL 2026 - PRODE COMPLETO")
        print(f"  Seed: {seed}")
        print("=" * 70)
        group_predictions, group_results, ko_predictions = run_full_simulation(seed=seed)
    else:
        with redirect_stdout(StringIO()):
            group_predictions, group_results, ko_predictions = run_full_simulation(seed=seed)

    if not top_scorer_only:
        print()

    print("=" * 70)
    print("  TABLA DE GOLEADORES")
    print("=" * 70)
    top_scorers, _ = compute_top_scorers(group_predictions, ko_predictions, top_n=30)
    print(f"  {'Jugador':35s} {'Equipo':20s} {'Goles':>5s}")
    print("  " + "-" * 62)
    for rank, (player, goals) in enumerate(top_scorers, 1):
        if goals == 0:
            break
        team = get_player_team(player)[:20]
        print(f"  {rank:<3d} {player:35s} {team:20s} {goals:>3d}")

    if not top_scorer_only:
        print(f"\n{'='*70}")
        print("  EXPORTANDO RESULTADOS...")
        print(f"{'='*70}")
        export_all(group_predictions, group_results, ko_predictions)

        print(f"\n{'='*70}")
        print("  PREDICCION COMPLETADA CON EXITO!")
        print(f"{'='*70}")
        print(f"\n  Resultados disponibles en: output/")

    return group_predictions, group_results, ko_predictions

if __name__ == "__main__":
    main()
