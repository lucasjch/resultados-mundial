# -*- coding: utf-8 -*-
"""
Validacion historica: predice 448 partidos de 1998-2022 y mide precision.

Estrategia:
1. Carga datos historicos embebidos (resultados, rankings, venues).
2. Construye dicts TEAMS/VENUES temporales con 9 factores activos.
3. Sobrescribe data.TEAMS/data.VENUES y ejecuta predict_match().
4. Restaura datos originales y reporta metricas.

9 factores activos (team_strength, home_advantage, climate, history,
morale, travel, foreign_pct, rest_days, travel_fatigue).
9 factores inactivos con peso 0 (player_stats, market_value, experience,
trophy_pedigree, height_advantage, club_chemistry, odds, squad_depth, stakes).
"""

import sys
import os
import copy
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from predictor import predict_match, WEIGHTS
import data as data_module

FACTORS_ZERO = frozenset({
    "player_stats", "market_value", "experience", "trophy_pedigree",
    "height_advantage", "club_chemistry", "odds", "squad_depth", "stakes",
})

_TOURNAMENT_VENUES = {}

_VENUE_STUBS = {
    "France 1998": {"country": "France", "avg_temp": 20, "altitude": 100, "roof": False},
    "South Korea 2002": {"country": "South Korea", "avg_temp": 25, "altitude": 50, "roof": False},
    "Japan 2002": {"country": "Japan", "avg_temp": 26, "altitude": 50, "roof": False},
    "Germany 2006": {"country": "Germany", "avg_temp": 20, "altitude": 100, "roof": False},
    "South Africa 2010": {"country": "South Africa", "avg_temp": 18, "altitude": 1700, "roof": False},
    "Brazil 2014": {"country": "Brazil", "avg_temp": 28, "altitude": 200, "roof": False},
    "Russia 2018": {"country": "Russia", "avg_temp": 22, "altitude": 150, "roof": False},
    "Qatar 2022": {"country": "Qatar", "avg_temp": 36, "altitude": 10, "roof": True},
    "Neutral": {"country": "France", "avg_temp": 20, "altitude": 100, "roof": False},
}

for _yr, _label in [("1998", "France 1998"), ("2002", "South Korea 2002"),
                    ("2006", "Germany 2006"), ("2010", "South Africa 2010"),
                    ("2014", "Brazil 2014"), ("2018", "Russia 2018"),
                    ("2022", "Qatar 2022")]:
    _TOURNAMENT_VENUES[_yr] = [_label]


_HISTORICAL_MATCHES = {}

