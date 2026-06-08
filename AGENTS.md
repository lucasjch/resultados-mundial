# Prode Mundial 2026 — AGENTS.md

<!-- markdownlint-disable MD013 -->

Memoria persistente del proyecto. opencode carga esto automáticamente al iniciar cada sesión.

---

## Objetivo

Script Python que analiza los 135 partidos del Mundial 2026 y predice resultados
para completar un prode. Exporta a CSV y JSON.

## Tech Stack

- Python 3.14+ (standard library: json, re, csv, os, sys, math, random, collections, itertools, time)
- `requests` (única dependencia externa)
- LSP: `python-lsp-server` (pylsp) + `pylint`
- Config LSP en `opencode.jsonc` (`"lsp": true`)
- Build: `pyproject.toml` (setuptools) + `prode_mundial/__init__.py`
- CI: `.github/workflows/ci.yml` (pytest + pylint + smoke test)
- Code quality: `.pylintrc`, `.editorconfig`, `.gitignore`

## Estructura

```text
prode_mundial/
├── scraper.py           # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py              # Datos de equipos, sedes, fixture, bases operativas, haversine, card rates
├── predictor.py         # Motor de 18 factores ponderados + simulación Poisson + Dixon-Coles τ
├── stats_scraper.py     # Scraper de estadísticas individuales (Transfermarkt API)
├── bracket.py           # Bracket oficial 2026 + H2H tiebreaker + safety net KO
├── output.py            # Exportación CSV/JSON
├── main.py              # Orquestador principal
├── top_scorer.py        # Distribución de goles a jugadores (top goleador)
├── wikiscraper.py       # Scraper individual de Wikipedia vía API
├── __init__.py          # Package init (v0.1.0)
├── tests/
│   ├── test_predictor.py   # 59 tests (46 original + 13 Dixon-Coles τ)
│   ├── test_bracket.py     # 27 tests
│   ├── test_data.py        # 22 tests
│   ├── test_top_scorer.py  # 11 tests
│   └── test_output.py      # 11 tests
├── output/
│   ├── players.json              # 1245 jugadores
│   ├── wiki_cache.json           # Caché de Wikipedia scraping
│   ├── tm_stats_cache.json       # Caché de Transfermarkt stats
│   ├── fase_grupos.csv/json      # Partidos de grupos
│   ├── tabla_posiciones.csv      # Posiciones finales
│   ├── eliminatorias.csv         # Llaves KO
│   └── prode_completo.csv        # Prode completo (135 partidos)
```

## Plan de Fases

| #  | Fase | Estado |
|----|------|--------|
| 1  | Ejecutar wikiscraper.py (1112/1245 jugadores) | ✅ Completado |
| 2  | Decidir fuente de asistencias | ✅ Completado |
| 3  | Integrar stats individuales como factores | ✅ Completado |
| 4  | Arreglar modelo (pesos, redundancias, fórmula) | ✅ Completado |
| 5  | Revisar predicciones Grupo A | ✅ Completado |
| 6  | Ejecutar simulación completa | ✅ Completado |
| —  | **Bloque A**: Fix fixture/venue bugs | ✅ Completado |
| —  | **Bloque B**: Market Value Parser + Estimaciones | ✅ Completado |
| —  | **Bloque C**: Team Data Calibrations + Overrides | ✅ Completado |
| —  | **Bloque D**: Actualizar temperaturas de sedes | ✅ Completado |
| —  | **Bloque E**: Ajustar modelo (form/goals, player_stats, is_neutral) | ✅ Completado |
| —  | **Bloque F**: Re-ejecutar stats_scraper + main.py | ✅ Completado |
| —  | **Bloque G**: 4 nuevos factores | ✅ Completado |
| —  | **Bloque H**: Fair Play + FIFA 2026 tiebreaker cascade + safety net KO | ✅ Completado |
| —  | **Bloque I**: Fix probabilidades (noise removal) + confidence del winner real | ✅ Completado |
| —  | **Bloque J**: Top scorer + ejecutar.bat menú interactivo | ✅ Completado |
| —  | **Bloque K**: Ensemble 100 seeds + upset correction + factor odds | ✅ Completado |
| —  | **Bloque L**: Optimización completa de factores (4 nuevos, 2 eliminados, mejoras) | ✅ Completado |
| —  | **Bloque M**: Eliminar ensemble, score promedio de 1500 sims | ✅ Completado |
| —  | **Bloque N**: Factor Stakes (presión de 3ª fecha) + varianza MD3 | ✅ Completado |
| —  | **Fase Tests**: 4 nuevos test files (bracket/data/top_scorer/output) | ✅ Completado |
| —  | **Dixon-Coles τ**: Corrección de empates (ρ=-0.15, joint dist 16×16) | ✅ Completado |
| —  | **Fase 4a**: pyproject.toml + __init__.py (package installable) | ✅ Completado |
| —  | **Fase 4b**: Retry + exponential backoff en scraper.py y stats_scraper.py | ✅ Completado |

