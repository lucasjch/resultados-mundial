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
├── scraper.py           # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py              # Datos de equipos, sedes, fixture, bases operativas
├── predictor.py         # Motor de 9 factores ponderados + simulación Poisson
├── stats_scraper.py     # Scraper de estadísticas individuales (Transfermarkt API)
├── bracket.py           # Bracket oficial 2026 (R32, R16, QF, SF, 3°, Final)
├── output.py            # Exportación CSV/JSON
├── main.py              # Orquestador principal
├── wikiscraper.py       # Scraper individual de Wikipedia vía API
└── output/
    ├── players.json              # 1245 jugadores (enriquecido vía wikiscraper + Transfermarkt)
    ├── wiki_cache.json           # Caché de Wikipedia scraping
    ├── tm_stats_cache.json       # Caché de Transfermarkt stats
    ├── fase_grupos.csv/json      # Partidos de grupos
    ├── tabla_posiciones.csv      # Posiciones finales
    ├── eliminatorias.csv         # Llaves KO
    └── prode_completo.csv        # Prode completo (135 partidos)
```

## Plan de Fases

| # | Fase | Estado |
|---|------|--------|
| 1 | Ejecutar wikiscraper.py (1112/1245 jugadores) | ✅ Completado |
| 2 | Decidir fuente de asistencias | ✅ Completado |
| 3 | Integrar stats individuales como factores en predictor.py | ✅ Completado |
| 4 | Arreglar modelo de predicción (pesos, redundancias, fórmula) | ✅ Completado |
| 5 | Revisar predicciones Grupo A con factores mejorados | ⬜ Pendiente |
| 6 | Ejecutar simulación completa (main.py) | ✅ Completado |
| — | **Bloque A**: Fix fixture/venue bugs | ✅ Completado |
| — | **Bloque B**: Market Value Parser + Estimaciones | ✅ Completado |
| — | **Bloque C**: Team Data Calibrations + TM_TEAM_OVERRIDES | ✅ Completado |
| — | **Bloque D**: Actualizar temperaturas de sedes con pronóstico 2026 | ✅ Completado |
| — | **Bloque E**: Ajustar modelo (form/goals fuera de team_strength, player_stats 15%, is_neutral) | ✅ Completado |
| — | **Bloque F**: Re-ejecutar stats_scraper + main.py | ✅ Completado (migración cache 2025→2026) |
| — | **Bloque G**: 4 nuevos factores (rest_days, squad_depth, travel_fatigue, jet_lag) | ✅ Completado |

## Decisiones Tomadas

1. **Wikiscraper**: Se agregó checkpoint incremental cada 50 jugadores para evitar perder progreso en timeouts.
2. **UTF-8 fix**: En Windows requiere `$env:PYTHONIOENCODING='utf-8'` antes de ejecutar scripts Python con caracteres UTF-8.
3. **LSP**: `python-lsp-server` (pylsp) instalado globalmente. `opencode.jsonc` con `"lsp": true` en la raíz.
4. **Repositorio**: `https://github.com/lucasjch/resultados-mundial.git`, branch `master`.
5. **Fuente de asistencias → Transfermarkt API**: La API `tmapi-alpha.transfermarkt.technology` devuelve stats detalladas por partido (goles, asistencias, minutos) sin rate limit. Reemplaza FBref (bloqueado por Cloudflare).
6. **Transfermarkt endpoints**: `/quickselect/teams/FIWC` → 48 equipos, `/quickselect/players/{teamId}` → jugadores, `/player/{playerId}/performance-game` → stats por temporada.

## Correcciones Aplicadas en predictor.py (Fase 4 + Bloque E)

### Problemas solucionados (Fase 4):
1. **Pesos sumaban 110%** → Redistribuidos a 100%, eliminados `fanbase` y `randomness` de los pesos.
2. **Redundancia (multicolinealidad)** → `team_strength` ya NO incluye `market_value`. `fanbase` eliminado y absorbido por `home_advantage`.
3. **Fórmula de goles esperados** → Ahora cruza ataque vs defensa: `base_A = (goals_scored_avg_A + goals_conceded_avg_B) / 2`.
4. **Randomness aditivo** → Ya no es un peso; es `random.gauss(0, 0.7) * 10` sumado a `total_diff`.
5. **Nuevo factor**: `player_stats` (10%) que agrega goles+asistencias promedio por plantilla desde Transfermarkt.