def _populate_matches():
    _HISTORICAL_MATCHES["1998"] = [
        ("Group A", "Brazil", "Scotland", 2, 1), ("Group A", "Morocco", "Norway", 2, 2),
        ("Group A", "Scotland", "Norway", 1, 1), ("Group A", "Brazil", "Morocco", 3, 0),
        ("Group A", "Brazil", "Norway", 1, 2), ("Group A", "Scotland", "Morocco", 0, 3),
        ("Group B", "Italy", "Chile", 2, 2), ("Group B", "Cameroon", "Austria", 1, 1),
        ("Group B", "Chile", "Austria", 1, 1), ("Group B", "Italy", "Cameroon", 3, 0),
        ("Group B", "Italy", "Austria", 2, 1), ("Group B", "Chile", "Cameroon", 1, 1),
        ("Group C", "Saudi Arabia", "Denmark", 0, 1), ("Group C", "France", "South Africa", 3, 0),
        ("Group C", "South Africa", "Denmark", 1, 1), ("Group C", "France", "Saudi Arabia", 4, 0),
        ("Group C", "France", "Denmark", 2, 1), ("Group C", "South Africa", "Saudi Arabia", 2, 2),
        ("Group D", "Paraguay", "Bulgaria", 0, 0), ("Group D", "Spain", "Nigeria", 2, 3),
        ("Group D", "Nigeria", "Bulgaria", 1, 0), ("Group D", "Spain", "Paraguay", 0, 0),
        ("Group D", "Spain", "Bulgaria", 6, 1), ("Group D", "Nigeria", "Paraguay", 1, 3),
        ("Group E", "Netherlands", "Belgium", 0, 0), ("Group E", "South Korea", "Mexico", 1, 3),
        ("Group E", "Mexico", "Belgium", 1, 1), ("Group E", "Netherlands", "South Korea", 5, 0),
        ("Group E", "Netherlands", "Mexico", 2, 2), ("Group E", "Belgium", "South Korea", 1, 1),
        ("Group F", "Germany", "USA", 2, 0), ("Group F", "Yugoslavia", "Iran", 1, 0),
        ("Group F", "Germany", "Yugoslavia", 2, 2), ("Group F", "USA", "Iran", 1, 2),
        ("Group F", "USA", "Yugoslavia", 0, 1), ("Group F", "Germany", "Iran", 2, 0),
        ("Group G", "Romania", "Colombia", 1, 0), ("Group G", "England", "Tunisia", 2, 0),
        ("Group G", "Romania", "England", 2, 1), ("Group G", "Colombia", "Tunisia", 1, 0),
        ("Group G", "Colombia", "England", 0, 2), ("Group G", "Romania", "Tunisia", 1, 1),
        ("Group H", "Argentina", "Japan", 1, 0), ("Group H", "Jamaica", "Croatia", 1, 3),
        ("Group H", "Japan", "Croatia", 0, 1), ("Group H", "Argentina", "Jamaica", 5, 0),
        ("Group H", "Argentina", "Croatia", 1, 0), ("Group H", "Japan", "Jamaica", 1, 2),
        ("R16", "Italy", "Norway", 1, 0), ("R16", "Brazil", "Chile", 4, 1),
        ("R16", "France", "Paraguay", 0, 0), ("R16", "Nigeria", "Denmark", 1, 4),
        ("R16", "Netherlands", "Yugoslavia", 2, 1), ("R16", "Argentina", "England", 2, 2),
        ("R16", "Germany", "Mexico", 2, 1), ("R16", "Romania", "Croatia", 0, 1),
        ("QF", "Italy", "France", 0, 0), ("QF", "Brazil", "Denmark", 3, 2),
        ("QF", "Netherlands", "Argentina", 2, 1), ("QF", "Germany", "Croatia", 0, 3),
        ("SF", "Brazil", "Netherlands", 1, 1), ("SF", "France", "Croatia", 2, 1),
        ("3rd", "Netherlands", "Croatia", 1, 2), ("Final", "Brazil", "France", 0, 3),
    ]
    _HISTORICAL_MATCHES["2002"] = [
        ("Group A", "Denmark", "Uruguay", 2, 1), ("Group A", "Senegal", "France", 1, 0),
        ("Group A", "Denmark", "Senegal", 1, 1), ("Group A", "France", "Uruguay", 0, 0),
        ("Group A", "Denmark", "France", 2, 0), ("Group A", "Senegal", "Uruguay", 3, 3),
        ("Group B", "Paraguay", "South Africa", 2, 2), ("Group B", "Spain", "Slovenia", 3, 1),
        ("Group B", "Spain", "Paraguay", 3, 1), ("Group B", "Slovenia", "South Africa", 0, 1),
        ("Group B", "Spain", "South Africa", 3, 2), ("Group B", "Slovenia", "Paraguay", 1, 3),
        ("Group C", "Brazil", "Turkey", 2, 1), ("Group C", "China", "Costa Rica", 0, 2),
        ("Group C", "Brazil", "China", 4, 0), ("Group C", "Costa Rica", "Turkey", 1, 1),
        ("Group C", "Brazil", "Costa Rica", 5, 2), ("Group C", "Turkey", "China", 3, 0),
        ("Group D", "South Korea", "Poland", 2, 0), ("Group D", "USA", "Portugal", 3, 2),
        ("Group D", "South Korea", "USA", 1, 1), ("Group D", "Portugal", "Poland", 4, 0),
        ("Group D", "South Korea", "Portugal", 1, 0), ("Group D", "Poland", "USA", 3, 1),
        ("Group E", "Ireland", "Cameroon", 1, 1), ("Group E", "Germany", "Saudi Arabia", 8, 0),
        ("Group E", "Germany", "Ireland", 1, 1), ("Group E", "Cameroon", "Saudi Arabia", 1, 0),
        ("Group E", "Germany", "Cameroon", 2, 0), ("Group E", "Ireland", "Saudi Arabia", 3, 0),
        ("Group F", "Argentina", "Nigeria", 1, 0), ("Group F", "England", "Sweden", 1, 1),
        ("Group F", "Sweden", "Nigeria", 2, 1), ("Group F", "Argentina", "England", 0, 1),
        ("Group F", "Argentina", "Sweden", 1, 1), ("Group F", "England", "Nigeria", 0, 0),
        ("Group G", "Croatia", "Mexico", 0, 1), ("Group G", "Italy", "Ecuador", 2, 0),
        ("Group G", "Italy", "Croatia", 1, 2), ("Group G", "Mexico", "Ecuador", 2, 1),
        ("Group G", "Mexico", "Italy", 1, 1), ("Group G", "Ecuador", "Croatia", 1, 0),
        ("Group H", "Japan", "Belgium", 2, 2), ("Group H", "Russia", "Tunisia", 2, 0),
        ("Group H", "Japan", "Russia", 1, 0), ("Group H", "Tunisia", "Belgium", 1, 1),
        ("Group H", "Japan", "Tunisia", 2, 0), ("Group H", "Belgium", "Russia", 3, 2),
        ("R16", "Germany", "Paraguay", 1, 0), ("R16", "Denmark", "England", 0, 3),
        ("R16", "Sweden", "Senegal", 1, 2), ("R16", "Spain", "Ireland", 1, 1),
        ("R16", "Mexico", "USA", 0, 2), ("R16", "Brazil", "Belgium", 2, 0),
        ("R16", "Japan", "Turkey", 0, 1), ("R16", "South Korea", "Italy", 2, 1),
        ("QF", "England", "Brazil", 1, 2), ("QF", "Germany", "USA", 1, 0),
        ("QF", "South Korea", "Spain", 0, 0), ("QF", "Senegal", "Turkey", 0, 1),
        ("SF", "Germany", "South Korea", 1, 0), ("SF", "Brazil", "Turkey", 1, 0),
        ("3rd", "South Korea", "Turkey", 2, 3), ("Final", "Germany", "Brazil", 0, 2),
    ]
    _HISTORICAL_MATCHES["2006"] = [
        ("Group A", "Germany", "Costa Rica", 4, 2), ("Group A", "Poland", "Ecuador", 0, 2),
        ("Group A", "Germany", "Poland", 1, 0), ("Group A", "Ecuador", "Costa Rica", 3, 0),
        ("Group A", "Ecuador", "Germany", 0, 3), ("Group A", "Costa Rica", "Poland", 1, 2),
        ("Group B", "England", "Paraguay", 1, 0), ("Group B", "Trinidad", "Sweden", 0, 0),
        ("Group B", "England", "Trinidad", 2, 0), ("Group B", "Sweden", "Paraguay", 1, 0),
        ("Group B", "England", "Sweden", 2, 2), ("Group B", "Paraguay", "Trinidad", 2, 0),
        ("Group C", "Argentina", "Ivory Coast", 2, 1), ("Group C", "Serbia", "Netherlands", 0, 1),
        ("Group C", "Argentina", "Serbia", 6, 0), ("Group C", "Netherlands", "Ivory Coast", 2, 1),
        ("Group C", "Argentina", "Netherlands", 0, 0), ("Group C", "Ivory Coast", "Serbia", 3, 2),
        ("Group D", "Mexico", "Iran", 3, 1), ("Group D", "Angola", "Portugal", 0, 1),
        ("Group D", "Mexico", "Angola", 0, 0), ("Group D", "Portugal", "Iran", 2, 0),
        ("Group D", "Portugal", "Mexico", 2, 1), ("Group D", "Iran", "Angola", 1, 1),
        ("Group E", "USA", "Czechia", 0, 3), ("Group E", "Italy", "Ghana", 2, 0),
        ("Group E", "Czechia", "Ghana", 0, 2), ("Group E", "Italy", "USA", 1, 1),
        ("Group E", "Czechia", "Italy", 0, 2), ("Group E", "USA", "Ghana", 1, 2),
        ("Group F", "Brazil", "Croatia", 1, 0), ("Group F", "Australia", "Japan", 3, 1),
        ("Group F", "Brazil", "Australia", 2, 0), ("Group F", "Japan", "Croatia", 0, 0),
        ("Group F", "Brazil", "Japan", 4, 1), ("Group F", "Croatia", "Australia", 2, 2),
        ("Group G", "France", "Switzerland", 0, 0), ("Group G", "South Korea", "Togo", 2, 1),
        ("Group G", "France", "South Korea", 1, 1), ("Group G", "Switzerland", "Togo", 2, 0),
        ("Group G", "Switzerland", "South Korea", 2, 0), ("Group G", "France", "Togo", 2, 0),
        ("Group H", "Spain", "Ukraine", 4, 0), ("Group H", "Tunisia", "Saudi Arabia", 2, 2),
        ("Group H", "Spain", "Tunisia", 3, 1), ("Group H", "Ukraine", "Saudi Arabia", 4, 0),
        ("Group H", "Spain", "Saudi Arabia", 1, 0), ("Group H", "Ukraine", "Tunisia", 1, 0),
        ("R16", "Germany", "Sweden", 2, 0), ("R16", "Argentina", "Mexico", 2, 1),
        ("R16", "England", "Ecuador", 1, 0), ("R16", "Portugal", "Netherlands", 1, 0),
        ("R16", "Italy", "Australia", 1, 0), ("R16", "Switzerland", "Ukraine", 0, 0),
        ("R16", "Brazil", "Ghana", 3, 0), ("R16", "Spain", "France", 1, 3),
        ("QF", "Germany", "Argentina", 1, 1), ("QF", "Italy", "Ukraine", 3, 0),
        ("QF", "England", "Portugal", 0, 0), ("QF", "Brazil", "France", 0, 1),
        ("SF", "Germany", "Italy", 0, 2), ("SF", "Portugal", "France", 0, 1),
        ("3rd", "Germany", "Portugal", 3, 1), ("Final", "Italy", "France", 1, 1),
    ]
    _HISTORICAL_MATCHES["2010"] = [
        ("Group A", "Uruguay", "France", 0, 0), ("Group A", "South Africa", "Mexico", 1, 1),
        ("Group A", "South Africa", "Uruguay", 0, 3), ("Group A", "France", "Mexico", 0, 2),
        ("Group A", "Mexico", "Uruguay", 0, 1), ("Group A", "France", "South Africa", 1, 2),
        ("Group B", "Argentina", "Nigeria", 1, 0), ("Group B", "South Korea", "Greece", 2, 0),
        ("Group B", "Argentina", "South Korea", 4, 1), ("Group B", "Greece", "Nigeria", 2, 1),
        ("Group B", "Argentina", "Greece", 2, 0), ("Group B", "Nigeria", "South Korea", 2, 2),
        ("Group C", "England", "USA", 1, 1), ("Group C", "Algeria", "Slovenia", 0, 1),
        ("Group C", "England", "Algeria", 0, 0), ("Group C", "Slovenia", "USA", 2, 2),
        ("Group C", "England", "Slovenia", 1, 0), ("Group C", "USA", "Algeria", 1, 0),
        ("Group D", "Germany", "Australia", 4, 0), ("Group D", "Serbia", "Ghana", 0, 1),
        ("Group D", "Germany", "Serbia", 0, 1), ("Group D", "Ghana", "Australia", 1, 1),
        ("Group D", "Germany", "Ghana", 1, 0), ("Group D", "Australia", "Serbia", 2, 1),
        ("Group E", "Netherlands", "Denmark", 2, 0), ("Group E", "Japan", "Cameroon", 1, 0),
        ("Group E", "Netherlands", "Japan", 1, 0), ("Group E", "Cameroon", "Denmark", 1, 2),
        ("Group E", "Netherlands", "Cameroon", 2, 1), ("Group E", "Denmark", "Japan", 1, 3),
        ("Group F", "Italy", "Paraguay", 1, 1), ("Group F", "New Zealand", "Slovakia", 1, 1),
        ("Group F", "Italy", "New Zealand", 1, 1), ("Group F", "Slovakia", "Paraguay", 0, 2),
        ("Group F", "Italy", "Slovakia", 2, 3), ("Group F", "Paraguay", "New Zealand", 0, 0),
        ("Group G", "Brazil", "North Korea", 2, 1), ("Group G", "Ivory Coast", "Portugal", 0, 0),
        ("Group G", "Brazil", "Ivory Coast", 3, 1), ("Group G", "Portugal", "North Korea", 7, 0),
        ("Group G", "Brazil", "Portugal", 0, 0), ("Group G", "Ivory Coast", "North Korea", 3, 0),
        ("Group H", "Chile", "Honduras", 1, 0), ("Group H", "Spain", "Switzerland", 0, 1),
        ("Group H", "Chile", "Switzerland", 1, 0), ("Group H", "Spain", "Honduras", 2, 0),
        ("Group H", "Chile", "Spain", 1, 2), ("Group H", "Switzerland", "Honduras", 0, 0),
        ("R16", "Uruguay", "South Korea", 2, 1), ("R16", "USA", "Ghana", 1, 2),
        ("R16", "Germany", "England", 4, 1), ("R16", "Argentina", "Mexico", 3, 1),
        ("R16", "Netherlands", "Slovakia", 2, 1), ("R16", "Brazil", "Chile", 3, 0),
        ("R16", "Paraguay", "Japan", 0, 0), ("R16", "Spain", "Portugal", 1, 0),
        ("QF", "Netherlands", "Brazil", 2, 1), ("QF", "Uruguay", "Ghana", 1, 1),
        ("QF", "Germany", "Argentina", 4, 0), ("QF", "Spain", "Paraguay", 1, 0),
        ("SF", "Netherlands", "Uruguay", 3, 2), ("SF", "Spain", "Germany", 1, 0),
        ("3rd", "Uruguay", "Germany", 2, 3), ("Final", "Netherlands", "Spain", 0, 1),
    ]
    _HISTORICAL_MATCHES["2014"] = [
        ("Group A", "Brazil", "Croatia", 3, 1), ("Group A", "Mexico", "Cameroon", 1, 0),
        ("Group A", "Brazil", "Mexico", 0, 0), ("Group A", "Cameroon", "Croatia", 0, 4),
        ("Group A", "Brazil", "Cameroon", 4, 1), ("Group A", "Croatia", "Mexico", 1, 3),
        ("Group B", "Spain", "Netherlands", 1, 5), ("Group B", "Chile", "Australia", 3, 1),
        ("Group B", "Spain", "Chile", 0, 2), ("Group B", "Netherlands", "Australia", 3, 2),
        ("Group B", "Spain", "Australia", 3, 0), ("Group B", "Netherlands", "Chile", 2, 0),
        ("Group C", "Colombia", "Greece", 3, 0), ("Group C", "Ivory Coast", "Japan", 2, 1),
        ("Group C", "Colombia", "Ivory Coast", 2, 1), ("Group C", "Japan", "Greece", 0, 0),
        ("Group C", "Colombia", "Japan", 4, 1), ("Group C", "Greece", "Ivory Coast", 2, 1),
        ("Group D", "Uruguay", "Costa Rica", 1, 3), ("Group D", "England", "Italy", 1, 2),
        ("Group D", "Uruguay", "England", 2, 1), ("Group D", "Italy", "Costa Rica", 0, 1),
        ("Group D", "Italy", "Uruguay", 0, 1), ("Group D", "Costa Rica", "England", 0, 0),
        ("Group E", "Switzerland", "Ecuador", 2, 1), ("Group E", "France", "Honduras", 3, 0),
        ("Group E", "Switzerland", "France", 2, 5), ("Group E", "Honduras", "Ecuador", 1, 2),
        ("Group E", "Honduras", "Switzerland", 0, 3), ("Group E", "Ecuador", "France", 0, 0),
        ("Group F", "Argentina", "Bosnia", 2, 1), ("Group F", "Iran", "Nigeria", 0, 0),
        ("Group F", "Argentina", "Iran", 1, 0), ("Group F", "Nigeria", "Bosnia", 1, 0),
        ("Group F", "Argentina", "Nigeria", 3, 2), ("Group F", "Bosnia", "Iran", 3, 1),
        ("Group G", "Germany", "Portugal", 4, 0), ("Group G", "Ghana", "USA", 1, 2),
        ("Group G", "Germany", "Ghana", 2, 2), ("Group G", "USA", "Portugal", 2, 2),
        ("Group G", "USA", "Germany", 0, 1), ("Group G", "Portugal", "Ghana", 2, 1),
        ("Group H", "Belgium", "Algeria", 2, 1), ("Group H", "Russia", "South Korea", 1, 1),
        ("Group H", "Belgium", "Russia", 1, 0), ("Group H", "South Korea", "Algeria", 2, 4),
        ("Group H", "Belgium", "South Korea", 1, 0), ("Group H", "Algeria", "Russia", 1, 1),
        ("R16", "Brazil", "Chile", 1, 1), ("R16", "Colombia", "Uruguay", 2, 0),
        ("R16", "Netherlands", "Mexico", 2, 1), ("R16", "Costa Rica", "Greece", 1, 1),
        ("R16", "France", "Nigeria", 2, 0), ("R16", "Germany", "Algeria", 2, 1),
        ("R16", "Argentina", "Switzerland", 1, 0), ("R16", "Belgium", "USA", 2, 1),
        ("QF", "France", "Germany", 0, 1), ("QF", "Brazil", "Colombia", 2, 1),
        ("QF", "Argentina", "Belgium", 1, 0), ("QF", "Netherlands", "Costa Rica", 0, 0),
        ("SF", "Brazil", "Germany", 1, 7), ("SF", "Argentina", "Netherlands", 0, 0),
        ("3rd", "Brazil", "Netherlands", 0, 3), ("Final", "Germany", "Argentina", 1, 0),
    ]
    _HISTORICAL_MATCHES["2018"] = [
        ("Group A", "Russia", "Saudi Arabia", 5, 0), ("Group A", "Egypt", "Uruguay", 0, 1),
        ("Group A", "Russia", "Egypt", 3, 1), ("Group A", "Uruguay", "Saudi Arabia", 1, 0),
        ("Group A", "Russia", "Uruguay", 0, 3), ("Group A", "Saudi Arabia", "Egypt", 2, 1),
        ("Group B", "Morocco", "Iran", 0, 1), ("Group B", "Portugal", "Spain", 3, 3),
        ("Group B", "Portugal", "Morocco", 1, 0), ("Group B", "Spain", "Iran", 1, 0),
        ("Group B", "Spain", "Morocco", 2, 2), ("Group B", "Iran", "Portugal", 1, 1),
        ("Group C", "France", "Australia", 2, 1), ("Group C", "Peru", "Denmark", 0, 1),
        ("Group C", "France", "Peru", 1, 0), ("Group C", "Denmark", "Australia", 1, 1),
        ("Group C", "France", "Denmark", 0, 0), ("Group C", "Australia", "Peru", 0, 2),
        ("Group D", "Argentina", "Iceland", 1, 1), ("Group D", "Croatia", "Nigeria", 2, 0),
        ("Group D", "Argentina", "Croatia", 0, 3), ("Group D", "Nigeria", "Iceland", 2, 0),
        ("Group D", "Argentina", "Nigeria", 2, 1), ("Group D", "Iceland", "Croatia", 1, 2),
        ("Group E", "Costa Rica", "Serbia", 0, 1), ("Group E", "Brazil", "Switzerland", 1, 1),
        ("Group E", "Brazil", "Costa Rica", 2, 0), ("Group E", "Serbia", "Switzerland", 1, 2),
        ("Group E", "Brazil", "Serbia", 2, 0), ("Group E", "Switzerland", "Costa Rica", 2, 2),
        ("Group F", "Germany", "Mexico", 0, 1), ("Group F", "Sweden", "South Korea", 1, 0),
        ("Group F", "Germany", "Sweden", 2, 1), ("Group F", "South Korea", "Mexico", 1, 2),
        ("Group F", "South Korea", "Germany", 2, 0), ("Group F", "Mexico", "Sweden", 0, 3),
        ("Group G", "Belgium", "Panama", 3, 0), ("Group G", "Tunisia", "England", 1, 2),
        ("Group G", "Belgium", "Tunisia", 5, 2), ("Group G", "England", "Panama", 6, 1),
        ("Group G", "England", "Belgium", 0, 1), ("Group G", "Panama", "Tunisia", 1, 2),
        ("Group H", "Colombia", "Japan", 1, 2), ("Group H", "Poland", "Senegal", 1, 2),
        ("Group H", "Senegal", "Japan", 2, 2), ("Group H", "Colombia", "Poland", 3, 0),
        ("Group H", "Japan", "Poland", 0, 1), ("Group H", "Senegal", "Colombia", 0, 1),
        ("R16", "France", "Argentina", 4, 3), ("R16", "Uruguay", "Portugal", 2, 1),
        ("R16", "Spain", "Russia", 1, 1), ("R16", "Croatia", "Denmark", 1, 1),
        ("R16", "Brazil", "Mexico", 2, 0), ("R16", "Belgium", "Japan", 3, 2),
        ("R16", "Sweden", "Switzerland", 1, 0), ("R16", "Colombia", "England", 1, 1),
        ("QF", "France", "Uruguay", 2, 0), ("QF", "Brazil", "Belgium", 1, 2),
        ("QF", "Sweden", "England", 0, 2), ("QF", "Russia", "Croatia", 2, 2),
        ("SF", "France", "Belgium", 1, 0), ("SF", "Croatia", "England", 2, 1),
        ("3rd", "Belgium", "England", 2, 0), ("Final", "France", "Croatia", 4, 2),
    ]
    _HISTORICAL_MATCHES["2022"] = [
        ("Group A", "Qatar", "Ecuador", 0, 2), ("Group A", "Senegal", "Netherlands", 0, 2),
        ("Group A", "Qatar", "Senegal", 1, 3), ("Group A", "Netherlands", "Ecuador", 1, 1),
        ("Group A", "Netherlands", "Qatar", 2, 0), ("Group A", "Ecuador", "Senegal", 1, 2),
        ("Group B", "England", "Iran", 6, 2), ("Group B", "USA", "Wales", 1, 1),
        ("Group B", "USA", "England", 0, 0), ("Group B", "Wales", "Iran", 0, 2),
        ("Group B", "Wales", "England", 0, 3), ("Group B", "Iran", "USA", 0, 1),
        ("Group C", "Argentina", "Saudi Arabia", 1, 2), ("Group C", "Mexico", "Poland", 0, 0),
        ("Group C", "Argentina", "Mexico", 2, 0), ("Group C", "Poland", "Saudi Arabia", 2, 0),
        ("Group C", "Argentina", "Poland", 2, 0), ("Group C", "Saudi Arabia", "Mexico", 1, 2),
        ("Group D", "Denmark", "Tunisia", 0, 0), ("Group D", "France", "Australia", 4, 1),
        ("Group D", "France", "Denmark", 2, 1), ("Group D", "Australia", "Tunisia", 0, 1),
        ("Group D", "Australia", "Denmark", 1, 0), ("Group D", "France", "Tunisia", 0, 1),
        ("Group E", "Germany", "Japan", 1, 2), ("Group E", "Spain", "Costa Rica", 7, 0),
        ("Group E", "Germany", "Spain", 1, 1), ("Group E", "Japan", "Costa Rica", 0, 1),
        ("Group E", "Japan", "Spain", 2, 1), ("Group E", "Costa Rica", "Germany", 2, 4),
        ("Group F", "Morocco", "Croatia", 0, 0), ("Group F", "Belgium", "Canada", 1, 0),
        ("Group F", "Belgium", "Morocco", 0, 2), ("Group F", "Croatia", "Canada", 4, 1),
        ("Group F", "Croatia", "Belgium", 0, 0), ("Group F", "Canada", "Morocco", 1, 2),
        ("Group G", "Switzerland", "Cameroon", 1, 0), ("Group G", "Brazil", "Serbia", 2, 0),
        ("Group G", "Brazil", "Switzerland", 1, 0), ("Group G", "Cameroon", "Serbia", 3, 3),
        ("Group G", "Cameroon", "Brazil", 1, 0), ("Group G", "Serbia", "Switzerland", 2, 3),
        ("Group H", "Uruguay", "South Korea", 0, 0), ("Group H", "Portugal", "Ghana", 3, 2),
        ("Group H", "Uruguay", "Portugal", 0, 2), ("Group H", "Ghana", "South Korea", 2, 3),
        ("Group H", "Ghana", "Uruguay", 0, 2), ("Group H", "South Korea", "Portugal", 2, 1),
        ("R16", "Netherlands", "USA", 3, 1), ("R16", "Argentina", "Australia", 2, 1),
        ("R16", "France", "Poland", 3, 1), ("R16", "England", "Senegal", 3, 0),
        ("R16", "Japan", "Croatia", 1, 1), ("R16", "Brazil", "South Korea", 4, 1),
        ("R16", "Morocco", "Spain", 0, 0), ("R16", "Portugal", "Switzerland", 6, 1),
        ("QF", "Netherlands", "Argentina", 2, 2), ("QF", "France", "England", 2, 1),
        ("QF", "Morocco", "Portugal", 1, 0), ("QF", "Croatia", "Brazil", 1, 1),
        ("SF", "Argentina", "Croatia", 3, 0), ("SF", "France", "Morocco", 2, 0),
        ("3rd", "Croatia", "Morocco", 2, 1), ("Final", "Argentina", "France", 3, 3),
    ]