## Decisiones Tomadas

1. **Wikiscraper**: Se agregó checkpoint incremental cada 50 jugadores para evitar
   perder progreso en timeouts.
2. **UTF-8 fix**: En Windows requiere `$env:PYTHONIOENCODING='utf-8'` antes de
   ejecutar scripts Python con caracteres UTF-8.
3. **LSP**: `python-lsp-server` (pylsp) instalado globalmente. `opencode.jsonc`
   con `"lsp": true` en la raíz.
4. **Repositorio**: `https://github.com/lucasjch/resultados-mundial.git`,
   branch `master`.
5. **Fuente de asistencias → Transfermarkt API**: La API
   `tmapi-alpha.transfermarkt.technology` devuelve stats detalladas por partido
   (goles, asistencias, minutos) sin rate limit. Reemplaza FBref (bloqueado por
   Cloudflare).
6. **Transfermarkt endpoints**: `/quickselect/teams/FIWC` → 48 equipos,
   `/quickselect/players/{teamId}` → jugadores,
   `/player/{playerId}/performance-game` → stats por temporada.
7. **Fair Play card simulation**: Tarjetas generadas por partido vía Poisson
   (yellow_rate confederation-level) + Bernoulli (red_rate). FP points según
   Artículo 13 (−1 por amarilla, −4 por roja directa).
8. **FIFA 2026 tiebreaker cascade (Artículo 13)**: H2H pts → H2H GD → H2H GF →
   GD global → GF global → Fair Play → Ranking FIFA. Aplicado en `_sort_group()`
   para grupos y en `determine_qualified()` para mejores terceros.
9. **Safety net KO doble capa**: `predict_match` resuelve empates en KO via
   morale + squad_depth + gauss noise; `simulate_knockout_round` tiene fallback
   por ranking FIFA si aún hay "Empate".
10. **Haversine centralizada**: Única implementación en `data.py`; predictor y
    bracket importan desde ahí — DRY, sin código duplicado.
11. **`_PLAYERS_CACHE`**: Carga lazy de `players.json` (1245 jugadores) para
    evitar 135 lecturas de disco durante predict_match.
12. **Pre-carga de team data**: `get_team()` llamado 1 vez al inicio de
    `predict_match`; los 8 factores que lo usaban internamente ahora reciben
    dicts pre-cargados.
13. **Dead code eliminado**: `SequenceMatcher` import, `_load_team_players()`,
    `_haversine` local en predictor y bracket, import de `calculate_team_strength`
    en bracket.
14. **1000 sims sin ruido extra**: Las probabilidades se calculan directamente
    de Poisson(λ determinista). El `random.gauss(0, 0.7)*10` fue eliminado de los
    1000 sims. El λ ya captura toda la varianza del modelo — agregar ruido extra
    degradaba la precisión de las probabilidades.
15. **Confidence = probabilidad del winner real**: Antes usaba `max(prob_a_win,
    prob_b_win, prob_draw)` que mostraba la probabilidad del resultado más probable
    (no necesariamente del ganador). Ahora `confidence = prob_winner * 100`, donde
    `prob_winner` es la probabilidad del equipo que efectivamente ganó según el
    score Poisson.
16. **Top scorer deterministic seed**: `random.seed(0)` dentro de
    `compute_top_scorers()` para distribución reproducible de goles entre
    jugadores, SIN afectar los resultados de los partidos (post-simulación).
17. **`players.json` es `{team: [players]}`**: No `{player_name: data}`. Requiere
    `get_player_team()` para lookup inverso de equipo → jugador.
