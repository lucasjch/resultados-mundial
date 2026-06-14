# Prode Mundial 2026 - AGENTS.md
_Autor: Lucas Congil Hadla_

<!-- markdownlint-disable MD013 -->

Memoria persistente del proyecto. opencode carga esto automáticamente al iniciar cada sesión.

## Objetivo

Script Python que analiza los 135 partidos del Mundial 2026 y predice resultados
para completar un prode. Exporta a CSV y JSON.

## Quick Start

```bash
cd prode_mundial
python wikiscraper.py          # ~40 min: scrapea 1248 jugadores (checkpoint cada 50)
python main.py                 # ejecuta predicción completa
```

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
├── scraper.py        # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py           # Datos de equipos, sedes, fixture, base camps, card rates, PENALTY_TAKERS
├── predictor.py      # Motor de 19 factores ponderados + Poisson + Dixon-Coles τ
├── stats_scraper.py  # Scraper de estadísticas individuales (Transfermarkt API)
├── bracket.py        # Bracket oficial 2026 (R32, R16, QF, SF, 3°, Final)
├── output.py         # Exportación CSV/JSON + inyección de análisis narrativo
├── main.py           # Orquestador principal
├── top_scorer.py     # Distribución de goles a jugadores (top goleador)
├── analysis.py       # Motor de narración PRODE (recomendación + análisis + veredicto)
├── friendlies_data.py# Dataset de 57 amistosos (may-jun 2026) + compute_friendly_form()
├── real_results.py   # Sistema de resultados reales (carga, forma, suspensiones, stats)
├── wikiscraper.py    # Scraper individual de Wikipedia vía API
├── __init__.py       # Package init (v0.1.0)
├── tests/            # 5 test files, 138 tests
│   ├── test_predictor.py
│   ├── test_bracket.py
│   ├── test_data.py
│   ├── test_top_scorer.py
│   └── test_output.py
└── output/           # Resultados generados
    ├── players.json          # 1248 jugadores (48 equipos × 26, enriquecido vía wikiscraper)
    ├── wiki_cache.json       # Caché de Wikipedia scraping
    ├── tm_stats_cache.json   # Caché de Transfermarkt stats
    ├── friendlies.json       # Dataset de 57 amistosos
    ├── real_results.json     # Resultados reales de MD1 (México 2-0 Sudáfrica, Corea 2-1 Chequia)
    ├── fase_grupos.csv/json  # Partidos de grupos (con analysis narrativo)
    ├── tabla_posiciones.csv  # Posiciones finales
    ├── eliminatorias.csv     # Llaves KO
    └── prode_completo.csv    # Prode completo (135 partidos)