_populate_matches()


_HISTORICAL_RANKINGS = {}

def _populate_rankings():
    _HISTORICAL_RANKINGS["1998"] = {
        "Brazil": 1, "France": 18, "Argentina": 6, "Germany": 2, "Netherlands": 11,
        "Italy": 14, "England": 5, "Croatia": 19, "Yugoslavia": 8, "Romania": 22,
        "Denmark": 27, "Nigeria": 40, "Mexico": 10, "Norway": 7, "Chile": 9,
        "Spain": 4, "Paraguay": 31, "Belgium": 36, "South Korea": 20, "Japan": 12,
        "Morocco": 13, "USA": 15, "Colombia": 23, "South Africa": 24,
        "Scotland": 21, "Austria": 30, "Cameroon": 33, "Tunisia": 23,
        "Iran": 42, "Jamaica": 39, "Saudi Arabia": 41, "Bulgaria": 35,
    }
    _HISTORICAL_RANKINGS["2002"] = {
        "Brazil": 2, "Germany": 8, "Turkey": 22, "South Korea": 40, "Spain": 7,
        "England": 10, "Senegal": 42, "USA": 13, "Japan": 32, "Denmark": 17,
        "Sweden": 19, "Ireland": 15, "Mexico": 9, "Belgium": 20, "Italy": 6,
        "Paraguay": 18, "South Africa": 35, "Argentina": 3, "Portugal": 5,
        "Croatia": 21, "Cameroon": 16, "France": 1, "Nigeria": 28,
        "Uruguay": 24, "Saudi Arabia": 34, "Slovenia": 25, "China": 53,
        "Costa Rica": 29, "Poland": 38, "Ecuador": 36, "Tunisia": 31, "Russia": 26,
    }
    _HISTORICAL_RANKINGS["2006"] = {
        "Italy": 2, "France": 8, "Germany": 9, "Portugal": 7, "Brazil": 1,
        "Argentina": 5, "England": 6, "Ukraine": 39, "Spain": 4, "Switzerland": 36,
        "Netherlands": 3, "Ecuador": 28, "Ghana": 48, "Sweden": 14, "Mexico": 11,
        "Australia": 42, "Czechia": 10, "Croatia": 23, "Ivory Coast": 32,
        "Paraguay": 33, "Iran": 47, "Togo": 61, "Trinidad": 53,
        "Angola": 63, "Serbia": 44, "Japan": 18, "USA": 15, "South Korea": 29,
        "Costa Rica": 25, "Poland": 22, "Saudi Arabia": 34, "Tunisia": 24,
    }
    _HISTORICAL_RANKINGS["2010"] = {
        "Spain": 1, "Netherlands": 3, "Germany": 2, "Uruguay": 6, "Argentina": 5,
        "Brazil": 4, "Paraguay": 31, "Ghana": 38, "England": 8, "Japan": 50,
        "Portugal": 7, "Slovakia": 34, "USA": 14, "South Korea": 48,
        "Chile": 15, "Mexico": 17, "France": 9, "Italy": 10, "Switzerland": 24,
        "Denmark": 32, "Ivory Coast": 16, "Serbia": 20, "Slovenia": 25,
        "Algeria": 31, "Nigeria": 33, "Honduras": 35, "Greece": 12,
        "Australia": 21, "Cameroon": 19, "New Zealand": 78, "North Korea": 105,
        "South Africa": 90,
    }
    _HISTORICAL_RANKINGS["2014"] = {
        "Germany": 1, "Argentina": 3, "Netherlands": 8, "Brazil": 4, "France": 10,
        "Colombia": 5, "Belgium": 11, "Costa Rica": 15, "Mexico": 18, "Chile": 14,
        "Switzerland": 7, "Uruguay": 6, "Greece": 12, "Croatia": 19, "Nigeria": 37,
        "Algeria": 22, "England": 9, "Portugal": 2, "Spain": 13, "Italy": 17,
        "Bosnia": 20, "Russia": 23, "Ivory Coast": 25, "Japan": 46,
        "Iran": 48, "South Korea": 61, "USA": 15, "Honduras": 34,
        "Cameroon": 50, "Ghana": 38, "Ecuador": 28, "Australia": 55,
    }
    _HISTORICAL_RANKINGS["2018"] = {
        "France": 7, "Croatia": 18, "Belgium": 3, "England": 12, "Uruguay": 21,
        "Brazil": 2, "Sweden": 23, "Russia": 65, "Colombia": 16, "Spain": 10,
        "Denmark": 12, "Switzerland": 6, "Japan": 40, "Mexico": 12,
        "Portugal": 4, "Argentina": 5, "Germany": 1, "Senegal": 24,
        "Iran": 32, "South Korea": 15, "Peru": 13, "Nigeria": 44,
        "Morocco": 41, "Iceland": 24, "Costa Rica": 25, "Serbia": 34,
        "Panama": 55, "Tunisia": 14, "Egypt": 47, "Saudi Arabia": 65,
        "Australia": 37, "Poland": 8,
    }
    _HISTORICAL_RANKINGS["2022"] = {
        "Argentina": 3, "France": 4, "Croatia": 12, "Morocco": 22, "Netherlands": 8,
        "England": 5, "Brazil": 1, "Portugal": 9, "Japan": 24, "Senegal": 18,
        "Australia": 38, "Switzerland": 15, "Spain": 7, "USA": 16, "Poland": 26,
        "South Korea": 28, "Germany": 11, "Ecuador": 44, "Cameroon": 43,
        "Ghana": 61, "Uruguay": 14, "Mexico": 13, "Belgium": 2, "Saudi Arabia": 51,
        "Iran": 20, "Costa Rica": 31, "Denmark": 10, "Tunisia": 30,
        "Wales": 19, "Canada": 41, "Qatar": 50, "Serbia": 29,
    }