18. **ejecutar.bat en raíz**: Menú interactivo PowerShell/.bat portable. No
    requiere instalación en PATH.
19. **Score promedio de 1500 sims**: El score final de cada partido es
    `round(sum_a / 1500, round(sum_b / 1500))` — promedio de 1500 Poisson draws.
20. **LSP instalado en sesión 2026-06-08**: Se instaló `python-lsp-server` 1.14.0
21. **Dixon-Coles τ (ρ = -0.15)**: Aumenta probabilidad de empates 0-0 y 1-1 (τ > 1),
    disminuye 1-0/0-1 (τ < 1); clip `max(0, ·)` evita τ negativo en λ > 6.67.
    `__build_joint_dist()` genera tabla 16×16, y `random.choices(k=1500)` muestrea
    batch — más rápido que 1500 Poisson independientes.
22. **Variance-boost saltea τ**: El ruido gaussiano(0, 0.15) en MD3 contender matches
    ya introduce aproximación; mantener Poisson independiente evita rebuild costoso.
23. **`pyproject.toml`**: Build con setuptools, entry point `prode-mundial`, pytest
    config con `testpaths` + `pythonpath`. Permite `pip install -e .` y `pytest`.
24. **Retry exponential backoff**: `scraper.py` usa `_fetch_with_retry()` con 4
    reintentos (delay 2s/4s/8s/16s) para `urllib.error.URLError`/`socket.timeout`.
    `stats_scraper.py` `_get()` reintenta 3 veces con timeout separado connect=10s/read=30s.

## Correcciones Aplicadas en predictor.py (Fase 4 + Bloque E)

### Problemas solucionados (Fase 4)

1. **Pesos sumaban 110%** → Redistribuidos a 100%, eliminados `fanbase` y
   `randomness` de los pesos.
2. **Redundancia (multicolinealidad)** → `team_strength` ya NO incluye
   `market_value`. `fanbase` eliminado y absorbido por `home_advantage`.
3. **Fórmula de goles esperados** → Ahora cruza ataque vs defensa:
   `base_A = (goals_scored_avg_A + goals_conceded_avg_B) / 2`.
4. **Randomness eliminado** → `random.gauss(0, 0.7) * 10` ya no se suma a
   `total_diff`. El λ determinista captura toda la varianza del modelo sin
   ruido extra que degradaba las probabilidades.
5. **Nuevo factor**: `player_stats` (10%) que agrega goles+asistencias promedio
   por plantilla desde Transfermarkt.

### Cambios Bloque E

1. **`calculate_team_strength`** — eliminados `form_score` (redundante con
   `morale`) y `goals_score` (redundante con la fórmula base). Ahora solo usa
   rank + tier.
2. **Pesos rebalanceados** — `player_stats` subió de 10% → 15%,
   `team_strength` bajó de 28% → 25%, `home_advantage` bajó de 12% → 10%,
   `foreign_pct` subió de 5% → 7%. Suma = 100%.
3. **`is_neutral`** — Implementado en `calculate_home_advantage()`. Cuando
   `is_neutral=True` (KO stages), los bonos de México/USA/Canadá fuera de casa
   se reducen ~50%.

> ⚠️ Estos pesos fueron rebalanceados nuevamente en el Bloque G (ver tabla
> abajo).

### Pesos actuales (suma = 100%)

| Factor          | Peso | Nota |
|-----------------|:----:|------|
| team_strength   | 15%  | Solo rank + tier (sin form/goals) |
| player_stats    | 11%  | Goals + 0.5×Assists ponderado por minutes_2026 |
| market_value    | 10%  | Valor de plantilla |
| experience      | 6%   | intl_caps promedio (Wikipedia) |
| home_advantage  | 6%   | Incluye fanbase/diaspora; is_neutral reduce bonos |
| rest_days       | 6%   | Penalidad si <4 días entre partidos |
| squad_depth     | 6%   | Ratio suplentes con >500 min (dinámico desde players.json) |
| climate         | 5%   | Temperatura + altitud del estadio |
| foreign_pct     | 3%   | % de jugadores en ligas extranjeras |
| travel_fatigue  | 4%   | Km totales acumulados viajando |
| history         | 4%   | Historial en Mundiales |
| morale          | 4%   | Racha de resultados reciente |
| trophy_pedigree | 4%   | trophy_count promedio (Wikipedia) |
| odds            | 3%   | Cuotas DraftKings pre-torneo |
| height_advantage| 3%   | Altura promedio — ventaja aérea |
| club_chemistry  | 3%   | Pares del mismo club — coordinación |
| travel          | 3%   | Distancia base camp → venue |
| stakes          | 4%   | Presión de 3ª fecha: qualified−1 / contender+1 / eliminated−2 |