```

## Pipeline Detallado

### 1. Scraping (`scraper.py`)

- **Promiedos** (28 equipos): parsea HTML `<tr>`/`<td>` - nombre, dorsal, edad, altura
- **Transfermarkt** (20 equipos): `html.unescape()` + regex - nombre, posición, DOB, valor de mercado
- **Retry**: `_fetch_with_retry()` con 4 reintentos (delay 2s/4s/8s/16s) para `urllib.error.URLError`/`socket.timeout`
- Total: **1248 jugadores** de 48 equipos
- Output: `output/players.json`

### 1b. Wikipedia Stats (`wikiscraper.py`)

- Scraper vía API REST de Wikipedia (`action=parse` + `action=query`)
- Para cada jugador, extrae del infobox:
  - `intl_caps`, `intl_goals` (selección mayor - descarta juveniles por regex `U\d+`)
  - `club_apps`, `club_goals` (club actual = entrada `yearsN` con N más alto)
  - `current_club`, `club_name` (limpia wikilinks tipo `[[Real Madrid CF|Real Madrid]]`)
  - `height` (parsea `1.80 m` desde el texto)
- De la sección **Honours**: lista de títulos con categoría y `trophy_count`
- **Fix `_extract_num()`**: maneja valores con wikilinks tipo `[[List of...|56]]` o templates `{{efn|...}}`
- **Incremental save**: checkpoint cada 50 jugadores para reanudar en caso de timeout
- Caché en `output/wiki_cache.json` - evita re-scrapear en ejecuciones posteriores
- Input: 1248 jugadores · Output: ~40 min (delay 1s entre requests) · Resultado: 1116/1248 encontrados (89%)

### 1c. Transfermarkt Stats (`stats_scraper.py`)

- Scraper vía API `tmapi-alpha.transfermarkt.technology` (sin rate limit)
- Para cada equipo consulta `/quickselect/players/{teamId}`, luego `/player/{playerId}/performance-game` con `seasonId: 2025`
- Extrae goles, asistencias, minutos de la temporada 2025/26
- **Fuzzy matching**: `SequenceMatcher` ≥0.75 con diferencia ≥0.1 del segundo mejor + limpieza de sufijos posicionales
- **TM_TEAM_OVERRIDES**: 9 correcciones de nombre (e.g. `Cape Verde→Cabo Verde`, `South Korea→Korea Republic`)
- **Retry**: `_get()` reintenta 3 veces con connect timeout separado (10s/read 30s) para Timeout/ConnectionError
- Caché en `output/tm_stats_cache.json` - evita re-scrapear
- Output: enriquece `players.json` con campos `goals_2026`, `assists_2026`, `minutes_2026`
- Resultado: 1248/1248 jugadores con stats (100%)

### 2. Datos (`data.py`)

- `TEAMS`: 48 equipos con rank, tier, confederación, coach, capitán, temperatura/altitud local, racha (`form_streak`), historial mundialista, jugadores clave, goles promedio, diáspora en USA
- `PENALTY_TAKERS`: 48 selecciones × 3 pateadores designados (144 jugadores, nombres exactos del `players.json`)
- `TOP_SCORER_CANDIDATES`: 27 estrellas con multiplicador (1.2–1.8) para top_scorer.py
- `_TOP_LEAGUE_CLUBS`: ~120 clubes de Top 5 ligas para league_boost en top_scorer.py
- `VENUES`: 16 sedes con país, estadio, capacidad, techo, temperatura, altitud
- `GROUPS`: 12 grupos (A-L) de 4 equipos
- `FIXTURES`: 72 partidos de grupos con fecha, hora ART (UTC-3), sede - corregidos desde ESPN (Jun 2026)
- `CITY_COORDS`: coordenadas de 41 ciudades (sedes + bases operativas)
- `BASE_CAMPS`: base de concentración real de cada selección
- `VENUE_TIMEZONES`: UTC offset para las 16 sedes
- `HOME_TIMEZONES`: UTC offset para los 48 equipos
- `SQUAD_DEPTH`: ratio de jugadores `impact` / `key_players` escalado 0–10
- `_FOREIGN_PCT_ESTIMATES`: % de jugadores en el extranjero por confederación
- `_FANBASE`: popularidad global (0–8), recalibrada post-clasificación
- `_MARKET_VALUE_ESTIMATES`: valores estimados para 48 equipos (France 1100M → Curacao 5M), usado como fallback
- `_enrich_teams()`: integra `players.json` en cada equipo con 6 campos extra
- `haversine()`: cálculo de distancia entre coordenadas (compartida con predictor y bracket)
- `_CONF_CARD_RATES`: tasas de tarjetas amarillas/rojas por confederación para Fair Play
- `get_matchday()`: identifica MD1/MD2/MD3 según índice del fixture

### 3. Predicción (`predictor.py`)

19 factores ponderados + Dixon-Coles τ + 1500 sims Poisson deterministas.

|Factor|Peso|Descripción|
|--------|:----:|-------------|
|`team_strength`|15%|Solo rank + tier (sin form/goals)|
|`player_stats`|11%|Goals + 0.5×Assists ponderado por minutes_2026; inyecta goles/asistencias reales si hay `--results`|
|`market_value`|10%|Diferencia de valor de plantilla (escala log)|
|`experience`|6%|intl_caps promedio (Wikipedia)|
|`home_advantage`|6%|Localía CONCACAF + fanbase/diaspora; `is_neutral` reduce bonos en KO|
|`rest_days`|6%|Penalidad si <4 días entre partidos|
|`squad_depth`|6%|Ratio suplentes con >500 min (dinámico desde players.json); excluye suspendidos si hay `--results`|
|`climate`|5%|Diferencia térmica, altitud, techo cerrado|
|`foreign_pct`|2%|% de jugadores en ligas extranjeras|
|`travel_fatigue`|4%|Km totales acumulados viajando entre sedes|
|`history`|3%|Mejor actuación histórica en Mundiales|
|`morale`|1%|`form_streak` del equipo|
|`friendly_form`|2%|Puntaje compuesto de 57 amistosos (may-jun 2026)|
|`trophy_pedigree`|4%|trophy_count promedio (Wikipedia)|
|`odds`|2%|Cuotas DraftKings pre-torneo|
|`height_advantage`|3%|Altura promedio - ventaja aérea; modulado por `_aerial_modifier` de resultados reales|
|`club_chemistry`|3%|Pares del mismo club - coordinación|
|`travel`|2%|Distancia base → sede (haversine)|
|`stakes`|4%|Presión de 3ª fecha: qualified−1 / contender+1 / eliminated−2|
|`real_match_form`|5%|Forma real de MD1: resultado 25%, xG 20%, tiros 15%, posesión 10%, pases 10%, corners/aéreos/errores/atajadas 5% c/u|

**Fórmula de goles esperados** (cruza ataque vs defensa):

```text
total_diff = Σ(factor_i × peso_i)   # sin randomness
total_diff_scaled = total_diff / 100

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = max(0.2, min(7.0, base_a * (1 + total_diff_scaled)))
λ_b = max(0.2, min(7.0, base_b * (1 - total_diff_scaled)))
```

**Dixon-Coles τ correction**: ρ = −0.15. Ajusta probabilidad de scores bajos (0-0, 1-1, 1-0, 0-1).
Tabla joint 16×16 con `_build_joint_dist()`, muestreo batch `random.choices(k=1500)`.
En MD3 con stakes contender se usa Poisson independiente (el ruido gaussiano ya aproxima).

**Score determinista**: Cada partido corre 1500 sims Poisson desde λ determinista.
Score final = `round(promedio_a, promedio_b)`. Siempre reproducible (seed interna 42).

**Fair Play**: `simulate_match_cards()` genera tarjetas vía Poisson (yellow_rate) + Bernoulli (red_rate).
FP loss según Artículo 13: amarilla −1, roja directa −4.

### 4. Bracket (`bracket.py`)

- **Fase de grupos**: 72 partidos, tabla con puntos y GD. Tiebreaker FIFA Artículo 13: H2H pts → H2H GD → H2H GF → GD global → GF global → Fair Play → Ranking FIFA.
- **Mejores terceros**: top 8 de 12 terceros clasifican (cascada pts → GD → GF → FP → Ranking).
- **R32**: 16 llaves fijas oficiales con venues FIFA 2026.
- **R16**: emparejamientos fijos con venues actualizados.
- **QF, SF, 3°, Final**: bracket estándar.
- **Team history tracking**: `compute_team_history()` calcula `last_date`, `last_venue`, `total_travel` por equipo tras grupos; `_update_history()` propaga entre rondas KO.
- **Stakes en MD3**: `classify_stakes()` determina qualified/contender/eliminated tras MD2; MD3 se predice con contexto de tabla.
- **Safety net KO**: si `predict_match` retorna "Empate", fallback por ranking FIFA.

### 1d. Friendlies Dataset (`friendlies_data.py`)

- Dataset de 57 amistosos internacionales reales disputados entre el 22 de mayo y el 10 de junio de 2026
- `compute_friendly_form(team_name)`: puntaje compuesto (resultados + goles + solidez defensiva) escalado -10 a +10
- `get_friendly_scorers(team_name)`: lista de goleadores en amistosos para boost en top_scorer.py
- Export a `output/friendlies.json`

### 1e. Real Results System (`real_results.py`)

- 6 funciones stateless: `load_real_results()`, `save_real_results()`, `compute_real_form()` (9-componente), `track_suspensions()` (2A/1R), `apply_player_stats()` (goles/asis extra), `update_goals_conceded_avg()`, `update_aerial_factor()`
- `compute_real_form()`: pesa resultado (25%), xG (20%), tiros (15%), posesión (10%), pases (10%), corners (5%), duelos aéreos (5%), errores (5%), atajadas (5%). Escala -10..+10
- `track_suspensions()`: 2 amarillas en distinto partido o 1 roja directa = baja automática
- `apply_player_stats()`: suma goles/asistencias reales para inyectar en `player_stats`
- `update_goals_conceded_avg()`: ajusta promedio de goles recibidos por errores defensivos (+0.1 c/u)
- `update_aerial_factor()`: modula `height_advantage` según % de duelos aéreos ganados
- Input: `output/real_results.json` (flag `--results` en main.py)
- Output: muta `get_team()` in-memory para `goals_conceded_avg`/`_aerial_modifier`; suspensiones/goles extra/forma real se pasan como kwargs a `predict_match()` en MD2/MD3

### 5. Exportación (`output.py`)

- `fase_grupos.csv/json`: todos los partidos con probabilidades, desglose de factores, y análisis narrativo
- `tabla_posiciones.csv`: posiciones finales por grupo
- `eliminatorias.csv`: todas las llaves KO
- `prode_completo.csv`: prode completo en un solo archivo

### 6. Análisis Narrativo PRODE (`analysis.py`)

- Motor de narración offline (sin APIs externas) para ayudar al usuario a completar su PRODE
- Se genera durante `main.py` y se guarda en el JSON, no se calcula en la GUI
- Cada partido produce 3 secciones:
  - **Recomendación** (badge de una línea): `LOCAL SEGURO`, `FAVORITO CON CAUTELA`, `EMPATE PROBABLE`, `SORPRESA POSIBLE`, etc. Según confianza y probabilidades.
  - **Análisis**: forma reciente del equipo (`form_streak`), preparación en amistosos (`friendly_form`), carta bajo la manga (estrella del equipo vía `get_team_weights`), pateador de penales designado, lesionados/ausentes, historial mundialista, factor diferencial del modelo, poderío ofensivo/defensivo basado en goles promedio.
  - **Veredicto**: ganador esperado con % de probabilidad, riesgo de empate, confianza del modelo.
- Datos usados: `get_team()` (data.py), `compute_friendly_form()` (friendlies_data.py), `get_team_weights()` (top_scorer.py), `PENALTY_TAKERS` e `INJURED_OUT` (data.py), `factors` del match.
- Se inyecta como campo `"analysis"` en `fase_grupos.json` y `eliminatorias.json`
- En la GUI se muestra arriba del score: badge colorido + Text widget con scroll

### 7. Top Scorer (`top_scorer.py`)

- Distribución Poisson de goles entre jugadores de equipos que llegan a KO
- Fórmula exponencial: `w = max(raw ** 1.8, 0.001)` sin piso artificial `+0.1`
- `_league_boost()`: ×1.3 para clubes en Top 5 ligas (set `_TOP_LEAGUE_CLUBS` ~120 clubes), ×1.0 para el resto. **Nunca penaliza** a jugadores en ligas menores.
- `_penalty_boost()`: ×1.5 (#1), ×1.2 (#2), ×1.0 (#3) según `PENALTY_TAKERS`
- `TOP_SCORER_CANDIDATES`: boosts fijos (Messi 1.8, Kane 1.6, Mbappé 1.6, Ronaldo 1.6, Haaland 1.4, etc.)
- Boost de experiencia internacional (+30% por gol/partido en selección si hay datos)
- Friendly boost: +30% por gol marcado en amistosos recientes
- Seed determinista `random.seed(0)` para reproducción
- Resultado actual: Kylian Mbappé 13, Kai Havertz 10, Cristiano Ronaldo 9, Harry Kane 9, Lionel Messi 7

## Bases Operativas Reales

|Selección|Base|Sede/Instalación|
|-----------|------|------------------|
|Algeria|Kansas City|Universidad de Kansas|
|Argentina|Kansas City|Sporting KC Training Center|
|Australia|San Francisco|Oakland Roots & Soul|
|Austria|Goleta|UC Santa Barbara Harder Stadium|
|Belgium|Renton|Seattle Sounders FC|
|Bosnia & Herzegovina|Sandy|RSL Stadium|
|Brazil|New York|Columbia Park|
|Cape Verde|Tampa|Waters Sportsplex|
|Canada|Vancouver|National Soccer Development Centre|
|Colombia|Guadalajara|Academia Atlas FC|
|DR Congo|Houston|Houston Training Centre|
|Ivory Coast|Philadelphia|Philadelphia Union|
|Croatia|Alexandria|Episcopal Institute|
|Curacao|Boca Raton|Florida Atlantic University|
|Czechia|Dallas|Mansfield Multipurpose Stadium|
|Ecuador|Columbus|Columbus Crew Training Center|
|Egypt|Spokane|Gonzaga University|
|England|Kansas City|Swope Soccer Village|
|France|Boston|Bentley University|
|Germany|Winston-Salem|Wake Forest University|
|Ghana|Boston|Bryant University|
|Haiti|New York|Stockton University|
|Iran|Tijuana|Xoloitzcuintle Center|
|Iraq|Greenbrier County|The Greenbrier|
|Japan|Nashville|Nashville SC|
|Jordan|Portland|University of Portland|
|Mexico|Mexico City|CAR|
|Morocco|New York|The Pingry School|
|Netherlands|Kansas City|KC Current Training|
|New Zealand|San Diego|University of San Diego|
|Norway|Greensboro|UNC Greensboro|
|Panama|New Tecumseth|Nottawasaga Training Site|
|Paraguay|San Francisco|Spartan Soccer Complex|
|Portugal|Palm Beach Gardens|Gardens North County Park|
|Qatar|Santa Barbara|Westmont College|
|Saudi Arabia|Austin|Austin FC Stadium|
|Scotland|Charlotte|Charlotte FC|
|Senegal|New York|Rutgers University|
|South Africa|Pachuca|CF Pachuca|
|South Korea|Guadalajara|Chivas Verde Valle|
|Spain|Chattanooga|Baylor School|
|Sweden|Dallas|Dallas FC Stadium|
|Switzerland|San Diego|SDJA|
|Tunisia|Monterrey|Rayados Training Center|
|Turkey|Mesa|Arizona Athletic Grounds|
|USA|Irvine|Great Park Sports Complex|
|Uruguay|Cancun|Mayakoba Training Center|
|Uzbekistan|Atlanta|Atlanta United Training Center|

## Plan de Fases

|#|Fase|Estado|
|----|------|--------|
|1|Ejecutar wikiscraper.py (1116/1248 jugadores)|✅ Completado|
|2|Decidir fuente de asistencias|✅ Completado|
|3|Integrar stats individuales como factores|✅ Completado|
|4|Arreglar modelo (pesos, redundancias, fórmula)|✅ Completado|
|5|Revisar predicciones Grupo A|✅ Completado|
|6|Ejecutar simulación completa|✅ Completado|
|-|**Bloque A**: Fix fixture/venue bugs|✅ Completado|
|-|**Bloque B**: Market Value Parser + Estimaciones|✅ Completado|
|-|**Bloque C**: Team Data Calibrations + Overrides|✅ Completado|
|-|**Bloque D**: Actualizar temperaturas de sedes|✅ Completado|
|-|**Bloque E**: Ajustar modelo (form/goals, player_stats, is_neutral)|✅ Completado|
|-|**Bloque F**: Re-ejecutar stats_scraper + main.py|✅ Completado|
|-|**Bloque G**: 4 nuevos factores|✅ Completado|
|-|**Bloque H**: Fair Play + FIFA 2026 tiebreaker cascade + safety net KO|✅ Completado|
|-|**Bloque I**: Fix probabilidades (noise removal) + confidence del winner real|✅ Completado|
|-|**Bloque J**: Top scorer + ejecutar.bat menú interactivo|✅ Completado|
|-|**Bloque K**: Ensemble 100 seeds + upset correction + factor odds|✅ Completado|
|-|**Bloque L**: Optimización completa de factores (4 nuevos, 2 eliminados, mejoras)|✅ Completado|
|-|**Bloque M**: Eliminar ensemble, score promedio de 1500 sims|✅ Completado|
|-|**Bloque N**: Factor Stakes (presión de 3ª fecha) + varianza MD3|✅ Completado|
|-|**Fase Tests**: 4 nuevos test files (bracket/data/top_scorer/output)|✅ Completado|
|-|**Dixon-Coles τ**: Corrección de empates (ρ=-0.15, joint dist 16×16)|✅ Completado|
|-|**Fase 4a**: pyproject.toml + __init__.py (package installable)|✅ Completado|
|-|**Fase 4b**: Retry + exponential backoff en scraper.py y stats_scraper.py|✅ Completado|
|-|**FIXTURES**: Corrección completa vía ESPN (72 partidos en ART, eliminado xlsx)|✅ Completado|
|-|**Friendlies Data**: dataset de 57 amistosos + factor friendly_form|✅ Completado|
|-|**Bloque Ñ**: Top scorer model (exponential, league boost, penalty boost, candidates)|✅ Completado|
|-|**Bloque O**: Análisis narrativo PRODE (analysis.py + GUI display)|✅ Completado|
|-|**Bloque P**: Icono + version_info.txt + --noupx (anti-falso-positivo)|✅ Completado|
|-|**Bloque Q**: Real Results System (carga MD1, factor real_match_form 5%, suspensiones)|✅ Completado|
|-|**Bloque W**: _SOFASCORE_NAME_MAP + _SEED_DATA expandido (Qatar, Switzerland, Brazil, Morocco) - 192 nuevos ratings de Sofascore, 6 seed blocks total|✅ Completado|

## Decisiones Tomadas

1. **Wikiscraper**: Se agregó checkpoint incremental cada 50 jugadores para evitar perder progreso en timeouts.
2. **UTF-8 fix**: En Windows requiere `$env:PYTHONIOENCODING='utf-8'` antes de ejecutar scripts Python con caracteres UTF-8.
3. **LSP**: `python-lsp-server` (pylsp) instalado globalmente. `opencode.jsonc` con `"lsp": true` en la raíz. Requiere reiniciar opencode para que tome efecto.
4. **Repositorio**: `https://github.com/lucasjch/resultados-mundial.git`, branch `master`.
5. **Fuente de asistencias → Transfermarkt API**: `tmapi-alpha.transfermarkt.technology` devuelve stats detalladas por partido (goles, asistencias, minutos) sin rate limit. Reemplaza FBref (bloqueado por Cloudflare).
6. **Transfermarkt endpoints**: `/quickselect/teams/FIWC` → 48 equipos, `/quickselect/players/{teamId}` → jugadores, `/player/{playerId}/performance-game` → stats por temporada.
7. **Fair Play card simulation**: Tarjetas generadas por partido vía Poisson (yellow_rate confederation-level) + Bernoulli (red_rate). FP points según Artículo 13 (−1 por amarilla, −4 por roja directa).
8. **FIFA 2026 tiebreaker cascade (Artículo 13)**: H2H pts → H2H GD → H2H GF → GD global → GF global → Fair Play → Ranking FIFA. Aplicado en `_sort_group()` para grupos y en `determine_qualified()` para mejores terceros.
9. **Safety net KO doble capa**: `predict_match` resuelve empates en KO via morale + squad_depth + gauss noise; `simulate_knockout_round` tiene fallback por ranking FIFA si aún hay "Empate".
10. **Haversine centralizada**: Única implementación en `data.py`; predictor y bracket importan desde ahí - DRY.
11. **`_PLAYERS_CACHE`**: Carga lazy de `players.json` (1248 jugadores) para evitar 135 lecturas de disco durante predict_match.
12. **Pre-carga de team data**: `get_team()` llamado 1 vez al inicio de `predict_match`; los 8 factores que lo usaban internamente ahora reciben dicts pre-cargados.
13. **Dead code eliminado**: `SequenceMatcher` import, `_load_team_players()`, `_haversine` local en predictor y bracket, import de `calculate_team_strength` en bracket.
14. **1000 sims sin ruido extra**: Las probabilidades se calculan directamente de Poisson(λ determinista). El `random.gauss(0, 0.7)*10` fue eliminado.
15. **Confidence = probabilidad del winner real**: `confidence = prob_winner * 100`, no del resultado más probable.
16. **Top scorer deterministic seed**: `random.seed(0)` dentro de `compute_top_scorers()` para distribución reproducible de goles.
17. **`players.json` es `{team: [players]}`**: No `{player_name: data}`. Requiere `get_player_team()` para lookup inverso.
18. **ejecutar.bat en raíz**: Menú interactivo PowerShell/.bat portable. No requiere instalación en PATH.
19. **Score promedio de 1500 sims**: `round(sum_a / 1500, round(sum_b / 1500))`.
20. **LSP instalado en sesión 2026-06-08**: `python-lsp-server` 1.14.0.
21. **Dixon-Coles τ (ρ = -0.15)**: Aumenta 0-0 y 1-1 (τ > 1), disminuye 1-0/0-1 (τ < 1). Tabla 16×16, `random.choices(k=1500)`.
22. **Variance-boost saltea τ**: Ruido gaussiano(0, 0.15) en MD3 contender matches; mantener Poisson independiente evita rebuild costoso.
23. **`pyproject.toml`**: Build con setuptools, entry point `prode-mundial`, pytest config con `testpaths` + `pythonpath`.
24. **Retry exponential backoff**: `scraper.py` 4 reintentos (2s/4s/8s/16s), `stats_scraper.py` 3 reintentos con timeout separado connect=10s/read=30s.
25. **`players.json` es `{team: [players]}`**: No `{player_name: data}`. Requiere `get_player_team()` para lookup inverso.
26. **Top scorer exponential formula**: `w = max(raw ** 1.8, 0.001)` concentra goles en estrellas; `league_boost` solo premia (×1.3), nunca penaliza (×1.0 todas las demás ligas).
27. **`PENALTY_TAKERS`**: 144 jugadores con nombres exactos del `players.json` y tabla de correcciones manuales para variaciones conocidas.
28. **Análisis narrativo offline**: Sin APIs externas, ~25 templates condicionales. Se genera en `main.py` y se guarda en JSON, no se calcula en la GUI.
29. **Display del análisis**: Badge de recomendación (Frame colorido) + Text widget (read-only, expandable via grid weight=1) en `_match_card()`. Layout grid: badge→text→sep→prob→stars→score→footer.
30. **build_exe.bat hidden imports**: Requiere `prode_mundial.analysis` y `prode_mundial.friendlies_data` como hidden imports para PyInstaller.
31. **Icono del Mundial**: Se usó `2026-FIFA-Logo.png` (1080×1080) convertido a `.ico` multi-size (16×16 a 256×256) vía PIL. `build_exe.bat` incluye `--icon`, `--version-file version_info.txt`, `--noupx` para reducir falsos positivos antivirus.
32. **version_info.txt**: Metadatos VSVersionInfo con CompanyName "Lucas Congil Hadla", FileDescription, FileVersion 1.0.0, Copyright. Incrustado en .exe via `--version-file`.
33. **Real Results System (Bloque Q)**: `real_results.py` con 6 funciones stateless que cargan resultados reales de MD1, computan forma real (9-componente, -10..+10), trackean suspensiones (2 amarillas o 1 roja = baja), inyectan goles/asistencias extra en `player_stats`, ajustan `goals_conceded_avg` por errores, y modulan `height_advantage` vía `_aerial_modifier` basado en duelos aéreos. `predictor.py` acepta `real_form_a/b`, `extra_goals_a/b`, `suspended_a/b`. `bracket.py` detecta partidos reales con `_find_real_result()` y propaga estado a MD2/MD3. `main.py` flag `--results path/to/file.json`. Pesos rebalanceados: `real_match_form` 5% financiado de `morale` 2→1%, `history` 4→3%, `foreign_pct` 3→2%, `odds` 3→2%, `travel` 3→2%.