### Cambios Bloque E:
1. **`calculate_team_strength`** — eliminados `form_score` (redundante con `morale`) y `goals_score` (redundante con la fórmula base). Ahora solo usa rank + tier.
2. **Pesos rebalanceados** — `player_stats` subió de 10% → 15%, `team_strength` bajó de 28% → 25%, `home_advantage` bajó de 12% → 10%, `foreign_pct` subió de 5% → 7%. Suma = 100%.
3. **`is_neutral`** — Implementado en `calculate_home_advantage()`. Cuando `is_neutral=True` (KO stages), los bonos de México/USA/Canadá fuera de casa se reducen ~50%.

### Pesos actuales (suma = 100%):

| Factor | Peso | Nota |
|--------|------|------|
| team_strength | 19% | Solo rank + tier (sin form/goals) |
| market_value | 12% | Factor independiente |
| player_stats | 12% | Goals + 0.5×Assists promedio por jugador (temporada 2025/26) |
| home_advantage | 8% | Incluye fanbase/diaspora; is_neutral reduce bonos |
| climate | 6% | |
| travel | 3% | |
| history | 4% | |
| morale | 4% | |
| age_penalty | 3% | |
| foreign_pct | 5% | |
| rest_days | 8% | Penalidad si <4 días entre partidos |
| squad_depth | 8% | Ratio de jugadores de impacto en plantilla |
| travel_fatigue | 5% | Km totales acumulados viajando |
| jet_lag | 3% | Diferencia horaria sede vs país de origen |
| randomness | — | Término aditivo `gauss(0,0.7)×10` |

### Fórmula de goles esperados:
```
total_diff = Σ(factor_i × peso_i)   # sin randomness
random_factor = random.gauss(0, 0.7) * 10
total_diff += random_factor
total_diff_scaled = total_diff / 100

base_a = (goals_scored_avg_a + goals_conceded_avg_b) / 2
base_b = (goals_scored_avg_b + goals_conceded_avg_a) / 2
λ_a = base_a * (1 + total_diff_scaled)
λ_b = base_b * (1 - total_diff_scaled)
```

## Seed

`seed = 42` en `main.py`. Resultado actual: Spain campeón, Germany subcampeón, England 3°.

## Bloque A: Fix fixture/venue bugs (Completado)

### Cambios aplicados:

1. **Group L fixtures** (data.py:1106-1107):
   - "Panama vs England" → "England vs Ghana"
   - "Croatia vs Ghana" (duplicado) → "Croatia vs Panama"
   - Resultado: 6 partidos únicos, cada equipo juega 3.

2. **Conflictos horarios resueltos** (data.py):
   - Dallas 18:00 2026-06-20: Ecuador vs Germany movido a Houston 20:00
   - Seattle 18:00 2026-06-25: Netherlands vs Sweden movido a Vancouver 21:00
   - Los Angeles 18:00 2026-06-26: Norway vs Iraq movido a San Francisco 20:00

3. **R32 bracket venues** (bracket.py:8 cambios):
   `Dallas→Toronto, Miami→Los Angeles, Seattle→San Francisco, Kansas City→Seattle, Philadelphia→Atlanta, Toronto→Miami, Atlanta→Dallas, Atlanta→Kansas City`

4. **R16 pairings & venues** (bracket.py):
   - Pairings actualizados al bracket oficial FIFA 2026
   - Venues: `[Boston, LA, Dallas, Seattle, Houston, Mexico City, Toronto, Vancouver]` → `[Philadelphia, Houston, New York, Mexico City, Dallas, Seattle, Atlanta, Vancouver]`

## Bloque B: Market Value Parser + Estimaciones (Completado)

### Cambios aplicados:

1. **Fix parse_market_value()** (scraper.py:96):
   - Agregado `'mio' in val_lower` para manejar el sufijo alemán "Mio" ("20 Mio. €")
   - Se unificó con el bloque `'mill'` ya que ambos representan millones

2. **Estimaciones de market value** (data.py:1149-1190):
   - Agregado `_MARKET_VALUE_ESTIMATES` con valores estimados para los 48 equipos (millones €)
   - Basado en tier + ajustes por equipo: Tier 1 (~1000M) → Tier 8 (~5M)
   - Modificado `_enrich_teams()` para usar estimaciones cuando no hay player-level market values
   - El factor `market_value` (15%) ahora tiene efecto real en predicciones

### Valores estimados (top/bottom):
| Rango | Equipos | Valor |
|-------|---------|-------|
| Top | France 1100, Argentina 1000, England 950, Spain 900 | ~1000M |
| Mid | USA 350, Uruguay 300, Croatia 300 | ~300M |
| Low | Haiti 10, Cape Verde 8, Curacao 5 | ~8M |

## Bloque C: Team Data Calibrations + TM_TEAM_OVERRIDES (Completado)

### Cambios aplicados:

1. **TM_TEAM_OVERRIDES** (stats_scraper.py):
   - Agregados: `Ivory Coast→Côte d'Ivoire`, `Czechia→Czech Republic`, `Cape Verde→Cabo Verde`, `South Korea→Korea Republic`
   - Total: 9 overrides → 49 team names mapeables

2. **Germany form_streak** (data.py:302):
   - `1.0` (10 victorias consecutivas irreales) → `0.70` con form_10 corregido

3. **Tiers recalibrados** (data.py):
   - Croatia: 4→3, Uruguay: 4→3, USA: 4→3, Japan: 4→3
   - Norway: 3→4, South Korea: 5→4, Sweden: 5→4, Austria: 5→4

4. **FANBASE** (data.py:1129-1147):
   - Eliminados equipos que no clasificaron (Italy, Poland, Denmark, Serbia, Nigeria, Cameroon)
   - Croatia subió de 4→5 por éxito reciente en Mundiales

## Bloque D: Actualizar temperaturas de sedes con pronóstico 2026 (Completado)

### Verificación:
- Se compararon los 16 avg_temp actuales con datos pronosticados para junio-julio 2026 de worldcuptourism.com y prepyourtrip.com
- Todos los valores coinciden exactamente con los datos de worldcuptourism.com
- No se requirieron cambios

## Bloque E: Ajustar modelo (Completado)

### Cambios aplicados en predictor.py:

1. **`calculate_team_strength`** — eliminados `form_score` y `goals_score` (redundantes con `morale` y la fórmula base de goles esperados). Ahora solo usa `rank_score` + `tier_score`.
2. **Pesos rebalanceados** — `player_stats` subió de 10% a 15%, `team_strength` bajó de 28% a 25%, `home_advantage` bajó de 12% a 10%, `foreign_pct` subió de 5% a 7%. Suma = 100%.
3. **`is_neutral`** — parámetro agregado a `calculate_home_advantage()`. Cuando es True (KO stages), los bonos de México/USA/Canadá fuera de casa se reducen ~50% (Mexico 10→5, USA 8→4, Canada 5→2).

## Bloque F: Re-ejecutar stats_scraper + main.py (Completado)

### Cambios aplicados:
1. **stats_scraper.py** — campos renombrados de `_2025` a `_2026` para reflejar que la temporada 2025/26 termina en 2026
2. **Migración de caché** — `players.json` (1245 jugadores) y `tm_stats_cache.json` migrados sin re-scrapeo

## Bloque G: 4 nuevos factores (rest_days, squad_depth, travel_fatigue, jet_lag)

### data.py
1. **VENUE_TIMEZONES**: UTC offset para las 16 sedes (Mexico City -6, Toronto -5, Vancouver -8, etc.)
2. **HOME_TIMEZONES**: UTC offset para los 48 equipos según su país de origen
3. **SQUAD_DEPTH**: Ratio de jugadores `impact` sobre el total de `key_players`, escalado 0-10

### predictor.py — 4 nuevos factores
1. **`calculate_rest_days(team_a, team_b, rest_a, rest_b)`**: Penaliza equipos con <4 días de descanso (3 pts por día faltante). El formato 2026 (48 equipos) comprime el fixture.
2. **`calculate_travel_fatigue(team_a, team_b, travel_km_a, travel_km_b)`**: Penaliza equipos con mucho kilometraje acumulado viajando entre sedes (3 países sede = hasta 30,000 km posibles).
3. **`calculate_squad_depth_factor(team_a, team_b)`**: Ventaja para equipos con muchos jugadores de impacto en el banquillo (aprovechan las 5 sustituciones).
4. **`calculate_jet_lag(team_a, team_b, venue_name)`**: Penaliza diferencia horaria sede vs país de origen (0.7 pts por hora de diferencia, máx 5 pts).

### bracket.py — Team history tracking
1. **`compute_team_history(group_predictions)`**: Calcula `last_date`, `last_venue` y `total_travel` por equipo tras fase de grupos.
2. **`_extend_matches(base, round_date)`**: Convierte matches simples a 7-tuplas con datos de descanso y fatiga.
3. **`_update_history(results, round_date)`**: Propaga el historial entre rondas KO (R32→R16→QF→SF→Final), acumulando kilómetros y actualizando fechas.

## Comandos Útiles

```powershell
# Ejecutar wikiscraper
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/wikiscraper.py

# Ejecutar scraper de estadísticas (Transfermarkt)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py

# Forzar re-scrapeo de estadísticas (ignorar caché)
$env:PYTHONIOENCODING='utf-8'; python prode_mundial/stats_scraper.py --force

# Ejecutar simulación completa
python prode_mundial/main.py

# Git push
git add -A; git commit -m "mensaje"; git push origin master
```