### Fórmula de goles esperados

```python
total_diff = Σ(factor_i × peso_i)   # sin randomness
total_diff_scaled = total_diff / 100

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = max(0.2, min(7.0, base_a * (1 + total_diff_scaled)))
λ_b = max(0.2, min(7.0, base_b * (1 - total_diff_scaled)))
```

## Score determinista (promedio de 1500 sims)

Cada partido corre **1500 simulaciones Poisson** desde λ determinista
(sin ruido aditivo). El score final es `round(avg_score_a, avg_score_b)`,
el promedio redondeado de las 1500 simulaciones. Esto reemplazó el ensemble
de 100 seeds y la selección de seed por campeón moda.

- No hay randomness en el resultado final (Ley de Grandes Números)
- Las probabilidades (win/draw/loss) se calculan de las frecuencias del mismo loop
- Un solo resultado, siempre reproducible con la misma seed interna (42)
- Tiempo total: ~0.10s para los 135 partidos (gracias a `random.choices` batch vs Poisson individual)

## Bloque A: Fix fixture/venue bugs (Completado)

### Cambios aplicados (A)

1. **Group L fixtures**:
   - "Panama vs England" → "England vs Ghana"
   - "Croatia vs Ghana" (duplicado) → "Croatia vs Panama"
   - Resultado: 6 partidos únicos, cada equipo juega 3.

2. **Conflictos horarios resueltos**:
   - Dallas 18:00 2026-06-20: Ecuador vs Germany movido a Houston 20:00
   - Seattle 18:00 2026-06-25: Netherlands vs Sweden movido a Vancouver 21:00
   - Los Angeles 18:00 2026-06-26: Norway vs Iraq movido a San Francisco 20:00

3. **R32 bracket venues** (bracket.py):
   `Dallas→Toronto, Miami→Los Angeles, Seattle→San Francisco, Kansas City→Seattle, Philadelphia→Atlanta, Toronto→Miami, Atlanta→Dallas, Atlanta→Kansas City`

4. **R16 pairings & venues** (bracket.py):
   - Pairings actualizados al bracket oficial FIFA 2026
   - Venues actualizados

## Bloque B: Market Value Parser + Estimaciones (Completado)

### Cambios aplicados (B)

1. **Fix parse_market_value()** (scraper.py):
   - Agregado `'mio' in val_lower` para manejar el sufijo alemán "Mio"
   - Se unificó con el bloque `'mill'` ya que ambos representan millones

2. **Estimaciones de market value**:
   - Agregado `_MARKET_VALUE_ESTIMATES` con valores estimados para los 48 equipos
   - Basado en tier + ajustes por equipo: Tier 1 (~1000M) → Tier 8 (~5M)
   - Modificado `_enrich_teams()` para usar estimaciones como fallback

### Valores estimados (top/bottom)

| Rango | Equipos | Valor |
|-------|---------|-------|
| Top   | France 1100, Argentina 1000, England 950, Spain 900 | ~1000M |
| Mid   | USA 350, Uruguay 300, Croatia 300 | ~300M |
| Low   | Haiti 10, Cape Verde 8, Curacao 5 | ~8M |

## Bloque C: Team Data Calibrations + Overrides (Completado)

### Cambios aplicados (C)

1. **TM_TEAM_OVERRIDES**:
   - Agregados: `Ivory Coast→Côte d'Ivoire`, `Czechia→Czech Republic`,
     `Cape Verde→Cabo Verde`, `South Korea→Korea Republic`
   - Total: 9 overrides → 49 team names mapeables

2. **Germany form_streak**: 1.0 → 0.70 con form_10 corregido