## Historial de Cambios

### Fase 4 - Correcciones en predictor.py

1. **Pesos sumaban 110%** → Redistribuidos a 100%, eliminados `fanbase` y `randomness`.
2. **Redundancia (multicolinealidad)** → `team_strength` ya NO incluye `market_value`. `fanbase` absorbido por `home_advantage`.
3. **Fórmula de goles esperados** → Cruza ataque vs defensa: `base_A = (goals_scored_avg_A + goals_conceded_avg_B) / 2`.
4. **Randomness eliminado** → `random.gauss(0, 0.7) * 10` eliminado de `total_diff`.
5. **Nuevo factor**: `player_stats` (10%).

### Bloque A - Fix fixture/venue bugs

- Group L corregido: England vs Croatia, Ghana vs Panama, England vs Ghana, Panama vs Croatia.
- Conflictos horarios resueltos (Ecuador→Germany a Houston, Netherlands→Sweden a Vancouver, Norway→Iraq a San Francisco).
- Venues R32/R16 actualizados al bracket oficial FIFA 2026.

### Bloque B - Market Value Parser + Estimaciones

- Fix `parse_market_value()`: agregado soporte para sufijo alemán "Mio".
- `_MARKET_VALUE_ESTIMATES` para 48 equipos como fallback (France 1100M → Curacao 5M).

