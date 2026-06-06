# -*- coding: utf-8 -*-
# Orquestador principal - Prediccion Mundial 2026

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bracket import run_full_simulation
from output import export_all

def main():
    seed = 256

    group_predictions, group_results, ko_predictions = run_full_simulation(seed=seed)

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