3. **Tiers recalibrados**:
   - Croatia: 4→3, Uruguay: 4→3, USA: 4→3, Japan: 4→3
   - Norway: 3→4, South Korea: 5→4, Sweden: 5→4, Austria: 5→4

4. **FANBASE**:
   - Eliminados equipos que no clasificaron
   - Croatia subió de 4→5 por éxito reciente en Mundiales

## Bloque D: Actualizar temperaturas de sedes (Completado)

### Verificación (D)

- Se compararon los 16 avg_temp actuales con datos pronosticados para
  junio-julio 2026 de worldcuptourism.com y prepyourtrip.com
- Todos los valores coinciden exactamente con worldcuptourism.com
- No se requirieron cambios

## Bloque E: Ajustar modelo (Completado)

### Cambios aplicados (E)

1. **`calculate_team_strength`** — eliminados `form_score` y `goals_score`
   (redundantes con `morale` y la fórmula base). Ahora solo usa `rank_score` +
   `tier_score`.
2. **Pesos rebalanceados** — `player_stats` subió de 10% a 15%,
   `team_strength` bajó de 28% a 25%, `home_advantage` bajó de 12% a 10%,
   `foreign_pct` subió de 5% a 7%. Suma = 100%.
3. **`is_neutral`** — parámetro agregado a `calculate_home_advantage()`. Cuando
   es True (KO stages), los bonos de México/USA/Canadá fuera de casa se reducen
   ~50% (Mexico 10→5, USA 8→4, Canada 5→2).

## Bloque F: Re-ejecutar stats_scraper + main.py (Completado)

### Cambios aplicados (F)

1. **stats_scraper.py** — campos renombrados de `_2025` a `_2026` para reflejar
   que la temporada 2025/26 termina en 2026
2. **Migración de caché** — `players.json` (1245 jugadores) y
   `tm_stats_cache.json` migrados sin re-scrapeo

## Bloque G: 4 nuevos factores (Completado)

### data.py (G)

1. **VENUE_TIMEZONES**: UTC offset para las 16 sedes (Mexico City -6, Toronto -5,
   Vancouver -8, etc.)
2. **HOME_TIMEZONES**: UTC offset para los 48 equipos según su país de origen
3. **SQUAD_DEPTH**: Ratio de jugadores `impact` sobre el total de `key_players`,
   escalado 0-10

### predictor.py — 4 nuevos factores (G)

1. **`calculate_rest_days(team_a, team_b, rest_a, rest_b)`**: Penaliza equipos
   con <4 días de descanso (3 pts por día faltante). El formato 2026 (48 equipos)
   comprime el fixture.
2. **`calculate_travel_fatigue(team_a, team_b, travel_km_a, travel_km_b)`**:
   Penaliza equipos con mucho kilometraje acumulado viajando entre sedes (3
   países sede = hasta 30,000 km posibles).
3. **`calculate_squad_depth_factor(team_a, team_b)`**: Ventaja para equipos con
   muchos jugadores de impacto en el banquillo (aprovechan las 5 sustituciones).
4. **`calculate_jet_lag(team_a, team_b, venue_name)`**: Penaliza diferencia
   horaria sede vs país de origen (0.7 pts por hora de diferencia, máx 5 pts).

### bracket.py — Team history tracking (G)

1. **`compute_team_history(group_predictions)`**: Calcula `last_date`,
   `last_venue` y `total_travel` por equipo tras fase de grupos.
2. **`_extend_matches(base, round_date)`**: Convierte matches simples a 7-tuplas
   con datos de descanso y fatiga.
3. **`_update_history(results, round_date)`**: Propaga el historial entre rondas
   KO (R32→R16→QF→SF→Final), acumulando kilómetros y actualizando fechas.

## Bloque H: Fair Play + FIFA 2026 tiebreaker cascade + safety net KO (Completado)

### data.py (H)

1. **`_CONF_CARD_RATES`**: Diccionario con `yellow_rate` (1.8–2.5) y `red_rate`
   (0.04–0.08) por confederación (AFC, CAF, CONCACAF, CONMEBOL, OFC, UEFA).
2. **`haversine()`**: Movida de `predictor.py` y `bracket.py` a `data.py` como
   función pública compartida — DRY.