### Bloque C - Team Data Calibrations

- 9 TM_TEAM_OVERRIDES para mapeo de nombres (Cape Verde→Cabo Verde, South Korea→Korea Republic, etc.).
- Germany form_streak: 1.0 → 0.70.
- Tiers recalibrados (Croatia 4→3, Uruguay 4→3, USA 4→3, etc.).
- FANBASE recalibrado post-clasificación.

### Bloque D - Temperaturas de sedes

- Verificadas contra worldcuptourism.com. Todos los valores correctos. Sin cambios.

### Bloque E - Ajustar modelo

- `calculate_team_strength` elimina form_score y goals_score (redundantes).
- Pesos rebalanceados (player_stats 15%, team_strength 25%, home_advantage 10%).
- `is_neutral` en KO stages reduce bonos de localía ~50%.

### Bloque F - Re-ejecutar stats_scraper

- Campos renombrados de `_2025` a `_2026`. Caché migrado sin re-scrapeo.

### Bloque G - 4 nuevos factores

- `rest_days`: penalidad si <4 días entre partidos.
- `travel_fatigue`: penalidad por km acumulados viajando.
- `squad_depth`: ventaja por profundidad de banquillo (5 sustituciones).
- `jet_lag`: penalidad por diferencia horaria sede vs país de origen.
- `VENUE_TIMEZONES`, `HOME_TIMEZONES`, `SQUAD_DEPTH` en data.py.
- Team history tracking en bracket.py (`compute_team_history`, `_update_history`).

