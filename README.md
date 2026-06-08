# Prode Mundial 2026

Predicción determinista de los **135 partidos** del Mundial 2026 usando **18 factores ponderados** + **Poisson (1500 sims)** con corrección **Dixon-Coles τ**. Exporta a CSV y JSON.

## Quick Start

```bash
pip install -e .
python prode_mundial/main.py              # simulación completa
python prode_mundial/main.py --goleadores  # solo tabla de goleadores
pytest                                     # 129 tests
.\ejecutar.bat                             # menú interactivo
```

## Output

| Archivo | Contenido |
|---------|-----------|
| `output/fase_grupos.csv/json` | 72 partidos de grupos con scores y probabilidades |
| `output/tabla_posiciones.csv` | Posiciones finales por grupo |
| `output/eliminatorias.csv` | 63 partidos KO |
| `output/prode_completo.csv` | Prode completo en un archivo |
| `output/players.json` | 1245 jugadores enriquecidos |

## Dependencias

- Python 3.10+
- `requests` (única externa)
- `pyinstaller` (solo para compilar .exe)

## Licencia

MIT
