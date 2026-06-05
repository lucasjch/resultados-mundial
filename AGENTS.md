# Prode Mundial 2026 — AGENTS.md

Memoria persistente del proyecto. opencode carga esto automáticamente al iniciar cada sesión.

---

## Objetivo

Script Python que analiza los 135 partidos del Mundial 2026 y predice resultados para completar un prode. Exporta a CSV y JSON.

## Tech Stack

- Python 3.14+ (standard library: json, re, csv, os, sys, math, random, collections, itertools, time)
- `requests` (única dependencia externa)
- LSP: `python-lsp-server` (pylsp) + `pylint`
- Config LSP en `opencode.jsonc` (`"lsp": true`)

## Estructura

```
prode_mundial/
├── scraper.py        # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py           # Datos de equipos, sedes, fixture, bases operativas
├── predictor.py      # Motor de 10 factores ponderados + simulación Poisson
├── bracket.py        # Bracket oficial 2026 (R32, R16, QF, SF, 3°, Final)
├── output.py         # Exportación CSV/JSON
├── main.py           # Orquestador principal
├── wikiscraper.py    # Scraper individual de Wikipedia vía API
└── output/
    ├── players.json          # 1245 jugadores (enriquecido vía wikiscraper)
    ├── wiki_cache.json       # Caché de Wikipedia scraping
    ├── fase_grupos.csv/json  # Partidos de grupos
    ├── tabla_posiciones.csv  # Posiciones finales
    ├── eliminatorias.csv     # Llaves KO
    └── prode_completo.csv    # Prode completo (135 partidos)
```

## Plan de Fases

| # | Fase | Estado |
|---|------|--------|
| 1 | Ejecutar wikiscraper.py (1112/1245 jugadores) | ✅ Completado |
| 2 | Decidir fuente de asistencias | ⬜ Pendiente |
| 3 | Integrar stats individuales como factores en predictor.py | ⬜ Pendiente |
| 4 | Arreglar modelo de predicción (pesos, redundancias, fórmula) | ⬜ Pendiente |
| 5 | Revisar predicciones Grupo A con factores mejorados | ⬜ Pendiente |
| 6 | Ejecutar simulación completa (main.py) | ⬜ Pendiente |

## Decisiones Tomadas

1. **Wikiscraper**: Se agregó checkpoint incremental cada 50 jugadores para evitar perder progreso en timeouts.
2. **UTF-8 fix**: En Windows requiere `$env:PYTHONIOENCODING='utf-8'` antes de ejecutar wikiscraper.
3. **LSP**: `python-lsp-server` (pylsp) instalado globalmente. `opencode.jsonc` con `"lsp": true` en la raíz.
4. **Repositorio**: `https://github.com/lucasjch/resultados-mundial.git`, branch `master`.

## Correcciones Pendientes en predictor.py (discutido con Gemini)

### Problemas identificados:

1. **Pesos suman 110%**: `30+15+12+10+8+6+6+4+4+5+10 = 110%`. Hay que redistribuir a 100%.
2. **Redundancia (multicolinealidad)**: `team_strength` ya incluye `market_value` internamente, pero después se pondera `market_value` como factor separado al 15%. También `fanbase` se solapa con `home_advantage`.
3. **Fórmula de goles esperados**: No cruza ataque vs defensa. Actual: `λ_A = goals_scored_avg_A + (total_diff/30) × 1.2`. Debería ser: `base_A = (goals_scored_avg_A + goals_conceded_avg_B) / 2`.
4. **Randomness**: Está dentro de la matriz de pesos (10%) cuando debería ser un término aditivo independiente.

### Pesos sugeridos (corregidos al 100%):

| Factor | Peso | Nota |
|--------|------|------|
| team_strength | 35% | Sacar market_value de adentro |
| market_value | 20% | Ya no duplicado |
| home_advantage | 12% | Absorbe fanbase |
| climate | 8% | |
| travel | 5% | |
| history | 5% | |
| morale | 5% | |
| age_penalty | 5% | |
| foreign_pct | 5% | |
| randomness | — | Término aditivo, no peso |

### Nueva fórmula de goles esperados:
```
total_diff = Σ(factor_i × peso_i)   # sin randomness
random_factor = random.gauss(0, 0.7) * 10
total_diff += random_factor
total_diff_scaled = total_diff / 100  # normalizado

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = base_a * (1 + total_diff_scaled)
λ_b = base_b * (1 - total_diff_scaled)
```

## Seed

`seed = 42` en `main.py`. Resultado actual: Germany campeón, Brazil subcampeón, Portugal 3°.

## Comandos Útiles

```powershell
# Ejecutar wikiscraper
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/wikiscraper.py

# Ejecutar simulación completa
python prode_mundial/main.py

# Git push
git add -A; git commit -m "mensaje"; git push origin master
```