### Bloque H - Fair Play + FIFA tiebreaker + safety net

- `_CONF_CARD_RATES`: yellow_rate y red_rate por confederación.
- `simulate_match_cards()` en predictor.py.
- `_sort_group()` con cascada FIFA Artículo 13.
- `_h2h_matches` global para mini-tabla H2H.
- Safety net KO via ranking FIFA.

### Bloque I - Fix probabilidades

- Ruido aditivo eliminado de las 1000 sims.
- Confidence = probabilidad del winner real (no del resultado más probable).

### Bloque J - Top scorer + ejecutar.bat

- `top_scorer.py`: distribución Poisson de goles entre jugadores con pesos posicionales.
- `main.py`: flag `--goleadores`, seed determinista `random.seed(0)`.
- `ejecutar.bat`: menú interactivo con 5 opciones.

### Bloque K - Ensemble 100 seeds

- Implementado y luego reemplazado por score promedio de 1500 sims (Bloque M).

### Bloque L - Optimización de factores

- Eliminados age_penalty y jet_lag. Agregados experience, trophy_pedigree, height_advantage, club_chemistry desde Wikipedia.
- player_stats ponderado por minutes_2026. squad_depth dinámico desde players.json.

### Bloque M - Score promedio de 1500 sims

- Eliminado ensemble de 100 seeds. Score final = promedio redondeado de 1500 Poisson draws.
- Siempre reproducible (seed 42). Sin randomness.

### Bloque N - Factor Stakes (3ª fecha)

- `classify_stakes()`: qualified (−1), contender (+1), eliminated (−2) según tabla parcial tras MD2.
- Varianza extra `gauss(0, 0.15)` en λ cuando al menos un equipo es contender en MD3.
- 24/24 MD3 matches con stakes poblados. 48/48 MD1/MD2 sin cambios.

### FIXTURES - Corrección vía ESPN (Jun 2026)

- Bloque FIXTURES reemplazado completamente: 72 tuplas con horarios ART (UTC-3) desde ESPN.
- Todos los equipos, sedes, fechas y orden cronológico corregidos.
- Eliminado `imput/resultados_reales.xlsx`.
- `build_exe.bat` corregido a release mode (`--windowed`, `ProdeMundial2026`, sin `--debug`).

### Friendlies Data - 57 amistosos (Jun 2026)

- `friendlies_data.py`: dataset de 57 amistosos (22 may – 10 jun 2026).
- `compute_friendly_form()`: puntaje compuesto escalado -10 a +10.
- `get_friendly_scorers()`: lista de goleadores en amistosos para boost.
- Factor `friendly_form` 2% en predictor.py. `morale` reducido de 4% a 2%.
- Export a `output/friendlies.json`.

### Bloque Ñ - Top Scorer Model