3. **`yellow_rate`/`red_rate`**: Campos agregados a cada equipo en `_enrich_teams()`
   según su confederación para simular Fair Play.

### predictor.py (H)

1. **`simulate_match_cards(team_a_data, team_b_data)`**: Genera tarjetas por
   partido usando Poisson (`yellow_rate`) + Bernoulli (`red_rate`). Calcula FP
   loss según Artículo 13: yellow −1, doble amarilla −3 (no implementada), roja
   directa −4.
2. **FP en output**: `predict_match` ahora retorna `fp_delta_a`, `fp_delta_b`,
   `yc_a`, `yc_b`, `rc_a`, `rc_b`.
3. **import haversine**: Ahora importa `haversine` desde `data` en lugar de
   la función local `_haversine` eliminada.

### bracket.py (H)

1. **`_sort_group(group_name, standings)`**: Implementa la cascada FIFA 2026
   (Artículo 13): pts → H2H mini-tabla (pts/GD/GF entre equipos empatados) →
   GD global → GF global → Fair Play (−1 por amarilla, −4 por roja) → Ranking
   FIFA (fallback 100 si no disponible).
2. **`_h2h_matches` global**: Diccionario que almacena los resultados de cada
   partido de grupos para poder calcular la mini-tabla H2H entre equipos
   empatados en pts.
3. **`determine_qualified`** actualizada: La selección de 8 mejores terceros usa
   cascada pts → GD → GF → FP → Ranking (7-tuplas en vez de 5-tuplas).
4. **`simulate_group_stage`** actualizada: Trackea `fp` por equipo y alimenta
   `_h2h_matches`.
5. **Safety net KO**: `simulate_knockout_round` detecta `winner == "Empate"` y
   resuelve mediante ranking FIFA como fallback final.
6. **`_ranking_winner(team_a, team_b, data_a, data_b)`**: Helper que elige al
   equipo con mejor ranking (ranking más bajo = mejor).
7. **`_venue_dist`** ahora usa `haversine` desde `data` — eliminada `_haversine`
   local.
8. **Advertencia `R16_PAIRINGS`**: Comentario prominente sobre índices frágiles
   que dependen del orden de `R32_BRACKET`.

## Bloque J: Top Scorer + ejecutar.bat (Completado)

### top_scorer.py (J)

1. **`_build_team_weights(team_name, players_data)`**: Construye pesos por
   jugador usando `(goals_2026 * position_weight + 0.1)`. Position weights:
   FW=1.0, MF=0.4, DF=0.05. El `+0.1` evita pesos cero para defensores.
2. **`distribute_goals(team_name, total_goals, players_data)`**: Distribuye
   `total_goals` enteros muestreando `random.choices()` con los pesos
   normalizados. Retorna `Counter[player_name]`.
3. **`compute_top_scorers(all_match_results, players_data)`**: Itera los 135
   partidos del prode completo, distribuye goles de local y visitante por
   separado, suma totales globales.
4. **`get_player_team(player_name, players_data)`**: Busca a qué equipo
   pertenece un jugador. Necesaria porque `players.json` está indexado por
   equipo, no por jugador.
5. **Seed determinista**: Se llama `random.seed(0)` al inicio de
   `compute_top_scorers()` para que la distribución de goles sea reproducible
   SIN afectar los resultados de los partidos (se ejecuta post-simulación).

### main.py (J)

1. **`--goleadores`**: Modo silencioso que suprime stdout de la simulación con
   `contextlib.redirect_stdout(io.StringIO())`, imprime solo la tabla de
   goleadores al final.
2. **Seed como argumento**: `python main.py 123` o `python main.py --seed 123`.
3. **Integración**: `run_top_scorers()` se llama al final de
   `run_full_simulation()` con el prode completo, iterando los dicts de
   `all_results_group` y `ko_results`.

### ejecutar.bat (J)

Menú interactivo con 5 opciones:
1. **Simulación completa (1500 sims por partido)** — `python prode_mundial/main.py`
2. **Tabla de goleadores** — `python prode_mundial/main.py --goleadores`
3. **Ver predicciones** — submenú interactivo (display.py)
4. **Optimizador** — `python prode_mundial/optimizer.py`
5. **Salir**

## Bloque N: Factor Stakes (Presión de 3ª Fecha) — Completo