_populate_rankings()


_HISTORY_EVENT = {
    "campeon": "campeon", "final": "final", "semifinal": "semifinal",
    "cuartos": "cuartos", "octavos": "octavos", "fase_grupos": "fase_grupos",
    "debut": "debut",
}

def _wc_best_result(year, team):
    year = int(year)
    if year <= 1998:
        if team == "Brazil": return "campeon"
        if team == "Germany": return "campeon"
        if team == "Argentina": return "campeon"
        if team == "England": return "campeon"
        if team == "France": return "campeon"
        if team in ("Netherlands", "Netherlands"): return "final"
        if team in ("Sweden",): return "final"
        if team in ("Croatia",): return "semifinal"
        if team in ("USA",): return "semifinal"
        if team == "Morocco": return "octavos"
    if year <= 2002:
        if team == "Brazil": return "campeon"
        if team == "Germany": return "final"
        if team == "Argentina": return "campeon"
        if team == "England": return "campeon"
        if team == "France": return "campeon"
        if team == "Spain": return "cuartos"
        if team == "Netherlands": return "final"
        if team == "Croatia": return "semifinal"
        if team == "USA": return "cuartos"
        if team == "South Korea": return "semifinal"
        if team == "Turkey": return "semifinal"
        if team == "Senegal": return "cuartos"
    if year <= 2006:
        if team == "Brazil": return "campeon"
        if team == "Germany": return "semifinal"
        if team == "Argentina": return "campeon"
        if team == "France": return "final"
        if team == "Italy": return "campeon"
        if team == "England": return "campeon"
        if team == "Portugal": return "semifinal"
        if team == "Netherlands": return "final"
        if team == "Croatia": return "semifinal"
        if team == "Spain": return "cuartos"
        if team == "Sweden": return "final"
        if team == "USA": return "cuartos"
    if year <= 2010:
        if team == "Brazil": return "campeon"
        if team == "Germany": return "semifinal"
        if team == "Argentina": return "cuartos"
        if team == "Netherlands": return "final"
        if team == "Spain": return "campeon"
        if team == "Italy": return "campeon"
        if team == "France": return "final"
        if team == "England": return "campeon"
        if team == "Uruguay": return "semifinal"
        if team == "Portugal": return "semifinal"
        if team == "Croatia": return "semifinal"
        if team == "USA": return "cuartos"
        if team == "Japan": return "octavos"
        if team == "South Korea": return "semifinal"
        if team == "Ghana": return "cuartos"
        if team == "Paraguay": return "cuartos"
    if year <= 2014:
        if team == "Brazil": return "semifinal"
        if team == "Germany": return "campeon"
        if team == "Argentina": return "final"
        if team == "Netherlands": return "semifinal"
        if team == "Spain": return "campeon"
        if team == "France": return "cuartos"
        if team == "Italy": return "final"
        if team == "England": return "campeon"
        if team == "Uruguay": return "semifinal"
        if team == "Portugal": return "semifinal"
        if team == "Croatia": return "semifinal"
        if team == "Colombia": return "cuartos"
        if team == "Belgium": return "cuartos"
        if team == "USA": return "octavos"
        if team == "Japan": return "octavos"
        if team == "South Korea": return "semifinal"
        if team == "Ghana": return "cuartos"
        if team == "Switzerland": return "cuartos"
    return "fase_grupos"


