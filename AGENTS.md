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

## Estructura

```text
prode_mundial/
├── scraper.py           # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py              # Datos de equipos, sedes, fixture, bases operativas, haversine, card rates
├── predictor.py         # Motor de 15 factores ponderados + simulación Poisson
├── stats_scraper.py     # Scraper de estadísticas individuales (Transfermarkt API)
├── bracket.py           # Bracket oficial 2026 + H2H tiebreaker + safety net KO
├── output.py            # Exportación CSV/JSON
├── main.py              # Orquestador principal
├── top_scorer.py        # Distribución de goles a jugadores (top goleador)
├── wikiscraper.py       # Scraper individual de Wikipedia vía API
└── output/
    ├── players.json              # 1245 jugadores
    ├── wiki_cache.json           # Caché de Wikipedia scraping
    ├── tm_stats_cache.json       # Caché de Transfermarkt stats
    ├── fase_grupos.csv/json      # Partidos de grupos
    ├── tabla_posiciones.csv      # Posiciones finales
    ├── eliminatorias.csv         # Llaves KO
    └── prode_completo.csv        # Prode completo (135 partidos)
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
| team_strength   | 17%  | Solo rank + tier (sin form/goals) |
| market_value    | 11%  | Factor independiente |
| player_stats    | 12%  | Goals + 0.5×Assists promedio por jugador (temporada 2025/26) |
| home_advantage  | 8%   | Incluye fanbase/diaspora; is_neutral reduce bonos |
| climate         | 6%   | Temperatura + altitud del estadio |
| travel          | 3%   | Distancia base camp → venue |
| history         | 4%   | Historial en Mundiales |
| morale          | 4%   | Racha de resultados reciente |
| age_penalty     | 3%   | Edad promedio de la plantilla |
| foreign_pct     | 5%   | % de jugadores en ligas extranjeras |
| rest_days       | 7%   | Penalidad si <4 días entre partidos |
| squad_depth     | 7%   | Ratio de jugadores de impacto en plantilla |
| travel_fatigue  | 5%   | Km totales acumulados viajando |
| jet_lag         | 3%   | Diferencia horaria sede vs país de origen |
| odds            | 5%   | Cuotas de apuestas DraftKings pre-torneo |
| randomness      | —    | Ya no se usa. Antes: `gauss(0,0.7)×10` |

### Fórmula de goles esperados

```python
total_diff = Σ(factor_i × peso_i)   # sin randomness
total_diff_scaled = total_diff / 100

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = max(0.2, min(7.0, base_a * (1 + total_diff_scaled)))
λ_b = max(0.2, min(7.0, base_b * (1 - total_diff_scaled)))
```

## Seed

Por defecto `main.py` corre un **ensemble de 100 seeds** con Poisson draw
(`skip_sims=True`) y selecciona la primera seed donde el campeón más frecuente
ganó, luego enriquece esa seed con probabilidades completas (`skip_sims=False`).
Esto elimina accidentes estadísticos de seed fija y asegura que el campeón del
bracket final coincida con la distribución del modelo.

Resultado (ensemble): Argentina 🇦🇷 campeón (1-0 vs France en final).

### Ensemble (100 seeds) — Probabilidades de campeonato

| Rango | Equipo | Prob |
|-------|--------|:----:|
| 1 | Argentina | 91% |
| 2 | France | 8% |
| 3 | Spain | 1% |

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
1. **Simulación completa (ensemble)** — `python prode_mundial/main.py` (100 seeds)
2. **Seed personalizada** — pide número y ejecuta `python prode_mundial/main.py <N>`
3. **Seed única (sin ensemble)** — `python prode_mundial/main.py --no-ensemble <N>`
4. **Tabla de goleadores** — `python prode_mundial/main.py --goleadores`
5. **Salir**

## Comandos Útiles

```powershell
# Ejecutar wikiscraper
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/wikiscraper.py

# Ejecutar scraper de estadísticas (Transfermarkt)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py

# Forzar re-scrapeo de estadísticas (ignorar caché)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py --force

# Ejecutar simulación completa (ensemble 100 seeds, con goleadores)
python prode_mundial/main.py

# Solo tabla de goleadores (modo silencioso)
python prode_mundial/main.py --goleadores

# Seed personalizada
python prode_mundial/main.py 123
python prode_mundial/main.py --seed 123

# Menú interactivo
.\ejecutar.bat

# Git push
git add -A; git commit -m "mensaje"; git push origin master
```