### Problema
La 3ª fecha de fase de grupos es el momento decisivo donde se define la clasificación.
El modelo original trataba todos los partidos de grupos igual, ignorando el contexto
de la tabla. Esto perdía dinámicas clave: equipos clasificados que rotan, eliminados
que bajan los brazos, y contendientes que sobre-renden en partidos decisivos.

### Solución aplicada

**1. `data.py` — `get_matchday(fixture_index)`**
Helper que identifica si un fixture es MD1, MD2 o MD3 según su posición (0-1→1, 2-3→2, 4-5→3).

**2. `bracket.py` — `classify_stakes(standings)` + loop grupo por grupo**
- `run_full_simulation()` reestructurada: procesa cada grupo por separado
- Para cada grupo: MD1 → MD2 → calcular tabla parcial → clasificar stakes → MD3 con contexto
- `classify_stakes()`: clasificación matemática basada en pts + GD después de 2 fechas:
  - `qualified`: 6+ pts y 2° con ≤3 pts (no puede ser alcanzado)
  - `eliminated`: incluso ganando no alcanza el 2° puesto
  - `contender`: todo lo demás (sigue en la lucha)

**3. `predictor.py` — `calculate_stakes_factor()` + varianza MD3**
- Nuevo factor con peso 4% (redistribuido: team_strength 16→15, home_adv 7→6, foreign_pct 4→3, odds 4→3)
- Valores por equipo: qualified=−1, contender=+1, eliminated=−2. Diff ×4 (rango −12 a +12)
- Varianza extra: `gauss(0, 0.15)` en λ cuando al menos un equipo es `contender` en MD3

### Efecto

| Combinación stakes | Factor diff | Varianza | Efecto esperado |
|---|---|---|---|
| contender vs qualified | +8 contender | Sí | Underdog empuja, posible sorpresa |
| contender vs eliminated | +12 contender | Sí | Contender arrasa |
| contender vs contender | 0 | Sí | Máxima tensión, más impredecible |
| qualified vs qualified | 0 | No | Ambos relajados |
| qualified vs eliminated | +4 qualified | No | Favorito gana sin arrasar |

### Verificación
- ✅ 24/24 MD3 matches tienen stakes poblados
- ✅ 48/48 MD1/MD2 matches tienen stakes=None (sin cambios)
- ✅ Compatibilidad hacia atrás: KO rounds sin stakes

## Comandos Útiles

```powershell
# Ejecutar wikiscraper
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/wikiscraper.py

# Ejecutar scraper de estadísticas (Transfermarkt)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py

# Forzar re-scrapeo de estadísticas (ignorar caché)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py --force

# Ejecutar simulación completa (1500 sims por partido, con goleadores)
python prode_mundial/main.py

# Solo tabla de goleadores (modo silencioso)
python prode_mundial/main.py --goleadores

# Instalar paquete (modo desarrollo)
pip install -e .

# Ejecutar todos los tests
pytest

# Menú interactivo
.\ejecutar.bat

# Git push
git add -A; git commit -m "mensaje"; git push origin master
```

## Sesiones

| Fecha | Acción | Detalle |
|-------|--------|---------|
| 2026-06-08 | `git reset --hard origin/master` | Reposincronizado a `e9fe83f` (Bloque N) — trajo display.py, optimizer.py, stats_scraper.py, top_scorer.py, ejecutar.bat, AGENTS.md, opencode.jsonc, outputs |
| 2026-06-08 | Instalación LSP | Se instaló `python-lsp-server` 1.14.0 (faltaba post-clone). `opencode.jsonc` ya tenía `"lsp": true` |
| 2026-06-08 | Fase 4a: pyproject.toml + __init__.py | Package instalable con `pip install -e .`, entry point `prode-mundial`, pytest config integrado |
| 2026-06-08 | Fase 4b: Retry resilience | `_fetch_with_retry()` en scraper.py (4 retries, 2s/4s/8s/16s), `_get()` en stats_scraper.py (3 retries, connect/read timeout separado) |
| 2026-06-08 | Fase Tests + Dixon-Coles τ | 4 nuevos test files (83 tests), τ correction (ρ=-0.15, joint dist 16×16), 129 tests total, todo pass |
```