_CONF_MAP = {
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL",
    "Chile": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL",
    "Germany": "UEFA", "France": "UEFA", "Spain": "UEFA", "England": "UEFA",
    "Italy": "UEFA", "Portugal": "UEFA", "Netherlands": "UEFA",
    "Croatia": "UEFA", "Belgium": "UEFA", "Switzerland": "UEFA",
    "Sweden": "UEFA", "Denmark": "UEFA", "Norway": "UEFA", "Greece": "UEFA",
    "Czechia": "UEFA", "Austria": "UEFA", "Poland": "UEFA", "Romania": "UEFA",
    "Serbia": "UEFA", "Russia": "UEFA", "Ukraine": "UEFA", "Slovakia": "UEFA",
    "Slovenia": "UEFA", "Bulgaria": "UEFA", "Yugoslavia": "UEFA",
    "Turkey": "UEFA", "Ireland": "UEFA", "Scotland": "UEFA",
    "Iceland": "UEFA", "Croatia": "UEFA", "Bosnia": "UEFA",
    "Mexico": "CONCACAF", "USA": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Honduras": "CONCACAF", "Panama": "CONCACAF",
    "Jamaica": "CONCACAF", "Trinidad": "CONCACAF", "Haiti": "CONCACAF",
    "Japan": "AFC", "South Korea": "AFC", "Australia": "AFC", "Iran": "AFC",
    "Saudi Arabia": "AFC", "China": "AFC", "Qatar": "AFC", "Iraq": "AFC",
    "Jordan": "AFC", "Uzbekistan": "AFC", "North Korea": "AFC",
    "Cameroon": "CAF", "Nigeria": "CAF", "Senegal": "CAF", "Ghana": "CAF",
    "Ivory Coast": "CAF", "Algeria": "CAF", "Tunisia": "CAF", "Egypt": "CAF",
    "South Africa": "CAF", "Morocco": "CAF", "Togo": "CAF", "Angola": "CAF",
    "DR Congo": "CAF", "Cape Verde": "CAF",
    "New Zealand": "OFC",
    "Wales": "UEFA", "Poland": "UEFA",
}

