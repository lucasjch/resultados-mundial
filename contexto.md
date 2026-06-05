# Prode Mundial 2026 — Documentación del Proyecto

## Objetivo
Script en Python que analiza los 135 partidos del Mundial 2026 y predice resultados para completar un prode. Exporta a CSV y JSON.

## Estructura del Proyecto

```
prode_mundial/
├── scraper.py        # Scraper de plantillas (Promiedos + Transfermarkt)
├── data.py           # Datos de equipos, sedes, fixture, bases operativas
├── predictor.py      # Motor de 10 factores ponderados + simulación Poisson
├── bracket.py        # Bracket oficial 2026 (R32, R16, QF, SF, 3°, Final)
├── output.py         # Exportación CSV/JSON
├── main.py           # Orquestador principal
└── output/           # Resultados generados
    ├── players.json          # 1245 jugadores scrapeados
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

### 2. Datos (`data.py`)
- `TEAMS`: 48 equipos con rank, tier, confederación, coach, capitán, temperatura/altitud local, racha (`form_streak`), historial mundialista, jugadores clave, goles promedio, diáspora en USA
- `VENUES`: 16 sedes con país, estadio, capacidad, techo, temperatura, altitud
- `GROUPS`: 12 grupos (A-L) de 4 equipos
- `FIXTURES`: 72 partidos de grupos con fecha, hora, sede
- `CITY_COORDS`: coordenadas de 41 ciudades (sedes + bases operativas)
- `BASE_CAMPS`: base de concentración real de cada selección
- `_FOREIGN_PCT_ESTIMATES`: % de jugadores que juegan en el extranjero por confederación
- `_FANBASE`: mapa de popularidad global (0-8)
- `_enrich_teams()`: integra `players.json` en cada equipo con 6 campos extra

### 3. Predicción (`predictor.py`)
10 factores ponderados → `total_diff` → goles esperados → Poisson (1000 sims):

| Factor | Peso | Descripción |
|--------|------|-------------|
| `team_strength` | 30% | Ranking, valor mercado, tier, racha, goles promedio |
| `market_value` | 15% | Diferencia de valor de plantilla (escala log, cap 500M) |
| `home_advantage` | 12% | Localía CONCACAF, México/USA/Canadá, diáspora, COI |
| `climate` | 10% | Diferencia térmica, altitud, techo cerrado |
| `travel` | 8% | Distancia base → sede (haversine) |
| `history` | 6% | Mejor actuación histórica en Mundiales |
| `morale` | 6% | `form_streak` del equipo |
| `foreign_pct` | 4% | % de jugadores en ligas extranjeras |
| `age_penalty` | 4% | Penalización por desviación de edad óptima (27) |
| `fanbase` | 5% | Popularidad global |
| `randomness` | 10% | Ruido gaussiano `N(0, 0.7)` |

Fórmula:
```
total_diff = Σ(factor_i × peso_i) + random
expected_goals_a = goals_scored_avg_a + (total_diff / 30) × 1.2
expected_goals_b = goals_conceded_avg_b - (total_diff / 30) × 0.8
```
Simulación Poisson con 1000 iteraciones. Score = moda de goles.

### 4. Bracket (`bracket.py`)
- **Fase de grupos**: 72 partidos, tabla de posiciones con puntos y GD
- **Mejores terceros**: top 8 de 12 terceros clasifican
- **R32**: 16 llaves fijas oficiales (1E vs 3°ABCDF, 1I vs 3°CDFGH, 2A vs 2B, etc.)
- **R16**: emparejamientos fijos (M01-M02, M03-M04, ...)
- **QF, SF, 3°, Final**: bracket estándar
- Terceros puestos asignados sin duplicados

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

## Ejecución

```bash
cd prode_mundial
python main.py
```

Para cambiar la semilla aleatoria, editar `seed = 42` en `main.py`.

## Resultado (seed 42)
- **Campeón**: Germany
- **Subcampeón**: Brazil
- **3er puesto**: Portugal
