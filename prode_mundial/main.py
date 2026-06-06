# -*- coding: utf-8 -*-
# Orquestador principal - Prediccion Mundial 2026

import sys
import os
import argparse
from contextlib import redirect_stdout
from io import StringIO
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bracket import run_full_simulation, ensemble_simulation
from output import export_all
from top_scorer import compute_top_scorers

def run_top_scorers(group_predictions, ko_predictions):
    top_scorers, _ = compute_top_scorers(group_predictions, ko_predictions, top_n=30)
    print("=" * 70)
    print("  TABLA DE GOLEADORES")
    print("=" * 70)
    print(f"  {'Jugador':35s} {'Equipo':20s} {'Goles':>5s}")
    print("  " + "-" * 62)
    for rank, (player, team, goals) in enumerate(top_scorers, 1):
        if goals == 0:
            break
        print(f"  {rank:<3d} {player:35s} {team:20s} {goals:>3d}")
    return top_scorers

def main():
    parser = argparse.ArgumentParser(description="Prode Mundial 2026")
    parser.add_argument("seed", nargs="?", type=int, default=None, help="Seed (default: ensemble 100 seeds)")
    parser.add_argument("--seed", "-s", type=int, dest="seed_flag", help="Seed (alternativo)")
    parser.add_argument("--goleadores", "--top", action="store_true", help="Solo tabla de goleadores")
    parser.add_argument("--no-ensemble", action="store_true", help="Usar seed unica en vez de ensemble")
    args = parser.parse_args()

    seed = args.seed if args.seed_flag is None else args.seed_flag
    single_seed = args.no_ensemble or seed is not None
    top_scorer_only = args.goleadores

    if single_seed:
        s = seed if seed is not None else 256
        if not top_scorer_only:
            print(f"Seed: {s}")
        with redirect_stdout(StringIO()) if top_scorer_only else nullcontext():
            group_predictions, group_results, ko_predictions = run_full_simulation(seed=s)
    else:
        n = 100
        if not top_scorer_only:
            print(f"Ensemble {n} seeds...")
            group_predictions, group_results, ko_predictions, _ = ensemble_simulation(n_seeds=n)
        else:
            with redirect_stdout(StringIO()):
                group_predictions, group_results, ko_predictions, _ = ensemble_simulation(n_seeds=n)

    if not top_scorer_only:
        print()
    run_top_scorers(group_predictions, ko_predictions)

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

def nullcontext():
    class NullContext:
        def __enter__(self): pass
        def __exit__(self, *a): pass
    return NullContext()

if __name__ == "__main__":
    main()