def _rank_to_tier(r):
    if r <= 5: return 1
    if r <= 10: return 2
    if r <= 20: return 3
    if r <= 30: return 4
    if r <= 45: return 5
    if r <= 60: return 6
    if r <= 75: return 7
    return 8


def _build_teams_for_year(year):
    teams_dict = {}
    rankings = _HISTORICAL_RANKINGS.get(year, {})
    for team, rank in rankings.items():
        tier = _rank_to_tier(rank)
        conf = _CONF_MAP.get(team, "UEFA")
        best = _wc_best_result(year, team)
        teams_dict[team] = {
            "rank": rank, "tier": tier, "confederation": conf,
            "home_continent": False,
            "avg_temp_home": 20, "altitude_home": 100, "roof": False,
            "diaspora_in_usa": 500000,
            "form_streak": 0.5,
            "wc_history": best,
            "goals_scored_avg": max(0.5, 2.5 - tier * 0.25),
            "goals_conceded_avg": max(0.3, 0.5 + tier * 0.15),
            "foreign_pct": 0.80,
            "market_value_total": 100,
            "market_value_avg": 5,
            "avg_caps": 20, "avg_trophies": 1,
            "avg_height": 1.80, "club_pairs": 2,
            "players": [], "yellow_rate": 2.0, "red_rate": 0.05,
            "odds_win": 10000,
        }
    return teams_dict


