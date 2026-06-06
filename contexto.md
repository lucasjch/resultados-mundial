# Prode Mundial 2026 — Documentación del Proyecto

## Requisitos

```bash
# Instalación (única dependencia externa)
pip install requests

# El resto es standard library: json, re, csv, os, sys, math, random, collections, itertools, time
```

## Quick Start

```bash
cd prode_mundial
python wikiscraper.py          # ~40 min: scrapea 1245 jugadores (checkpoint cada 50)
python main.py                 # ejecuta predicción completa
```

## Objetivo
Script en Python que analiza los 135 partidos del Mundial 2026 y predice resultados para completar un prode. Exporta a CSV y JSON.

## Estructura del Proyecto

```
prode_mundial/
├── scraper.py        # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py           # Datos de equipos, sedes, fixture, bases operativas
├── predictor.py      # Motor de 15 factores ponderados + simulación Poisson
├── stats_scraper.py  # Scraper de estadísticas individuales (Transfermarkt API)
├── bracket.py        # Bracket oficial 2026 (R32, R16, QF, SF, 3°, Final)
├── output.py         # Exportación CSV/JSON
├── main.py           # Orquestador principal
├── wikiscraper.py    # Scraper individual de Wikipedia vía API
└── output/           # Resultados generados
    ├── players.json          # 1245 jugadores (enriquecido vía wikiscraper)
    ├── wiki_cache.json       # Caché de Wikipedia scraping
    ├── fase_grupos.csv/json  # Partidos de grupos
    ├── tabla_posiciones.csv  # Posiciones finales
    ├── eliminatorias.csv     # Llaves KO
    └── prode_completo.csv    # Prode completo (135 partidos)
```

## Pipeline

### 1. Scraping (`scraper.py`)
- **Promiedos** (28 equipos): parsea HTML `<tr>`/`<td>` — nombre, dorsal, edad, altura
- **Transfermarkt** (20 equipos): `html.unescape()` + regex — nombre, posición, DOB, valor de mercado
- Total: **1245 jugadores** de 48 equipos
- Output: `output/players.json`

### 1b. Wikipedia Stats (`wikiscraper.py`)
- Scraper vía API REST de Wikipedia (`action=parse` + `action=query`)
- Para cada jugador, extrae del infobox:
  - `intl_caps`, `intl_goals` (selección mayor — descarta juveniles por regex `U\d+`)
  - `club_apps`, `club_goals` (club actual = entrada `yearsN` con N más alto)
  - `current_club`, `club_name` (limpia wikilinks tipo `[[Real Madrid CF|Real Madrid]]`)
  - `height` (parsea `1.80 m` desde el texto)
- De la sección **Honours**: lista de títulos con categoría y `trophy_count`
- **Fix `_extract_num()`**: maneja valores con wikilinks tipo `[[List of...|56]]` o templates `{{efn|...}}`
- **Incremental save**: checkpoint cada 50 jugadores para reanudar en caso de timeout
- **UTF-8 fix**: requiere `$env:PYTHONIOENCODING='utf-8'` en Windows para caracteres acentuados
- Caché en `output/wiki_cache.json` — evita re-scrapear en ejecuciones posteriores
- Checkpoint cada 50 jugadores — guarda `wiki_cache.json` y `players.json` incrementalmente
- Enriquecimiento directo de `output/players.json` con todos los campos nuevos
- Input: 1245 jugadores · Output: ~40 min (delay 1s entre requests) · Resultado: 1112/1245 encontrados (89%)

### 1c. Transfermarkt Stats (`stats_scraper.py`)
- Scraper vía API `tmapi-alpha.transfermarkt.technology` (sin rate limit)
- Para cada equipo consulta `/quickselect/players/{teamId}`, luego `/player/{playerId}/performance-game` con `seasonId: 2025`
- Extrae goles, asistencias, minutos de la temporada 2025/26
- **Fuzzy matching**: `SequenceMatcher` ≥0.75 con diferencia ≥0.1 del segundo mejor + limpieza de sufijos posicionales
- **TM_TEAM_OVERRIDES**: 9 correcciones de nombre (e.g. `Cape Verde→Cabo Verde`, `South Korea→Korea Republic`) para mapear 49 nombres
- Caché en `output/tm_stats_cache.json` — evita re-scrapear
- Output: enriquece `output/players.json` con campos `goals_2026`, `assists_2026`, `minutes_2026`
- Resultado: 1205/1245 jugadores con stats (96.8%)
- Ejecución: `$env:PYTHONIOENCODING='utf-8'; python stats_scraper.py` (o con `--force` para ignorar caché)

