# -*- coding: utf-8 -*-
"""Orquestador principal: simula el torneo completo y exporta resultados."""

import sys
import os
import json
import argparse
import re
from contextlib import redirect_stdout
from io import StringIO
import time

_RE_ASCII = re.compile(r'[^\x20-\x7e]')

def _safe(text):
    """Limpia caracteres no ASCII para Windows."""
    return _RE_ASCII.sub('?', str(text))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prode_mundial.bracket import run_full_simulation
from prode_mundial.output import export_all
from prode_mundial.top_scorer import compute_top_scorers
from prode_mundial.real_results import load_real_results

def run_top_scorers(group_predictions, ko_predictions):
    """Imprime tabla de goleadores en consola."""
    top_scorers, _ = compute_top_scorers(group_predictions, ko_predictions, top_n=30)
    print("=" * 70)
    print("  TABLA DE GOLEADORES")
    print("=" * 70)
    print(f"  {'Jugador':35s} {'Equipo':20s} {'Goles':>5s}")
    print("  " + "-" * 62)
    for rank, (player, team, goals) in enumerate(top_scorers, 1):
        if goals == 0:
            break
        print(f"  {rank:<3d} {_safe(player):35s} {_safe(team):20s} {goals:>3d}")
    return top_scorers

def main():
    """Punto de entrada: flag --goleadores."""
    parser = argparse.ArgumentParser(description="Prode Mundial 2026")
    parser.add_argument("--goleadores", "--top", action="store_true", help="Solo tabla de goleadores")
    args = parser.parse_args()

    top_scorer_only = args.goleadores
    real_results = None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, "output", "real_results.json")
    if os.path.exists(results_path):
        real_results = load_real_results(results_path)
        if real_results:
            print(f"  Cargados {len(real_results)} resultados reales desde output/real_results.json")
            for rr in real_results:
                print(f"    {rr['team_a']} {rr['score_a']}-{rr['score_b']} {rr['team_b']}")

    if not top_scorer_only:
        print("Simulación completa (1500 simulaciones por partido)...")
        print()

    with redirect_stdout(StringIO()) if top_scorer_only else nullcontext():
        group_predictions, group_results, ko_predictions = run_full_simulation(real_results=real_results)

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
    """Context manager nulo para redirect opcional."""
    class NullContext:
        def __enter__(self): pass
        def __exit__(self, *a): pass
    return NullContext()

if __name__ == "__main__":
    main()