def _build_venues_for_year(year):
    label = _TOURNAMENT_VENUES[year][0]
    stub = _VENUE_STUBS[label].copy()
    stub["stadium"] = label
    return {"Main": stub}


def _label_round(r):
    """True if round is knockout (not group stage)."""
    return r.startswith("R16") or r.startswith("QF") or r.startswith("SF") or r in ("3rd", "Final")


def _is_draw(match):
    return match[3] == match[4]


def run():
    _ORIG_TEAMS = data_module.TEAMS
    _ORIG_VENUES = data_module.VENUES
    _ORIG_WEIGHTS = dict(WEIGHTS)

    for f in FACTORS_ZERO:
        WEIGHTS[f] = 0.0
    _renorm = 1.0 / sum(WEIGHTS.values())
    for k in WEIGHTS:
        WEIGHTS[k] *= _renorm

    years = ["1998", "2002", "2006", "2010", "2014", "2018", "2022"]

    grand_total = grand_correct = 0
    cum_draws_actual = 0
    cum_draws_pred = 0
    cum_draws_correct = 0
    try:
        for year in years:
            teams = _build_teams_for_year(year)
            venues = _build_venues_for_year(year)
            data_module.TEAMS = teams
            data_module.VENUES = venues

            matches = _HISTORICAL_MATCHES.get(year, [])
            correct = 0
            total = 0
            correct_gs = 0
            total_gs = 0
            correct_ko = 0
            total_ko = 0
            predicted_draws = 0
            actual_draws = 0
            correct_draws = 0

            for round_label, team_a, team_b, actual_a, actual_b in matches:
                is_ko = _label_round(round_label)
                venue_name = "Main"
                result = predict_match(
                    team_a, team_b, venue_name,
                    is_neutral=is_ko,
                    allows_draw=not is_ko,
                    round_name=round_label,
                )

                pred_a = result["score_a"]
                pred_b = result["score_b"]

                if pred_a > pred_b:
                    predicted_winner = team_a
                elif pred_b > pred_a:
                    predicted_winner = team_b
                else:
                    predicted_winner = "Empate"

                if actual_a > actual_b:
                    actual_winner = team_a
                elif actual_b > actual_a:
                    actual_winner = team_b
                elif is_ko:
                    r_a = _HISTORICAL_RANKINGS[year].get(team_a, 50)
                    r_b = _HISTORICAL_RANKINGS[year].get(team_b, 50)
                    actual_winner = team_a if r_a <= r_b else team_b
                else:
                    actual_winner = "Empate"

                if actual_winner == "Empate":
                    actual_draws += 1

                if predicted_winner == "Empate":
                    predicted_draws += 1
                    if actual_winner == "Empate":
                        correct_draws += 1

                is_correct = predicted_winner == actual_winner
                if is_correct:
                    correct += 1
                    if is_ko:
                        correct_ko += 1
                    else:
                        correct_gs += 1

                total += 1
                if is_ko:
                    total_ko += 1
                else:
                    total_gs += 1

            acc = correct / total * 100 if total else 0
            acc_gs = correct_gs / total_gs * 100 if total_gs else 0
            acc_ko = correct_ko / total_ko * 100 if total_ko else 0
            ds = actual_draws - predicted_draws
            grand_total += total
            grand_correct += correct
            cum_draws_actual += actual_draws
            cum_draws_pred += predicted_draws
            cum_draws_correct += correct_draws
            print(f"\n--- {year} ({total} partidos) ---")
            print(f"  Exactitud:        {acc:.1f}%")
            print(f"  Fase grupos:      {acc_gs:.1f}%")
            print(f"  Eliminatorias:    {acc_ko:.1f}%")
            print(f"  Empates reales:   {actual_draws}")
            print(f"  Empates predichos:{predicted_draws}")
            print(f"  Diferencia:       {ds:+d}")
            print(f"  Draw precision:   {correct_draws/max(predicted_draws,1)*100:.0f}%")
        avg_acc = grand_correct / grand_total * 100 if grand_total else 0
        print(f"\n{'='*40}")
        print(f"  RESUMEN {grand_total} PARTIDOS (1998-2022)")
        print(f"{'='*40}")
        print(f"  Exactitud global:  {avg_acc:.1f}%")
        print(f"  Empates totales:   reales={cum_draws_actual}, predichos={cum_draws_pred}")
        print(f"  Draw precision:    {cum_draws_correct/max(cum_draws_pred,1)*100:.0f}%")
        print(f"  Factores activos:  9/18 (cero: player, mv, exp, trophy, ")
        print(f"                     height, chemistry, odds, depth, stakes)")
        print(f"  Simulaciones:      1500 poisson per match (con τ)")
        print(f"{'='*40}")
    finally:
        data_module.TEAMS = _ORIG_TEAMS
        data_module.VENUES = _ORIG_VENUES
        if _ORIG_WEIGHTS:
            WEIGHTS.clear()
            WEIGHTS.update(_ORIG_WEIGHTS)


if __name__ == "__main__":
    run()