### 2. Datos (`data.py`)
- `TEAMS`: 48 equipos con rank, tier, confederación, coach, capitán, temperatura/altitud local, racha (`form_streak`), historial mundialista, jugadores clave, goles promedio, diáspora en USA
- `VENUES`: 16 sedes con país, estadio, capacidad, techo, temperatura, altitud
- `GROUPS`: 12 grupos (A-L) de 4 equipos
- `FIXTURES`: 72 partidos de grupos con fecha, hora, sede
- `CITY_COORDS`: coordenadas de 41 ciudades (sedes + bases operativas)
- `BASE_CAMPS`: base de concentración real de cada selección
- `VENUE_TIMEZONES`: UTC offset para las 16 sedes
- `HOME_TIMEZONES`: UTC offset para los 48 equipos
- `SQUAD_DEPTH`: ratio de jugadores `impact` / `key_players` escalado 0–10
- `_FOREIGN_PCT_ESTIMATES`: % de jugadores en el extranjero por confederación
- `_FANBASE`: popularidad global (0–8), recalibrada post-clasificación
- `_MARKET_VALUE_ESTIMATES`: valores estimados para 48 equipos (France 1100M → Curacao 5M), usado como fallback cuando player-level es null
- `_enrich_teams()`: integra `players.json` en cada equipo con 6 campos extra

### 3. Predicción (`predictor.py`)
15 factores ponderados + Poisson (1000 sims): `total_diff = Σ(factor_i × peso_i)`, sin randomness aditivo:

| Factor | Peso | Descripción |
|--------|:----:|-------------|
| `team_strength` | 17% | Solo rank + tier (sin form/goals) |
| `market_value` | 11% | Diferencia de valor de plantilla (escala log) |
| `player_stats` | 12% | Goals + 0.5×Assists promedio por jugador (temporada 2025/26) |
| `home_advantage` | 8% | Localía CONCACAF + fanbase/diaspora; `is_neutral` reduce bonos en KO |
| `climate` | 6% | Diferencia térmica, altitud, techo cerrado |
| `travel` | 3% | Distancia base → sede (haversine) |
| `history` | 4% | Mejor actuación histórica en Mundiales |
| `morale` | 4% | `form_streak` del equipo |
| `age_penalty` | 3% | Penalización por desviación de edad óptima (27) |
| `foreign_pct` | 5% | % de jugadores en ligas extranjeras |
| `rest_days` | 7% | Penalidad si <4 días entre partidos (3 pts por día faltante) |
| `squad_depth` | 7% | Ratio de jugadores de impacto en plantilla (aprovecha 5 sustituciones) |
| `travel_fatigue` | 5% | Km totales acumulados viajando entre sedes |
| `jet_lag` | 3% | Diferencia horaria sede vs país de origen (0.7 pts/hora, máx 5) |
| `odds` | 5% | Cuotas DraftKings pre-torneo |
| `randomness` | — | Eliminado. Antes: `gauss(0,0.7)×10` |

Fórmula de goles esperados (cruza ataque vs defensa):
```
total_diff = Σ(factor_i × peso_i)   # sin randomness
total_diff_scaled = total_diff / 100

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = max(0.2, min(7.0, base_a * (1 + total_diff_scaled)))
λ_b = max(0.2, min(7.0, base_b * (1 - total_diff_scaled)))
```
Simulación Poisson con 1000 iteraciones. Score = moda de goles.
λ clamp entre 0.2 y 7.0 para evitar valores extremos.

### 4. Bracket (`bracket.py`)
- **Fase de grupos**: 72 partidos, tabla de posiciones con puntos y GD
- **Mejores terceros**: top 8 de 12 terceros clasifican
- **R32**: 16 llaves fijas oficiales (1E vs 3°ABCDF, 1I vs 3°CDFGH, 2A vs 2B, etc.) con venues oficiales FIFA 2026
- **R16**: emparejamientos fijos (M01-M02, M03-M04, ...) con venues actualizados
- **QF, SF, 3°, Final**: bracket estándar
- **Team history tracking**: `compute_team_history()` calcula `last_date`, `last_venue`, `total_travel` por equipo tras grupos; `_update_history()` propaga entre rondas KO acumulando kilómetros y actualizando fechas
- Venues corregidos: Dallas→Toronto, Miami→Los Angeles, Seattle→San Francisco, etc. (Bloque A)
- Conflictos horarios resueltos: Ecuador vs Germany→Houston 20:00, Netherlands vs Sweden→Vancouver 21:00 (Bloque A)

### 5. Exportación (`output.py`)

- `fase_grupos.csv/json`: todos los partidos con probabilidades y desglose de factores
- `tabla_posiciones.csv`: posiciones finales por grupo
- `eliminatorias.csv`: todas las llaves KO
- `prode_completo.csv`: prode completo en un solo archivo

## Bases Operativas Reales