- Fórmula exponencial `w = max(raw ** 1.8, 0.001)` sin piso artificial.
- `_league_boost()`: ×1.3 para clubes en Top 5 ligas, ×1.0 para todas las demás (nunca penaliza).
- `_penalty_boost()`: ×1.5 (#1), ×1.2 (#2), ×1.0 (#3) según `PENALTY_TAKERS`.
- `TOP_SCORER_CANDIDATES`: 27 estrellas con boosts fijos (Messi 1.8, Kane 1.6, Mbappé 1.6, etc.).
- Boost experiencia internacional (+30%) + friendly boost (+30%).
- `data.py`: agregados `PENALTY_TAKERS` (144), `TOP_SCORER_CANDIDATES` (27), `_TOP_LEAGUE_CLUBS` (~120).
- Resultado actual: Mbappé 13, Havertz 10, Ronaldo 9, Kane 9, Messi 7.

### Bloque O - Análisis Narrativo PRODE

- `analysis.py`: motor de narración offline con 3 secciones (Recomendación, Análisis, Veredicto).
- Datos usados: `get_team()`, `compute_friendly_form()`, `get_team_weights()`, `PENALTY_TAKERS`, `INJURED_OUT`, factores del match.
- `output.py`: inyecta campo `"analysis"` en `fase_grupos.json` y `eliminatorias.json`.
- `gui.py`: muestra badge colorido + Text widget (expandable via grid weight=1) en `_match_card()`. Layout grid: badge→text→sep→prob→stars→score→footer.
- `build_exe.bat`: agregados `--hidden-import prode_mundial.analysis` y `--hidden-import prode_mundial.friendlies_data`.

### Bloque P - Icono + version_info.txt + --noupx

- `version_info.txt`: metadatos VSVersionInfo (CompanyName "Lucas Congil Hadla", FileDescription, FileVersion 1.0.0, Copyright).
- `build_exe.bat`: agregados `--noupx` (reduce falsos positivos antivirus), `--version-file version_info.txt`, `--icon wc26_logo.ico`.
- Icono `.ico` multi-size generado desde `2026-FIFA-Logo.png` (1080×1080) vía PIL.
- .exe recompilado con icono del Mundial 2026, commit `6453c64`.

### Bloque Q - Real Results System

- `real_results.py`: 6 funciones (carga, forma 9-componente, suspensiones 2A/1R, goles/asis extra, ajuste goles concedidos, modulador aéreo).
- `output/real_results.json`: MD1 Grupo A completo (México 2-0 Sudáfrica, Corea 2-1 Chequia) con todas las stats (xG, posesión, tiros, pases, corners, duelos aéreos, tarjetas, errores, atajadas).
- `predictor.py`: factor `real_match_form` 5%, pesos rebalanceados (morale 2→1%, history 4→3%, foreign_pct 3→2%, odds 3→2%, travel 3→2%).
- `predict_match()` acepta `real_form_a/b`, `extra_goals_a/b`, `suspended_a/b`.
- `calculate_player_stats_factor()` inyecta goles/asistencias reales.
- `calculate_squad_depth_factor()` excluye suspendidos.
- `calculate_height_advantage()` modulado por `_aerial_modifier`.
- `bracket.py`: `run_full_simulation(real_results=...)`, `_find_real_result()`, MD1 real salta predicción, estado propagado a MD2/MD3.
- `main.py`: auto-detecta `output/real_results.json` (sin flag `--results`), también chequea MD2 y MD3 si hay resultados reales disponibles.
- 137/138 tests pass (1 pre-existing `test_smoke_run`).

### Bloque R - Caps Data Quality

- **Wikiscraper regex fix**: `\bcap`→`\bcaps`, `[^\n]*`→`[^|\n]*` para evitar regex poisoning en nombres con caracteres Unicode o puntuación
- **Sanity check**: caps >100 → `None` (rechaza valores imposibles)
- **24 players corruptos reparados** en `players.json`:
  - 16 con regex poisoning (nombres con patrones hex como `\u043c\u043e\u0436\u043d\u043e`)
  - 3 con caps incorrectas (Mahrez 100→96, Zouma 16→15, Pau Víctor 7→6)
  - 3 con club_apps/club_goals corruptos
  - 2 con club_name corrupto (wikilinks malformados)

### Bloque S - Friendly Form Improvements

- **Removido France override**: Francia ya no fuerza `friendly_form=0.5`, ahora usa el cálculo normal como todos los equipos
- **Uruguay friendlies**: Agregados 3 amistosos faltantes (vs Ecuador 1-1, Czechia 2-0, Saudi Arabia 2-1) - antes Uruguay tenía 0 partidos
- **Bayesian shrinkage**: `friendly_form` ahora requiere mínimo 5 partidos como base; equipos con menos se shrinkage hacia 0 con peso reducido
- **Tier weighting**: Equipos Tier 1 tienen ×1.2 de peso en `friendly_form` (sus amistosos son más indicativos)
- **Factor `friendly_form`**: Peso 2%, sin cambios. `morale` reducido de 4% a 2% (ya hecho en Bloque Ñ).
- **Simulación regenerada**: Argentina campeón, Francia subcampeón, España 3°. Mbappé 11, Messi 11, Kane 8.

### Bloque T - Real Results Auto-Detection

- **Flag `--results` eliminado** de `main.py`: ahora auto-detecta `output/real_results.json` si existe
- **MD2/MD3 checking**: extendido el chequeo de resultados reales a matchdays 2 y 3 (antes solo MD1)
- **Backward compatible**: si no hay `output/real_results.json`, corre normal sin resultados reales
- **.exe recompilado**: con auto-detección de resultados reales

### Bloque V - Player Ratings System (SQLite + Jugadores Tab)

- **`player_ratings.py`**: Motor de calificaciones con SQLite. Clase `PlayerRatingsDB` con `create_tables()`, `insert_match_ratings()`, `seed_if_empty()`, y 7 funciones de consulta (`get_golden_ball()`, `get_top_by_position()`, `get_best_xi()`, `get_mvp_by_match()`, `get_top_scorers()`, `get_top_assisters()`, `get_mejores_por_fase()`).
- **`_SEED_DATA`**: ~93 jugadores de 6 equipos (Mexico, South Africa, South Korea, Czechia, Canada, Bosnia) con stats de 3 partidos MD1.
- **`_SOFASCORE_NAME_MAP`**: Mapa manual por equipo para traducir nombres de Sofascore a formato `players.json`.
- **`_compute_highlight()`**: Genera stat destacado según posición (GK → atajadas + % pases, DEF → entradas/duelos + % pases, MID → asistencias + % pases, FW → goles + duelos).
- **`db_ratings.db`**: Base SQLite en `output/`, editable con DB Browser for SQLite.
- **`jugadores_destacados.json`**: Export generado por `PlayerRatingsDB.export_standings()` con 7 tablas para la GUI.
- **GUI**: Tab "Jugadores" entre Goleadores y Bonus con 8 secciones (Golden Ball, Top por Posición, Once Ideal, Mejores por Fase, MVP por Partido, Goleadores Reales, Asistidores Reales). Muestra "⏳ Sin datos aún" cuando no hay data para una fase.
- **`output.py`**: `export_player_standings()` llama a `PlayerRatingsDB().seed_if_empty()` + `export_standings()`. Integrado en `export_all()`.
- **`main.py`**: Auto-inicializa DB y exporta jugadores destacados. También exporta en modo `--goleadores`.
- **SQLite editable**: El usuario puede abrir `output/db_ratings.db` con DB Browser for SQLite y editar/agregar ratings de partidos reales.

### Bloque U Fix 2 - Geometry Manager Conflict (GUI Crash Fix)

- **Error encontrado**: `_show_ko_match()` en `gui.py:604` agregaba un Label a `card` con `.pack()`, pero `_match_card()` ya usaba `.grid()` dentro de `card` → `TclError: cannot use pack inside grid slaves`.
- **Causa raíz**: Esto causaba la "pantalla negra" — el error en `_build_ko_tab()` propagaba hasta `ProdeGUI.__init__()`, que fallaba después de `root.deiconify()` (ventana ya visible pero vacía).
- **Fix principal**: Movido el label de ronda KO a `self._card_frame_ko` (padre, no dentro de `card`), usando `.pack()` consistente con el layout existente.
- **Safety net**: Envueltos todos los `_build_*_tab()` en try/except con traceback impreso y mensaje de error en la tab. Previene que una falla aislada deje toda la ventana en negro.
- Commit: sesión 2026-06-12.

### Bloque U - GUI Layout Fixes

- **Info tab actualizado**: 18→19 factores, pesos corregidos (foreign_pct 3→2%, history 4→3%, morale 2→1%, odds 3→2%, travel 3→2%), agregado párrafo real_match_form
- **X2 fix**: `optimizer.py:analyze_x2()` filtra `result_type: "real"` para no mostrar resultados reales como X2
- **Subcampeón fix**: `output.py` exporta campo `loser` en KO JSON para que la GUI muestre el subcampeón
- **Goles reales visibles**: `bracket.py:_apply_real_result()` guarda `goals_scorers`, `output.py` lo exporta, `gui.py:_match_card()` lo muestra abajo del score
- **Grid layout _match_card**: reemplazado pack por grid con contador `row` dinámico; `text_frame` es única fila con weight=1; score siempre visible. Commit `984ab3e`.
- **Fix score row 3-column grid**: `inner.place()` reemplazado por grid de 3 columnas en `vs_frame` para flanqueo simétrico de nombres. Goals reales migrado de pack a grid. Commit `00514c4`.

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

# Validación histórica (448 partidos 1998-2022)
python prode_mundial/validation.py

# Optimizador (modo normal)
python prode_mundial/optimizer.py

# Optimizador (cargar MC cache)
python prode_mundial/optimizer.py --load

# GUI tkinter
python prode_mundial/gui.py

# Compilar .exe (PyInstaller)
.\build_exe.bat

# Git push
git add -A; git commit -m "mensaje"; git push origin master
```

## Próximos Pasos

✅ **Proyecto completo** - Los 135 partidos del Mundial 2026 analizados con 19 factores + Dixon-Coles τ + Poisson (1500 sims promedio). Resultados exportados a CSV/JSON en `output/`.
✅ **FIXTURES corregidos** - 72 partidos de grupos con horarios ART oficiales desde ESPN (commit `80609ea`).
✅ **build_exe.bat** - Compilación release (`--windowed`, `ProdeMundial2026`, sin debug).
✅ **Bloque P** - Icono del Mundial 2026, version_info.txt, --noupx anti-falso-positivo.
✅ **Bloque Q** - Real Results System (factor real_match_form 5%, suspensiones, goles extra, auto-detection).
✅ **Bloque R** - Caps data quality: wikiscraper regex fix + sanity check + 24 corrupt players reparados.
✅ **Bloque S** - Friendly form improvements: removido France override, Uruguay friendlies, Bayesian shrinkage, tier weighting.
✅ **Bloque T** - Real results auto-detection: removido flag `--results`, auto-detect MD1/MD2/MD3.
✅ **Bloque U** - GUI layout fixes: grid _match_card, info tab actualizado, X2 filter, subcampeón fix, goles reales visibles. Commits `984ab3e`, `00514c4`.
✅ **Bloque U Fix 2** - Geometry Manager Conflict en `_show_ko_match()`: label de ronda KO movido fuera del `card` para evitar `TclError: cannot use pack inside grid slaves`. Safety net: todos los `_build_*_tab()` envueltos en try/except con error visible en la tab. Pantalla negra solucionada.
✅ **Bloque V** - Player Ratings System mejora: `seed_if_empty()` ahora recarga DB desde cero permitiendo agregar nuevos seed blocks sin borrar DB manualmente. `_SOFASCORE_NAME_MAP` ampliado con USA y Paraguay. `_SEED_DATA` agregado 4° bloque USA-Paraguay con 32 jugadores desde Sofascore. `real_results.json` actualizado con stats mejoradas de Sofascore para los 4 partidos MD1. `gui.py`: `_safe()` reemplazado por identidad (preserva acentos/ñ), Info tab layout reemplazado Canvas+scroll_frame por Text+Scrollbar directo, contenido de Info actualizado con 4 partidos reales y sistema de ratings.
✅ **Bloque W** - _SOFASCORE_NAME_MAP expandido con Qatar, Switzerland, Brazil, Morocco (14 entries). _SEED_DATA expandido con 2 nuevos bloques: Qatar-Switzerland (32 players) y Brazil-Morocco (32 players). 6 seed blocks total, ~192 player ratings.
✅ **Bloque X** - GUI Modernization: font system (Bebas Neue, Teko download/load via ctypes), maximized window, multi-column Groups grid (compact cards), multi-column KO grid, Segoe UI bold italic buttons, Bebas Neue headers, green accent #00FF66, `build_exe.bat` font assets.

## Sesiones

|Fecha|Acción|Detalle|
|-------|--------|---------|
|2026-06-08|`git reset --hard origin/master`|Reposincronizado a `e9fe83f` (Bloque N) - trajo display.py, optimizer.py, stats_scraper.py, top_scorer.py, ejecutar.bat, AGENTS.md, opencode.jsonc, outputs|
|2026-06-08|Instalación LSP|Se instaló `python-lsp-server` 1.14.0 (faltaba post-clone). `opencode.jsonc` ya tenía `"lsp": true`|
|2026-06-08|Fase 4a: pyproject.toml + __init__.py|Package instalable con `pip install -e .`, entry point `prode-mundial`, pytest config integrado|
|2026-06-08|Fase 4b: Retry resilience|`_fetch_with_retry()` en scraper.py (4 retries, 2s/4s/8s/16s), `_get()` en stats_scraper.py (3 retries, connect/read timeout separado)|
|2026-06-08|Fase Tests + Dixon-Coles τ|4 nuevos test files (83 tests), τ correction (ρ=-0.15, joint dist 16×16), 129 tests total, todo pass|
|2026-06-08|**Hito 5.1**: README.md + docstrings|Resumen ejecutivo + módulo/función docstrings en 12 archivos fuente (~136 funciones). README.md con 6 comandos esenciales|
|2026-06-08|**Hito 5.2**: validation.py (448 partidos)|Validación histórica 1998-2022 con 9 factores activos. Precisión global: **51.8%**. Datos embebidos (FIFA rankings, resultados, venues por torneo)|
|2026-06-08|**Hito 5.3**: Optimizador mejorado|`--load` flag (carga MC cache), factor-based plausibility (market_value + avg_caps boost), percentiles P10/P50/P99 via distribución binomial|
|2026-06-08|**Hito 5.4**: GUI tkinter + .exe|`gui.py` con 4 tabs (Grupos/KO/Estadisticas/Goleadores), 3D buttons, tooltip confianza, navegación por flechas. `build_exe.bat` para PyInstaller|
|2026-06-08|**Tests**: 138 tests|9 nuevos tests de validation.py. Suite completa 138/138 pass|
|2026-06-08|**FIXTURES**: Corrección completa vía ESPN|Bloque FIXTURES reemplazado (72 tuplas) con horarios oficiales en ART (UTC-3) desde ESPN. Se eliminó `imput/resultados_reales.xlsx`. `build_exe.bat` corregido a release mode (`--windowed`, `ProdeMundial2026`, sin `--debug`). Commit `80609ea`, push a master.|
|2026-06-09|**Friendlies Data**|`friendlies_data.py`: dataset de 57 amistosos (22 may–10 jun 2026). Factor `friendly_form` 2%. Export a `output/friendlies.json`.|
|2026-06-09|**Top Scorer Model**|Fórmula exponencial (`raw**1.8`), `_league_boost()` solo premia (×1.3), `_penalty_boost()` según `PENALTY_TAKERS`, `TOP_SCORER_CANDIDATES` con 27 estrellas. Resultado: Messi 9, Havertz 9, Kane 8, Mbappé 8.|
|2026-06-09|**Análisis Narrativo PRODE**|`analysis.py` con 3 secciones (Recomendación → Análisis → Veredicto). Inyectado en JSON via `output.py`. Display en GUI arriba del score. `build_exe.bat` actualizado con hidden imports.|
|2026-06-09|**Corrección ortográfica analysis.py**|10 fixes de tildes/ortografía en castellano argentino (arrasó, definitiva, ABIERTO, prevé, táctico, localía, presión, palmarés, química, compañeros). Output JSONs regenerados. .exe recompilado. Push a master.|
|2026-06-09|**Fix analysis fallback (33 partidos sin narrativa)**|`_build_recommendation()` retornaba `None` cuando ningún bloque condicional matcheaba → TypeError silencioso → análisis vacío. Se agregó fallback `PARTIDO DISPUTADO` para cubrir el 100% de los partidos. JSONs regenerados, .exe recompilado.|
|2026-06-09|**Splash Screen + Firma en GUI**|`splash.py`: pantalla de carga con imagen de fondo (cover mode), barra verde 3D, 12 frases animadas. `bracket.py`: `progress_callback` en `run_full_simulation()`. `gui.py`: integración de splash, refactor para evitar doble simulación. `build_exe.bat`: `--add-data imput` + `--hidden-import splash`. Status bar con autor. Commit `04e6ad2`.|
|2026-06-09|**Bloque P: Icono + version_info + --noupx**|`version_info.txt` con metadatos VSVersionInfo. `build_exe.bat`: `--noupx`, `--version-file`, `--icon`. .ico generado desde `2026-FIFA-Logo.png` vía PIL. Icono anterior (balón PIL) reemplazado. .exe recompilado con icono del Mundial 2026. Commit `6453c64`, push a master.|
|2026-06-10|**GUI layout: score abajo + equipos centrados + text scroll**|`gui.py:_match_card()`: Canvas+Scrollbar envolvente eliminado, Text widget height=8→12 con scrollbar interno, score movido al final (Badge→Text→Sep→Prob→Stars→Score→Footer), padx equipos 30→12 para centrar cerca del resultado. .exe recompilado.|
|2026-06-10|**Fix historial mundialista en ¿Cómo funciona?**|Corregida la descripción de títulos mundiales: Francia con dos, Uruguay con dos, España con uno (vs "Francia e Inglaterra" que omitía a Uruguay y España). .exe recompilado.|
|2026-06-11|**Friendlies 10 Jun: Portugal 2-1 Nigeria + Bolivia 0-4 Algeria**|Agregados 2 amistosos del 10/6 a `friendlies_data.py`: Portugal 2-1 Nigeria (Neto 23', Conceição 75'; Adams 37') y Bolivia 0-4 Algeria (Mandi 45', Gouiri 57' 59', Hadj Moussa 61'). Outputs regenerados, .exe recompilado.|
|2026-06-11|**Spanish team names + bonus tab bugfix**|`TEAM_ES` dict (48 equipos) + `team_name_es()` en `data.py`. Aplicado en: score labels, prob labels, tabla posiciones, terceros, goleadores tab, bonus tab (campeón/subcampeón/tercero/semifinalistas/clasificados/x2/extra stats). Bug `wcard→winner` en `_compute_bonus_data()`. Exe recompilado. Commit `973a727`, push a master.|
|2026-06-11|**Factor arquero penales + fix veredicto + fix draw text**|`data.py`: `_PENALTY_SAVERS` dict (27 equipos con rating manual, 21 por fórmula), `_compute_gk_penalty_save()`, `gk_name`/`gk_penalty_save` en `_enrich_teams()`. `predictor.py`: `gk_factor` en tiebreaker de penales (`(gk_a - gk_b) * 3`). `analysis.py`: fix veredicto (muestra ganador aun si ambos <50%), fix draw text (nuevo `_VERDICT_B_HIGH` para ≥28%), penalty narrative en KO (menciona arqueros especialistas). Outputs regenerados. Commit push.|
|2026-06-11|**Fix Wikipedia cache Ederson + Saadane**|Cache entries `"Ederson": {}` y `"Marwane Saadane": {}` → datos reales desde páginas correctas: `Éderson (footballer, born 1999)` (3 caps, Atalanta, 4 trofeos) y `Marwane Saâdane` (6 caps, Al-Fateh, 2 trofeos). Wikiscraper re-ejecutado: 1116/1248 encontrados (+2). Simulación regenerada: **España campeón**, Alemania subcampeón, Francia 3°, Mbappé 13 goles.|
|2026-06-11|**Refactor _match_card layout**|Score row + footer movidos a `side=tk.BOTTOM`, text widget expandido (sin scrollbar, sin height fijo), pads de equipos reducidos (12→6), font score 36→32, nombres 18→14. .exe recompilado.|
|2026-06-12|**Real Results System (Bloque Q)**|`real_results.py`: 6 funciones (carga, forma 9-componente, suspensiones 2A/1R, goles/asis extra, ajuste goles concedidos, modulador aéreo). `output/real_results.json`: MD1 Grupo A (México 2-0 Sudáfrica, Corea 2-1 Chequia). `predictor.py`: factor `real_match_form` 5%, pesos rebalanceados (morale/history/foreign_pct/odds/travel reducidos). `bracket.py`: `run_full_simulation(real_results=...)`, saltos de predicción MD1, trackeo de estado (suspensiones/goles extra/forma/moduladores) propagado a MD2/MD3. `main.py`: flag `--results`. Outputs regenerados. .exe recompilado. 137/138 tests pass (1 pre-existing). Commit push.|
|2026-06-12|**Bloque R: Caps data quality**|Wikiscraper regex fix: `\bcap`→`\bcaps`, `[^\n]*`→`[^|\n]*` para evitar regex poisoning en nombres con caracteres Unicode o puntuación. Sanity check: caps >100 → `None`. 24 players corruptos reparados (16 regex-poisoned, 3 caps, 3 club stats, 2 club names).|
|2026-06-12|**Bloque S: Friendly form improvements**|Removido France override (siempre 0.5). Agregados 3 amistosos de Uruguay (vs Ecuador, Czechia, Saudi Arabia). Bayesian shrinkage: mínimo 5 partidos de base. Tier weighting: Tier 1 ×1.2. Simulación regenerada: **Argentina campeón**, Francia subcampeón, España 3°. Mbappé 11, Messi 11, Kane 8. 137/137 tests pass. .exe recompilado. Commit `97bec0a`.|
|2026-06-12|**Bloque T: Real results auto-detection**|Removido flag `--results` de `main.py`. Auto-detecta `output/real_results.json`. Real result checking extendido a MD2 y MD3 (antes solo MD1). .exe recompilado. Commit `1a6d672`.|
|2026-06-12|**Fix 4 GUI issues**|Info tab outdated (19 factores, pesos correctos, real_match_form), X2 excluye resultados reales, subcampeón muestra nombre en vez de "?", goles reales se muestran con goleadores. Commit `dd87058`.|
|2026-06-12|**Grid layout _match_card**|Reemplazado pack por grid con contador `row` dinámico; `text_frame` es única fila con weight=1 y se expande; score siempre visible abajo. Commit `984ab3e`.|
|2026-06-12|**Fix score row 3-column grid**|Score row reemplazado: `inner.place()` → grid de 3 columnas en `vs_frame` (col 0 weight=1 equipo A sticky=e, col 1 weight=0 score centrado, col 2 weight=1 equipo B sticky=w). Goals reales migrado de pack a grid. Commit `00514c4`.|
|2026-06-13|**Bloque V: Player Ratings + Sofascore + fix GUI**|`player_ratings.py`: `_SOFASCORE_NAME_MAP` ampliado (USA, Paraguay), `_SEED_DATA` con 4° bloque USA-Paraguay (32 jugadores), `seed_if_empty()` ahora recarga DB desde cero. `real_results.json` actualizado con stats mejoradas de Sofascore para 4 partidos MD1 (incluye USA 4-1 Paraguay). `gui.py`: `_safe()` reemplazado por identidad (preserva acentos/ñ), Info tab layout cambiado a Text+Scrollbar directo, contenido actualizado. `AGENTS.md` actualizado. Outputs regenerados.|
|2026-06-13|**Bloque W: Expand _SEED_DATA + _SOFASCORE_NAME_MAP**|`player_ratings.py`: `_SOFASCORE_NAME_MAP` expandido con Qatar (6), Switzerland (2), Brazil (9), Morocco (16) — 33 entries total. `_SEED_DATA` agregados bloques Qatar-Switzerland y Brazil-Morocco (32+32 players, ~192 total). Fix script bugs (closing brace dedup). Simulación regenerada: **Argentina campeón**, Francia subcampeón, España 3°. Mbappé 9, Messi 10, Kane 8. Outputs regenerados, .exe recompilado. Push a master.|
|2026-06-14|**Bloque X: GUI Modernization**|`gui.py`: font system (Bebas Neue, Teko download/load via ctypes gdi32 FR_PRIVATE), maximized window with responsive fallback, multi-column Groups grid (3 cols × compact cards + canvas+scroll), multi-column KO grid grouped by round, `_styled_btn` Segoe UI bold italic, Bebas Neue headers green accent #00FF66, compact match cards with new `_compact_match_card()` method (only badge+score+prob+names, no analysis). `build_exe.bat`: `--add-data` fonts.|
|2026-06-14|**Real Results: Qatar & Brazil added**|`real_results.json` ampliado de 4 a 6 partidos: Qatar 1-1 Switzerland y Brazil 1-1 Morocco con stats agregadas desde `_SEED_DATA` vía script. Stats de pases, duelos aéreos, atajadas computados de datos de Sofascore de `player_ratings.py`. xG/posesión/tiros estimados. **Impacto**: Grupo B ahora Suiza 5pts-Canada 5pts (Qatar 1pt), Grupo C Morocco 7pts-Brazil 7pts (Marruecos 1° por tiebreaker). Argentina campeón, Mbappé 10, Messi 12, Kane 10. Outputs regenerados, .exe recompilado.|
|2026-06-14|**Bloque Y: Haiti 0-1 Scotland (7° resultado real)**|`output/players.json`: 7 alturas corregidas (Arcus, Ade, Providence, Hendry, McGinn, McLean, Adams) + 52 market values poblados (Placide 155K, Bellegarde 17.6M, McTominay 38M, etc.). `player_ratings.py`: `_SOFASCORE_NAME_MAP` ampliado con Haiti (3) y Scotland (2); `_SEED_DATA` agregado bloque MD1_Haiti_Scotland (30 players, ratings Sofascore). `output/real_results.json`: 7° partido agregado (Haiti 0-1 Scotland, xG 1.21-1.05, McGinn 28', Boston). `gui.py`: BUG 5 fix — `_compact_match_card()` ahora muestra goleadores reales (⚽). **Impacto**: Grupo C Brazil 7pts-Morocco 5pts-Scotland 4pts (3° clasificado)-Haiti 0pts. Argentina campeon, Francia subcampeon, Espana 3°. Messi 11, Mbappe 9, Kane 8. Outputs regenerados, .exe recompilado. Push a master.|