| Selección | Base | Sede/Instalación |
|-----------|------|------------------|
| Algeria | Kansas City | Universidad de Kansas |
| Argentina | Kansas City | Sporting KC Training Center |
| Australia | San Francisco | Oakland Roots & Soul |
| Austria | Goleta | UC Santa Barbara Harder Stadium |
| Belgium | Renton | Seattle Sounders FC |
| Bosnia & Herzegovina | Sandy | RSL Stadium |
| Brazil | New York | Columbia Park |
| Cape Verde | Tampa | Waters Sportsplex |
| Canada | Vancouver | National Soccer Development Centre |
| Colombia | Guadalajara | Academia Atlas FC |
| DR Congo | Houston | Houston Training Centre |
| Ivory Coast | Philadelphia | Philadelphia Union |
| Croatia | Alexandria | Episcopal Institute |
| Curacao | Boca Raton | Florida Atlantic University |
| Czechia | Dallas | Mansfield Multipurpose Stadium |
| Ecuador | Columbus | Columbus Crew Training Center |
| Egypt | Spokane | Gonzaga University |
| England | Kansas City | Swope Soccer Village |
| France | Boston | Bentley University |
| Germany | Winston-Salem | Wake Forest University |
| Ghana | Boston | Bryant University |
| Haiti | New York | Stockton University |
| Iran | Tijuana | Xoloitzcuintle Center |
| Iraq | Greenbrier County | The Greenbrier |
| Japan | Nashville | Nashville SC |
| Jordan | Portland | University of Portland |
| Mexico | Mexico City | CAR |
| Morocco | New York | The Pingry School |
| Netherlands | Kansas City | KC Current Training |
| New Zealand | San Diego | University of San Diego |
| Norway | Greensboro | UNC Greensboro |
| Panama | New Tecumseth | Nottawasaga Training Site |
| Paraguay | San Francisco | Spartan Soccer Complex |
| Portugal | Palm Beach Gardens | Gardens North County Park |
| Qatar | Santa Barbara | Westmont College |
| Saudi Arabia | Austin | Austin FC Stadium |
| Scotland | Charlotte | Charlotte FC |
| Senegal | New York | Rutgers University |
| South Africa | Pachuca | CF Pachuca |
| South Korea | Guadalajara | Chivas Verde Valle |
| Spain | Chattanooga | Baylor School |
| Sweden | Dallas | Dallas FC Stadium |
| Switzerland | San Diego | SDJA |
| Tunisia | Monterrey | Rayados Training Center |
| Turkey | Mesa | Arizona Athletic Grounds |
| USA | Irvine | Great Park Sports Complex |
| Uruguay | Cancun | Mayakoba Training Center |
| Uzbekistan | Atlanta | Atlanta United Training Center |

## Progreso

| Fase | Estado |
|------|--------|
| ✅ **Fase 1** — Wikiscraper (1112/1245 jugadores enriquecidos) | Completado |
| ✅ **Fase 2** — Decidir fuente de asistencias (Transfermarkt API) | Completado |
| ✅ **Fase 3** — Integrar stats individuales como factores en `predictor.py` | Completado |
| ✅ **Fase 4** — Arreglar modelo de predicción (pesos 110→100%, redundancias, nueva fórmula) | Completado |
| ✅ **Fase 5** — Revisar predicciones Grupo A con factores mejorados | Completado |
| ✅ **Fase 6** — Ejecutar simulación completa (`main.py`) | Completado |
| ✅ **Bloque A** — Fix fixture/venue bugs (Group L, conflictos horarios, venues R32/R16) | Completado |
| ✅ **Bloque B** — Market Value Parser + `_MARKET_VALUE_ESTIMATES` | Completado |
| ✅ **Bloque C** — Team Data Calibrations + TM_TEAM_OVERRIDES | Completado |
| ✅ **Bloque D** — Verificar temperaturas de sedes | Completado |
| ✅ **Bloque E** — Ajustar modelo (form/goals, `player_stats` 15%, `is_neutral`) | Completado |
| ✅ **Bloque F** — Re-ejecutar stats_scraper + campos `_2026` | Completado |
| ✅ **Bloque G** — 4 nuevos factores (rest_days, squad_depth, travel_fatigue, jet_lag) | Completado |
| ✅ **Bloque H** — Fair Play + FIFA 2026 tiebreaker cascade + safety net KO | Completado |
| ✅ **Bloque I** — Fix probabilidades (noise removal) + confidence del winner real | Completado |
| ✅ **Bloque J** — Top scorer + ejecutar.bat menú interactivo | Completado |
| ✅ **Bloque K** — Ensemble 100 seeds + upset correction + factor odds | Completado |

## Configuración LSP

- LSP habilitado vía `opencode.jsonc` (`"lsp": true`)
- Servidor: `python-lsp-server` (pylsp) vía pip
- Requiere reiniciar opencode para que tome efecto

## Ejecución

```bash
cd prode_mundial
python main.py                # ensemble 100 seeds (default)
python main.py --seed 123     # seed personalizada
python main.py --no-ensemble  # seed única sin ensemble
```

## Resultado (ensemble 100 seeds)

- **Campeón**: Argentina 🇦🇷 (1-0 vs France en final)
- **Subcampeón**: France 🇫🇷
- **3er puesto**: Determinado por bracket de la seed ensemble
- **Distribución**: Argentina 91%, France 8%, Spain 1%

## Próximos Pasos

✅ **Proyecto completo** — Los 135 partidos del Mundial 2026 han sido analizados con 15 factores + Poisson + ensemble de 100 seeds. Resultados exportados a CSV/JSON en `output/`.
