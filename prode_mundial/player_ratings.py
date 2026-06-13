# -*- coding: utf-8 -*-
"""Player Ratings System — SQLite backend for real Sofascore match ratings."""

import sqlite3
import json
import os
import re

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

_DEF_POS = {
    "Defensa Central", "Defensa Lateral Derecho", "Defensa Lateral Izquierdo",
    "Lateral Derecho", "Lateral Izquierdo",
}
_MID_POS = {
    "Centrocampista defensivo", "Interior Derecho",
    "Mediocampista Central", "Mediocampista Ofensivo",
    "Mediocentro", "Mediocentro Ofensivo", "Pivote",
    "Volante Derecho", "Volante Izquierdo",
}
_FWD_POS = {
    "Delantero", "Delantero Centro", "Delantero Derecho", "Delantero Izquierdo",
    "Extremo Derecho", "Extremo Izquierdo",
}
_GK_POS = {"Arquero", "Portero"}

def _categorize_position(pos):
    if pos in _GK_POS:
        return "Arquero"
    if pos in _DEF_POS:
        return "Defensa"
    if pos in _MID_POS:
        return "Mediocampista"
    if pos in _FWD_POS:
        return "Delantero"
    return "Mediocampista"

_TEAM_KEY_MAP = {
    "Korea Republic": "South Korea",
    "Czech Republic": "Czechia",
    "Bosnia & Herzegovina": "Bosnia & Herzegovina",
}

_SOFASCORE_NAME_MAP = {
    "Mexico": {
        "Julián Quiñones": "Julian Quiñones",
        "Roberto Alvarado": "Roberto Alvarado",
        "Raúl Jiménez": "Raúl Jiménez",
        "Erik Lira": "Érik Lira",
        "Raúl Rangel": "Raúl Rangel",
        "Israel Reyes": "Israel Reyes",
        "Álvaro Fidalgo": "Álvaro Fidalgo",
        "Edson Álvarez": "Edson Álvarez",
        "Brian Gutiérrez": "Brian Gutiérrez",
        "Jesús Gallardo": "Jesús Gallardo",
        "Johan Vásquez": "Johan Vásquez",
        "César Montes": "César Montes",
        "Luis Chávez": "Luis Chávez",
        "Gilberto Mora": "Gilberto Mora",
        "Alexis Vega": "Alexis Vega",
        "Armando González": "Armando González",
    },
    "South Africa": {
        "Evidence Makgopa": "Evidence Makgopa",
        "Jayden Adams": "Jayden Adams",
        "Oswin Appollis": "Oswin Appollis",
        "Khuliso Mudau": "Khuliso Mudau",
        "Thalente Mbatha": "Thalente Mbatha",
        "Teboho Mokoena": "Teboho Mokoena",
        "Mbekezeli Mbokazi": "Mbekezeli Mbokazi",
        "Ime Okon": "Ime Okon",
        "Ronwen Williams": "Ronwen Williams",
        "Iqraam Rayners": "Iqraam Rayners",
        "Nkosinathi Sibisi": "Nkosinathi Sibisi",
        "Aubrey Modiba": "Aubrey Modiba",
        "Lyle Foster": "Lyle Foster",
        "Themba Zwane": "Themba Zwane",
        "Siphephelo Sithole": "Yaya Sithole",
    },
    "South Korea": {
        "Hwang In-beom": "In-beom Hwang",
        "Kang-in Lee": "Kang-in Lee",
        "Hyeon-gyu Oh": "Hyeon-gyu Oh",
        "Kim Seung-gyu": "Seung-gyu Kim",
        "Lee Tae-seok": "Tae-seok Lee",
        "Seung Ho Paik": "Seung-ho Paik",
        "Ji-sung Eom": "Ji-sung Eom",
        "Gi-Hyuk Lee": "Gi-hyuk Lee",
        "Jae-sung Lee": "Jae-sung Lee",
        "Kim Min-jae": "Min-jae Kim",
        "Han-Beom Lee": "Han-beom Lee",
        "Son Heung-min": "Heung-min Son",
        "Hwang Hee-chan": "Hee-chan Hwang",
        "Jin-gyu Kim": "Jin-gyu Kim",
        "Jin-seob Park": "Jin-seob Park",
        "Young-woo Seol": "Young-woo Seol",
    },
    "Korea Republic": {
        "Hwang In-beom": "In-beom Hwang",
        "Kang-in Lee": "Kang-in Lee",
        "Hyeon-gyu Oh": "Hyeon-gyu Oh",
        "Kim Seung-gyu": "Seung-gyu Kim",
        "Lee Tae-seok": "Tae-seok Lee",
        "Seung Ho Paik": "Seung-ho Paik",
        "Ji-sung Eom": "Ji-sung Eom",
        "Gi-Hyuk Lee": "Gi-hyuk Lee",
        "Jae-sung Lee": "Jae-sung Lee",
        "Kim Min-jae": "Min-jae Kim",
        "Han-Beom Lee": "Han-beom Lee",
        "Son Heung-min": "Heung-min Son",
        "Hwang Hee-chan": "Hee-chan Hwang",
        "Jin-gyu Kim": "Jin-gyu Kim",
        "Jin-seob Park": "Jin-seob Park",
        "Young-woo Seol": "Young-woo Seol",
    },
    "Czechia": {
        "Ladislav Krejčí": "Ladislav Krejčí",
        "Adam Hložek": "Adam Hložek",
        "Matěj Kovář": "Matej Kovar",
        "Lukáš Provod": "Lukas Provod",
        "Jaroslav Zelený": "Jaroslav Zeleny",
        "Alexandr Sojka": "Alexandr Sojka",
        "Pavel Šulc": "Pavel Šulc",
        "Michal Sadílek": "Michal Sadilek",
        "Tomáš Souček": "Tomas Soucek",
        "Tomáš Chorý": "Tomas Chorý",
        "Mojmír Chytil": "Mojmir Chytil",
        "Patrik Schick": "Patrik Schick",
        "Vladimír Coufal": "Vladimir Coufal",
        "Robin Hranáč": "Robin Hranáč",
        "Štěpán Chaloupek": "Štěpán Chaloupek",
    },
    "Czech Republic": {
        "Ladislav Krejčí": "Ladislav Krejčí",
        "Adam Hložek": "Adam Hložek",
        "Matěj Kovář": "Matej Kovar",
        "Lukáš Provod": "Lukas Provod",
        "Jaroslav Zelený": "Jaroslav Zeleny",
        "Alexandr Sojka": "Alexandr Sojka",
        "Pavel Šulc": "Pavel Šulc",
        "Michal Sadílek": "Michal Sadilek",
        "Tomáš Souček": "Tomas Soucek",
        "Tomáš Chorý": "Tomas Chorý",
        "Mojmír Chytil": "Mojmir Chytil",
        "Patrik Schick": "Patrik Schick",
        "Vladimír Coufal": "Vladimir Coufal",
        "Robin Hranáč": "Robin Hranáč",
        "Štěpán Chaloupek": "Štěpán Chaloupek",
    },
    "Canada": {
        "Richie Laryea": "Richie Laryea",
        "Cyle Larin": "Cyle Larin",
        "Stephen Eustaquio": "Stephen Eustáquio",
        "Alistair Johnston": "Alistair Johnston",
        "Maxime Crépeau": "Maxime Crépeau",
        "Jacob Shaffelburg": "Jacob Shaffelburg",
        "Luc De Fougerolles": "Luc De Fougerolles",
        "Liam Millar": "Liam Millar",
        "Ali Ahmed": "Ali Ahmed",
        "Derek Cornelius": "Derek Cornelius",
        "Ismael Koné": "Ismaël Koné",
        "Promise David": "Promise David",
        "Jonathan David": "Jonathan David",
        "Tajon Buchanan": "Tajon Buchanan",
        "Tani Oluwaseyi": "Tani Oluwaseyi",
        "Jonathan Osorio": "Jonathan Osorio",
    },
    "Bosnia & Herzegovina": {
        "Nikola Katić": "Nikola Katic",
        "Sead Kolašinac": "Sead Kolasinac",
        "Tarik Muharemović": "Tarik Muharemovic",
        "Ivan Bašić": "Ivan Bašić",
        "Jovo Lukić": "Jovo Lukic",
        "Amar Dedić": "Amar Dedić",
        "Armin Gigović": "Armin Gigovic",
        "Ermedin Demirović": "Ermedin Demirovic",
        "Dženis Burnić": "Dzenis Burnic",
        "Benjamin Tahirović": "Benjamin Tahirovic",
        "Kerim Alajbegović": "Kerim Alajbegovic",
        "Ivan Šunjić": "Ivan Šunjić",
        "Amar Memić": "Amar Memić",
        "Nikola Vasilj": "Nikola Vasilj",
        "Samed Baždar": "Samed Bazdar",
        "Esmir Bajraktarević": "Esmir Bajraktarevic",
    },
    "USA": {
        "Christian Pulišić": "Christian Pulisic",
        "Alexander Freeman": "Alex Freeman",
        "Sergiño Dest": "Sergino Dest",
        "Matthew Freese": "Matt Freese",
    },
    "Paraguay": {
        "Mauricio": "Mauricio Magalhaes",
        "Andres Cubas": "Andrés Cubas",
        "Ramon Sosa": "Ramón Sosa Segundo",
        "Miguel Almiron": "Miguel Almirón",
        "Gustavo Velazquez": "Gustavo Velázquez",
        "Juan Caceres": "Juan José Cáceres",
        "Diego Gomez": "Diego Gómez",
        "Alex Arce": "Álex Arce",
        "Gustavo Gomez": "Gustavo Gómez",
        "Damian Bobadilla": "Damián Bobadilla",
        "Junior Alonso": "Júnior Alonso",
    },
}

_POS_FROM_SOFASCORE = {
    "G": "Arquero",
    "D": "Defensa",
    "M": "Mediocampista",
    "F": "Delantero",
}

_SEED_DATA = [
    {
        "match_id": "MD1_Mexico_SouthAfrica",
        "matchday": 1,
        "team_a": "Mexico",
        "team_b": "South Africa",
        "score_a": 2,
        "score_b": 0,
        "players": {
            "Mexico": [
                {"name": "Julián Quiñones", "pos": "F", "min": 79, "rating": 8.6, "goals": 1, "assists": 0, "tackles": 0, "duels_w": 7, "duels_t": 10, "aerial_w": 0, "aerial_t": 1, "pass_a": 28, "pass_t": 33, "saves": 0},
                {"name": "Roberto Alvarado", "pos": "F", "min": 90, "rating": 8.2, "goals": 0, "assists": 1, "tackles": 5, "duels_w": 9, "duels_t": 14, "aerial_w": 0, "aerial_t": 0, "pass_a": 32, "pass_t": 35, "saves": 0},
                {"name": "Raúl Jiménez", "pos": "F", "min": 76, "rating": 7.6, "goals": 1, "assists": 1, "tackles": 0, "duels_w": 6, "duels_t": 10, "aerial_w": 5, "aerial_t": 6, "pass_a": 15, "pass_t": 19, "saves": 0},
                {"name": "Erik Lira", "pos": "M", "min": 76, "rating": 7.4, "goals": 0, "assists": 1, "tackles": 2, "duels_w": 5, "duels_t": 5, "aerial_w": 1, "aerial_t": 1, "pass_a": 42, "pass_t": 45, "saves": 0},
                {"name": "Raúl Rangel", "pos": "G", "min": 90, "rating": 7.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 26, "pass_t": 30, "saves": 1},
                {"name": "Israel Reyes", "pos": "D", "min": 90, "rating": 7.2, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 1, "aerial_w": 1, "aerial_t": 1, "pass_a": 38, "pass_t": 42, "saves": 0},
                {"name": "Álvaro Fidalgo", "pos": "M", "min": 66, "rating": 7.1, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 3, "aerial_w": 0, "aerial_t": 0, "pass_a": 30, "pass_t": 34, "saves": 0},
                {"name": "Edson Álvarez", "pos": "M", "min": 14, "rating": 7.0, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 2, "duels_t": 2, "aerial_w": 0, "aerial_t": 0, "pass_a": 14, "pass_t": 15, "saves": 0},
                {"name": "Brian Gutiérrez", "pos": "M", "min": 66, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 7, "aerial_w": 0, "aerial_t": 2, "pass_a": 20, "pass_t": 23, "saves": 0},
                {"name": "Jesús Gallardo", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 5, "aerial_w": 3, "aerial_t": 3, "pass_a": 34, "pass_t": 45, "saves": 0},
                {"name": "Johan Vásquez", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 4, "duels_t": 6, "aerial_w": 3, "aerial_t": 5, "pass_a": 75, "pass_t": 81, "saves": 0},
                {"name": "César Montes", "pos": "D", "min": 90, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 6, "aerial_w": 2, "aerial_t": 3, "pass_a": 60, "pass_t": 65, "saves": 0},
                {"name": "Luis Chávez", "pos": "M", "min": 24, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 2, "duels_t": 4, "aerial_w": 0, "aerial_t": 0, "pass_a": 28, "pass_t": 28, "saves": 0},
                {"name": "Gilberto Mora", "pos": "M", "min": 24, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 5, "aerial_w": 0, "aerial_t": 0, "pass_a": 14, "pass_t": 14, "saves": 0},
                {"name": "Alexis Vega", "pos": "F", "min": 11, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 10, "pass_t": 10, "saves": 0},
                {"name": "Armando González", "pos": "F", "min": 14, "rating": 6.2, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 1, "pass_t": 1, "saves": 0},
            ],
            "South Africa": [
                {"name": "Evidence Makgopa", "pos": "F", "min": 14, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 3, "aerial_w": 3, "aerial_t": 3, "pass_a": 2, "pass_t": 5, "saves": 0},
                {"name": "Jayden Adams", "pos": "M", "min": 61, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 2, "aerial_w": 0, "aerial_t": 1, "pass_a": 16, "pass_t": 20, "saves": 0},
                {"name": "Oswin Appollis", "pos": "F", "min": 13, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 1, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 5, "pass_t": 6, "saves": 0},
                {"name": "Khuliso Mudau", "pos": "D", "min": 90, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 4, "duels_w": 7, "duels_t": 11, "aerial_w": 0, "aerial_t": 1, "pass_a": 25, "pass_t": 29, "saves": 0},
                {"name": "Thalente Mbatha", "pos": "M", "min": 34, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 2, "duels_t": 3, "aerial_w": 0, "aerial_t": 0, "pass_a": 4, "pass_t": 7, "saves": 0},
                {"name": "Teboho Mokoena", "pos": "M", "min": 90, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 4, "duels_t": 7, "aerial_w": 2, "aerial_t": 2, "pass_a": 39, "pass_t": 42, "saves": 0},
                {"name": "Mbekezeli Mbokazi", "pos": "D", "min": 90, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 5, "duels_t": 10, "aerial_w": 0, "aerial_t": 1, "pass_a": 23, "pass_t": 30, "saves": 0},
                {"name": "Ime Okon", "pos": "D", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 3, "duels_t": 7, "aerial_w": 1, "aerial_t": 4, "pass_a": 45, "pass_t": 49, "saves": 0},
                {"name": "Ronwen Williams", "pos": "G", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 28, "pass_t": 40, "saves": 4},
                {"name": "Iqraam Rayners", "pos": "F", "min": 76, "rating": 6.1, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 6, "aerial_w": 0, "aerial_t": 4, "pass_a": 9, "pass_t": 10, "saves": 0},
                {"name": "Nkosinathi Sibisi", "pos": "D", "min": 90, "rating": 6.0, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 41, "pass_t": 50, "saves": 0},
                {"name": "Aubrey Modiba", "pos": "D", "min": 77, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 3, "duels_w": 5, "duels_t": 11, "aerial_w": 0, "aerial_t": 1, "pass_a": 12, "pass_t": 15, "saves": 0},
                {"name": "Lyle Foster", "pos": "F", "min": 56, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 7, "aerial_w": 0, "aerial_t": 4, "pass_a": 1, "pass_t": 5, "saves": 0},
                {"name": "Themba Zwane", "pos": "M", "min": 23, "rating": 5.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 3, "aerial_w": 0, "aerial_t": 0, "pass_a": 5, "pass_t": 7, "saves": 0},
                {"name": "Siphephelo Sithole", "pos": "M", "min": 49, "rating": 4.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 8, "aerial_w": 1, "aerial_t": 1, "pass_a": 17, "pass_t": 19, "saves": 0},
            ],
        }
    },
    {
        "match_id": "MD1_Korea_Czechia",
        "matchday": 1,
        "team_a": "Korea Republic",
        "team_b": "Czechia",
        "score_a": 2,
        "score_b": 1,
        "players": {
            "Korea Republic": [
                {"name": "Hwang In-beom", "pos": "M", "min": 84, "rating": 8.8, "goals": 1, "assists": 1, "tackles": 0, "duels_w": 3, "duels_t": 5, "aerial_w": 1, "aerial_t": 2, "pass_a": 73, "pass_t": 81, "saves": 0},
                {"name": "Kang-in Lee", "pos": "F", "min": 90, "rating": 8.2, "goals": 0, "assists": 1, "tackles": 1, "duels_w": 10, "duels_t": 14, "aerial_w": 0, "aerial_t": 0, "pass_a": 38, "pass_t": 38, "saves": 0},
                {"name": "Hyeon-gyu Oh", "pos": "F", "min": 21, "rating": 7.5, "goals": 1, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 4, "aerial_w": 2, "aerial_t": 3, "pass_a": 4, "pass_t": 7, "saves": 0},
                {"name": "Kim Seung-gyu", "pos": "G", "min": 90, "rating": 7.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 19, "pass_t": 34, "saves": 3},
                {"name": "Lee Tae-seok", "pos": "M", "min": 69, "rating": 7.2, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 4, "duels_t": 9, "aerial_w": 3, "aerial_t": 6, "pass_a": 21, "pass_t": 25, "saves": 0},
                {"name": "Seung Ho Paik", "pos": "M", "min": 84, "rating": 7.1, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 4, "aerial_w": 1, "aerial_t": 1, "pass_a": 56, "pass_t": 63, "saves": 0},
                {"name": "Ji-sung Eom", "pos": "F", "min": 21, "rating": 7.0, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 3, "duels_t": 3, "aerial_w": 1, "aerial_t": 1, "pass_a": 2, "pass_t": 3, "saves": 0},
                {"name": "Gi-Hyuk Lee", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 5, "duels_t": 9, "aerial_w": 4, "aerial_t": 6, "pass_a": 58, "pass_t": 62, "saves": 0},
                {"name": "Jae-sung Lee", "pos": "F", "min": 62, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 4, "duels_t": 8, "aerial_w": 2, "aerial_t": 4, "pass_a": 25, "pass_t": 33, "saves": 0},
                {"name": "Kim Min-jae", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 6, "duels_t": 9, "aerial_w": 4, "aerial_t": 5, "pass_a": 51, "pass_t": 54, "saves": 0},
                {"name": "Han-Beom Lee", "pos": "D", "min": 90, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 6, "duels_t": 11, "aerial_w": 5, "aerial_t": 7, "pass_a": 53, "pass_t": 63, "saves": 0},
                {"name": "Son Heung-min", "pos": "F", "min": 69, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 4, "aerial_w": 0, "aerial_t": 1, "pass_a": 20, "pass_t": 22, "saves": 0},
                {"name": "Hwang Hee-chan", "pos": "F", "min": 28, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 3, "aerial_w": 0, "aerial_t": 0, "pass_a": 10, "pass_t": 11, "saves": 0},
                {"name": "Jin-gyu Kim", "pos": "M", "min": 13, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 2, "aerial_w": 1, "aerial_t": 2, "pass_a": 3, "pass_t": 4, "saves": 0},
                {"name": "Jin-seob Park", "pos": "M", "min": 13, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 5, "aerial_w": 3, "aerial_t": 5, "pass_a": 6, "pass_t": 9, "saves": 0},
                {"name": "Young-woo Seol", "pos": "M", "min": 90, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 1, "duels_t": 4, "aerial_w": 0, "aerial_t": 0, "pass_a": 30, "pass_t": 32, "saves": 0},
            ],
            "Czechia": [
                {"name": "Ladislav Krejčí", "pos": "D", "min": 90, "rating": 7.1, "goals": 1, "assists": 0, "tackles": 3, "duels_w": 7, "duels_t": 13, "aerial_w": 3, "aerial_t": 6, "pass_a": 31, "pass_t": 45, "saves": 0},
                {"name": "Adam Hložek", "pos": "F", "min": 26, "rating": 7.0, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 2, "aerial_w": 0, "aerial_t": 1, "pass_a": 4, "pass_t": 4, "saves": 0},
                {"name": "Matěj Kovář", "pos": "G", "min": 90, "rating": 7.0, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 9, "pass_t": 26, "saves": 3},
                {"name": "Lukáš Provod", "pos": "F", "min": 64, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 4, "duels_t": 8, "aerial_w": 0, "aerial_t": 3, "pass_a": 17, "pass_t": 22, "saves": 0},
                {"name": "Jaroslav Zelený", "pos": "M", "min": 90, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 5, "aerial_w": 1, "aerial_t": 2, "pass_a": 22, "pass_t": 28, "saves": 0},
                {"name": "Alexandr Sojka", "pos": "M", "min": 84, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 3, "duels_t": 7, "aerial_w": 0, "aerial_t": 0, "pass_a": 26, "pass_t": 33, "saves": 0},
                {"name": "Pavel Šulc", "pos": "F", "min": 64, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 5, "duels_t": 8, "aerial_w": 1, "aerial_t": 1, "pass_a": 13, "pass_t": 18, "saves": 0},
                {"name": "Michal Sadílek", "pos": "M", "min": 26, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 2, "aerial_w": 0, "aerial_t": 1, "pass_a": 8, "pass_t": 11, "saves": 0},
                {"name": "Tomáš Souček", "pos": "M", "min": 90, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 7, "aerial_w": 2, "aerial_t": 4, "pass_a": 25, "pass_t": 34, "saves": 0},
                {"name": "Tomáš Chorý", "pos": "F", "min": 26, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 5, "duels_t": 11, "aerial_w": 4, "aerial_t": 9, "pass_a": 5, "pass_t": 8, "saves": 0},
                {"name": "Mojmír Chytil", "pos": "F", "min": 13, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 2, "aerial_w": 0, "aerial_t": 1, "pass_a": 2, "pass_t": 2, "saves": 0},
                {"name": "Patrik Schick", "pos": "F", "min": 64, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 6, "aerial_w": 1, "aerial_t": 4, "pass_a": 3, "pass_t": 5, "saves": 0},
                {"name": "Vladimír Coufal", "pos": "M", "min": 90, "rating": 6.4, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 2, "duels_t": 8, "aerial_w": 1, "aerial_t": 4, "pass_a": 17, "pass_t": 26, "saves": 0},
                {"name": "Robin Hranáč", "pos": "D", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 7, "aerial_w": 2, "aerial_t": 3, "pass_a": 30, "pass_t": 36, "saves": 0},
                {"name": "Štěpán Chaloupek", "pos": "D", "min": 90, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 8, "aerial_w": 1, "aerial_t": 4, "pass_a": 18, "pass_t": 29, "saves": 0},
            ],
        }
    },
    {
        "match_id": "MD1_Canada_Bosnia",
        "matchday": 1,
        "team_a": "Canada",
        "team_b": "Bosnia & Herzegovina",
        "score_a": 1,
        "score_b": 1,
        "players": {
            "Canada": [
                {"name": "Richie Laryea", "pos": "D", "min": 90, "rating": 8.1, "goals": 0, "assists": 0, "tackles": 5, "duels_w": 9, "duels_t": 11, "aerial_w": 1, "aerial_t": 3, "pass_a": 27, "pass_t": 37, "saves": 0},
                {"name": "Cyle Larin", "pos": "F", "min": 14, "rating": 7.6, "goals": 1, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 1, "aerial_w": 1, "aerial_t": 2, "pass_a": 3, "pass_t": 3, "saves": 0},
                {"name": "Stephen Eustaquio", "pos": "M", "min": 89, "rating": 7.0, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 4, "duels_t": 7, "aerial_w": 0, "aerial_t": 1, "pass_a": 42, "pass_t": 47, "saves": 0},
                {"name": "Alistair Johnston", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 5, "duels_t": 7, "aerial_w": 1, "aerial_t": 1, "pass_a": 24, "pass_t": 36, "saves": 0},
                {"name": "Maxime Crépeau", "pos": "G", "min": 90, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 2, "aerial_w": 1, "aerial_t": 1, "pass_a": 17, "pass_t": 24, "saves": 2},
                {"name": "Jacob Shaffelburg", "pos": "F", "min": 29, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 1, "duels_t": 4, "aerial_w": 0, "aerial_t": 1, "pass_a": 5, "pass_t": 7, "saves": 0},
                {"name": "Luc De Fougerolles", "pos": "D", "min": 90, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 3, "duels_w": 11, "duels_t": 22, "aerial_w": 4, "aerial_t": 13, "pass_a": 39, "pass_t": 50, "saves": 0},
                {"name": "Liam Millar", "pos": "M", "min": 61, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 6, "duels_t": 13, "aerial_w": 2, "aerial_t": 5, "pass_a": 21, "pass_t": 28, "saves": 0},
                {"name": "Ali Ahmed", "pos": "M", "min": 29, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 5, "aerial_w": 0, "aerial_t": 1, "pass_a": 10, "pass_t": 18, "saves": 0},
                {"name": "Derek Cornelius", "pos": "D", "min": 90, "rating": 6.6, "goals": 0, "assists": 0, "tackles": 4, "duels_w": 9, "duels_t": 16, "aerial_w": 4, "aerial_t": 11, "pass_a": 50, "pass_t": 66, "saves": 0},
                {"name": "Ismael Koné", "pos": "M", "min": 90, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 4, "duels_t": 17, "aerial_w": 1, "aerial_t": 6, "pass_a": 50, "pass_t": 59, "saves": 0},
                {"name": "Promise David", "pos": "F", "min": 29, "rating": 6.5, "goals": 0, "assists": 1, "tackles": 1, "duels_w": 3, "duels_t": 10, "aerial_w": 1, "aerial_t": 3, "pass_a": 1, "pass_t": 3, "saves": 0},
                {"name": "Jonathan David", "pos": "F", "min": 61, "rating": 6.3, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 2, "duels_t": 4, "aerial_w": 0, "aerial_t": 1, "pass_a": 8, "pass_t": 14, "saves": 0},
                {"name": "Tajon Buchanan", "pos": "M", "min": 61, "rating": 6.2, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 3, "duels_t": 10, "aerial_w": 0, "aerial_t": 2, "pass_a": 6, "pass_t": 7, "saves": 0},
                {"name": "Tani Oluwaseyi", "pos": "F", "min": 76, "rating": 6.2, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 8, "duels_t": 19, "aerial_w": 5, "aerial_t": 13, "pass_a": 6, "pass_t": 20, "saves": 0},
                {"name": "Jonathan Osorio", "pos": "M", "min": 1, "rating": None, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 4, "pass_t": 5, "saves": 0},
            ],
            "Bosnia & Herzegovina": [
                {"name": "Nikola Katić", "pos": "D", "min": 90, "rating": 8.1, "goals": 0, "assists": 0, "tackles": 5, "duels_w": 15, "duels_t": 24, "aerial_w": 10, "aerial_t": 15, "pass_a": 14, "pass_t": 23, "saves": 0},
                {"name": "Sead Kolašinac", "pos": "D", "min": 84, "rating": 7.9, "goals": 0, "assists": 1, "tackles": 2, "duels_w": 5, "duels_t": 9, "aerial_w": 1, "aerial_t": 2, "pass_a": 15, "pass_t": 21, "saves": 0},
                {"name": "Tarik Muharemović", "pos": "D", "min": 90, "rating": 7.8, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 9, "duels_t": 11, "aerial_w": 6, "aerial_t": 7, "pass_a": 24, "pass_t": 31, "saves": 0},
                {"name": "Ivan Bašić", "pos": "M", "min": 62, "rating": 7.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 5, "aerial_w": 1, "aerial_t": 2, "pass_a": 17, "pass_t": 21, "saves": 0},
                {"name": "Jovo Lukić", "pos": "F", "min": 62, "rating": 7.4, "goals": 1, "assists": 1, "tackles": 0, "duels_w": 10, "duels_t": 13, "aerial_w": 9, "aerial_t": 9, "pass_a": 7, "pass_t": 17, "saves": 0},
                {"name": "Amar Dedić", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 6, "duels_t": 10, "aerial_w": 3, "aerial_t": 3, "pass_a": 14, "pass_t": 22, "saves": 0},
                {"name": "Armin Gigović", "pos": "M", "min": 28, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 5, "duels_t": 8, "aerial_w": 1, "aerial_t": 1, "pass_a": 12, "pass_t": 16, "saves": 0},
                {"name": "Ermedin Demirović", "pos": "F", "min": 90, "rating": 6.8, "goals": 0, "assists": 0, "tackles": 3, "duels_w": 11, "duels_t": 22, "aerial_w": 7, "aerial_t": 11, "pass_a": 12, "pass_t": 17, "saves": 0},
                {"name": "Dženis Burnić", "pos": "M", "min": 13, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 2, "pass_t": 2, "saves": 0},
                {"name": "Benjamin Tahirović", "pos": "M", "min": 90, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 3, "duels_w": 5, "duels_t": 8, "aerial_w": 1, "aerial_t": 2, "pass_a": 17, "pass_t": 24, "saves": 0},
                {"name": "Kerim Alajbegović", "pos": "F", "min": 16, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 3, "aerial_w": 0, "aerial_t": 0, "pass_a": 5, "pass_t": 5, "saves": 0},
                {"name": "Ivan Šunjić", "pos": "M", "min": 16, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 3, "aerial_w": 1, "aerial_t": 1, "pass_a": 10, "pass_t": 14, "saves": 0},
                {"name": "Amar Memić", "pos": "M", "min": 74, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 8, "aerial_w": 1, "aerial_t": 2, "pass_a": 3, "pass_t": 7, "saves": 0},
                {"name": "Nikola Vasilj", "pos": "G", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 11, "pass_t": 30, "saves": 2},
                {"name": "Samed Baždar", "pos": "F", "min": 28, "rating": 6.2, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 4, "duels_t": 13, "aerial_w": 1, "aerial_t": 6, "pass_a": 2, "pass_t": 6, "saves": 0},
                {"name": "Esmir Bajraktarević", "pos": "M", "min": 74, "rating": 6.0, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 13, "aerial_w": 1, "aerial_t": 3, "pass_a": 7, "pass_t": 15, "saves": 0},
            ],
        }
    },
    {
        "match_id": "MD1_USA_Paraguay",
        "matchday": 1,
        "team_a": "USA",
        "team_b": "Paraguay",
        "score_a": 4,
        "score_b": 1,
        "players": {
            "USA": [
                {"name": "Christian Pulišić", "pos": "F", "min": 90, "rating": 8.5, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 5, "duels_t": 8, "aerial_w": 0, "aerial_t": 0, "pass_a": 63, "pass_t": 70, "saves": 0},
                {"name": "Folarin Balogun", "pos": "F", "min": 75, "rating": 9.1, "goals": 2, "assists": 0, "tackles": 0, "duels_w": 4, "duels_t": 8, "aerial_w": 1, "aerial_t": 2, "pass_a": 20, "pass_t": 25, "saves": 0},
                {"name": "Malik Tillman", "pos": "M", "min": 82, "rating": 8.1, "goals": 0, "assists": 1, "tackles": 2, "duels_w": 6, "duels_t": 10, "aerial_w": 1, "aerial_t": 2, "pass_a": 48, "pass_t": 55, "saves": 0},
                {"name": "Giovanni Reyna", "pos": "F", "min": 90, "rating": 7.5, "goals": 1, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 6, "aerial_w": 0, "aerial_t": 1, "pass_a": 42, "pass_t": 48, "saves": 0},
                {"name": "Sergiño Dest", "pos": "D", "min": 82, "rating": 7.3, "goals": 0, "assists": 0, "tackles": 3, "duels_w": 7, "duels_t": 11, "aerial_w": 1, "aerial_t": 2, "pass_a": 54, "pass_t": 62, "saves": 0},
                {"name": "Joe Scally", "pos": "D", "min": 90, "rating": 6.9, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 5, "duels_t": 9, "aerial_w": 2, "aerial_t": 4, "pass_a": 58, "pass_t": 68, "saves": 0},
                {"name": "Mark McKenzie", "pos": "D", "min": 90, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 4, "duels_t": 7, "aerial_w": 3, "aerial_t": 5, "pass_a": 72, "pass_t": 80, "saves": 0},
                {"name": "Matthew Freese", "pos": "G", "min": 90, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 26, "pass_t": 32, "saves": 1},
                {"name": "Weston McKennie", "pos": "M", "min": 72, "rating": 6.7, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 7, "duels_t": 14, "aerial_w": 3, "aerial_t": 6, "pass_a": 37, "pass_t": 42, "saves": 0},
                {"name": "Tyler Adams", "pos": "M", "min": 90, "rating": 6.5, "goals": 0, "assists": 0, "tackles": 4, "duels_w": 9, "duels_t": 15, "aerial_w": 1, "aerial_t": 3, "pass_a": 55, "pass_t": 62, "saves": 0},
                {"name": "Tim Ream", "pos": "D", "min": 66, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 4, "aerial_w": 2, "aerial_t": 3, "pass_a": 48, "pass_t": 52, "saves": 0},
                {"name": "Alexander Freeman", "pos": "D", "min": 8, "rating": 6.7, "goals": 0, "assists": 1, "tackles": 0, "duels_w": 1, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 4, "pass_t": 4, "saves": 0},
                {"name": "Chris Richards", "pos": "D", "min": 24, "rating": 7.0, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 3, "aerial_w": 1, "aerial_t": 2, "pass_a": 18, "pass_t": 20, "saves": 0},
                {"name": "Sebastian Berhalter", "pos": "M", "min": 18, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 1, "duels_t": 3, "aerial_w": 0, "aerial_t": 1, "pass_a": 12, "pass_t": 14, "saves": 0},
                {"name": "Ricardo Pepi", "pos": "F", "min": 15, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 3, "aerial_w": 0, "aerial_t": 1, "pass_a": 3, "pass_t": 4, "saves": 0},
                {"name": "Timothy Weah", "pos": "F", "min": 8, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 1, "aerial_w": 0, "aerial_t": 0, "pass_a": 4, "pass_t": 5, "saves": 0},
            ],
            "Paraguay": [
                {"name": "Julio Enciso", "pos": "F", "min": 90, "rating": 7.2, "goals": 0, "assists": 1, "tackles": 1, "duels_w": 7, "duels_t": 14, "aerial_w": 2, "aerial_t": 4, "pass_a": 22, "pass_t": 30, "saves": 0},
                {"name": "Mauricio", "pos": "D", "min": 19, "rating": 6.6, "goals": 1, "assists": 0, "tackles": 0, "duels_w": 2, "duels_t": 3, "aerial_w": 1, "aerial_t": 2, "pass_a": 6, "pass_t": 8, "saves": 0},
                {"name": "Ramon Sosa", "pos": "F", "min": 34, "rating": 6.4, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 7, "aerial_w": 1, "aerial_t": 2, "pass_a": 10, "pass_t": 16, "saves": 0},
                {"name": "Gustavo Velazquez", "pos": "D", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 2, "duels_w": 4, "duels_t": 8, "aerial_w": 2, "aerial_t": 4, "pass_a": 20, "pass_t": 28, "saves": 0},
                {"name": "Omar Alderete", "pos": "D", "min": 90, "rating": 6.3, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 3, "duels_t": 7, "aerial_w": 2, "aerial_t": 4, "pass_a": 24, "pass_t": 32, "saves": 0},
                {"name": "Andres Cubas", "pos": "M", "min": 71, "rating": 6.2, "goals": 0, "assists": 0, "tackles": 4, "duels_w": 6, "duels_t": 12, "aerial_w": 1, "aerial_t": 3, "pass_a": 28, "pass_t": 36, "saves": 0},
                {"name": "Miguel Almiron", "pos": "F", "min": 71, "rating": 6.1, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 3, "duels_t": 8, "aerial_w": 0, "aerial_t": 0, "pass_a": 18, "pass_t": 24, "saves": 0},
                {"name": "Gustavo Gomez", "pos": "D", "min": 90, "rating": 6.0, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 5, "duels_t": 10, "aerial_w": 4, "aerial_t": 6, "pass_a": 26, "pass_t": 32, "saves": 0},
                {"name": "Diego Gomez", "pos": "M", "min": 34, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 6, "aerial_w": 0, "aerial_t": 1, "pass_a": 10, "pass_t": 16, "saves": 0},
                {"name": "Alex Arce", "pos": "F", "min": 56, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 4, "aerial_w": 0, "aerial_t": 2, "pass_a": 6, "pass_t": 8, "saves": 0},
                {"name": "Orlando Gill", "pos": "G", "min": 90, "rating": 5.9, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 0, "duels_t": 0, "aerial_w": 0, "aerial_t": 0, "pass_a": 20, "pass_t": 30, "saves": 3},
                {"name": "Antonio Sanabria", "pos": "F", "min": 56, "rating": 5.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 5, "aerial_w": 0, "aerial_t": 3, "pass_a": 4, "pass_t": 6, "saves": 0},
                {"name": "Junior Alonso", "pos": "D", "min": 24, "rating": 5.8, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 3, "aerial_w": 1, "aerial_t": 1, "pass_a": 8, "pass_t": 12, "saves": 0},
                {"name": "Alejandro Romero", "pos": "M", "min": 19, "rating": 5.7, "goals": 0, "assists": 0, "tackles": 0, "duels_w": 1, "duels_t": 2, "aerial_w": 0, "aerial_t": 0, "pass_a": 6, "pass_t": 8, "saves": 0},
                {"name": "Juan Caceres", "pos": "D", "min": 66, "rating": 5.5, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 6, "aerial_w": 1, "aerial_t": 3, "pass_a": 14, "pass_t": 20, "saves": 0},
                {"name": "Damian Bobadilla", "pos": "M", "min": 56, "rating": 5.5, "goals": 0, "assists": 0, "tackles": 1, "duels_w": 2, "duels_t": 7, "aerial_w": 0, "aerial_t": 1, "pass_a": 12, "pass_t": 16, "saves": 0},
            ],
        }
    },
]


def _compute_highlight(p):
    rating = p.get("rating")
    pos = p.get("_position_cat") or p.get("position") or "Mediocampista"
    goals = p.get("goals", p.get("total_goals", 0))
    assists = p.get("assists", p.get("total_assists", 0))
    tackles = p.get("tackles", 0)
    dw = p.get("duels_w", p.get("duels_won", 0))
    dt = p.get("duels_t", p.get("duels_total", 0))
    aw = p.get("aerial_w", p.get("aerial_duels_won", 0))
    at = p.get("aerial_t", p.get("aerial_duels_total", 0))
    pa = p.get("pass_a", p.get("passes_accurate", 0))
    pt = p.get("pass_t", p.get("passes_total", 0))
    saves = p.get("saves", 0)

    if pos == "Arquero":
        pass_pct = f"{int(pa/pt*100)}%" if pt > 0 else "—"
        hl = f"{saves} atajadas · {pass_pct} pases"
    elif pos == "Defensa":
        pass_pct = f"{int(pa/pt*100)}%" if pt > 0 else "—"
        duel_str = f"{dw}/{dt}" if dt > 0 else "—"
        if tackles > 0:
            hl = f"{tackles} entradas · {pass_pct}"
        else:
            hl = f"{duel_str} duelos · {pass_pct}"
    elif pos == "Mediocampista":
        pass_pct = f"{int(pa/pt*100)}%" if pt > 0 else "—"
        duel_str = f"{dw}/{dt}" if dt > 0 else "—"
        if assists > 0:
            hl = f"{assists} asistencias · {pass_pct}"
        else:
            hl = f"{duel_str} duelos · {pass_pct}"
    elif pos == "Delantero":
        duel_str = f"{dw}/{dt}" if dt > 0 else "—"
        if goals > 0:
            hl = f"{goals} goles · {duel_str} duelos"
        else:
            pass_pct = f"{int(pa/pt*100)}%" if pt > 0 else "—"
            hl = f"{duel_str} duelos · {pass_pct}"
    else:
        hl = ""

    return hl


class PlayerRatingsDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(OUTPUT_DIR, "db_ratings.db")
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        conn = self._connect()
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                matchday INTEGER NOT NULL,
                team_a TEXT NOT NULL,
                team_b TEXT NOT NULL,
                score_a INTEGER DEFAULT 0,
                score_b INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS player_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                team TEXT NOT NULL,
                player_name TEXT NOT NULL,
                sofascore_name TEXT,
                position TEXT NOT NULL,
                minutes INTEGER DEFAULT 0,
                rating REAL,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                tackles INTEGER DEFAULT 0,
                duels_won INTEGER DEFAULT 0,
                duels_total INTEGER DEFAULT 0,
                aerial_duels_won INTEGER DEFAULT 0,
                aerial_duels_total INTEGER DEFAULT 0,
                passes_accurate INTEGER DEFAULT 0,
                passes_total INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                UNIQUE(match_id, team, player_name)
            );
            CREATE INDEX IF NOT EXISTS idx_player ON player_ratings(player_name);
            CREATE INDEX IF NOT EXISTS idx_team ON player_ratings(team);
            CREATE INDEX IF NOT EXISTS idx_match ON player_ratings(match_id);
            CREATE INDEX IF NOT EXISTS idx_rating ON player_ratings(rating);
        """)
        conn.commit()
        conn.close()

    def _get_players_json_name(self, team, sofascore_name):
        name_map = _SOFASCORE_NAME_MAP.get(team, {})
        return name_map.get(sofascore_name, sofascore_name)

    def insert_match_ratings(self, match_id, matchday, team_a, team_b,
                             score_a, score_b, players_dict):
        conn = self._connect()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO matches VALUES (?,?,?,?,?,?)",
                  (match_id, matchday, team_a, team_b, score_a, score_b))
        for team_name, player_list in players_dict.items():
            db_team = _TEAM_KEY_MAP.get(team_name, team_name)
            for p in player_list:
                rating = p.get("rating")
                if rating is None:
                    continue
                pj_name = self._get_players_json_name(team_name, p["name"])
                pos_code = p.get("pos", "M")
                pos_cat = _POS_FROM_SOFASCORE.get(pos_code, "Mediocampista")
                c.execute("""
                    INSERT OR REPLACE INTO player_ratings
                    (match_id, team, player_name, sofascore_name, position,
                     minutes, rating, goals, assists, tackles,
                     duels_won, duels_total, aerial_duels_won, aerial_duels_total,
                     passes_accurate, passes_total, saves)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    match_id, db_team, pj_name, p["name"], pos_cat,
                    p.get("min", 0), rating,
                    p.get("goals", 0), p.get("assists", 0), p.get("tackles", 0),
                    p.get("duels_w", 0), p.get("duels_t", 0),
                    p.get("aerial_w", 0), p.get("aerial_t", 0),
                    p.get("pass_a", 0), p.get("pass_t", 0),
                    p.get("saves", 0),
                ))
        conn.commit()
        conn.close()

    def seed_if_empty(self):
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM matches")
        count = c.fetchone()[0]
        if count > 0:
            c.execute("DELETE FROM player_ratings")
            c.execute("DELETE FROM matches")
        conn.commit()
        conn.close()
        for sd in _SEED_DATA:
            self.insert_match_ratings(
                sd["match_id"], sd["matchday"],
                sd["team_a"], sd["team_b"],
                sd["score_a"], sd["score_b"],
                sd["players"],
            )

    def get_golden_ball(self, limit=1, min_minutes=60):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT player_name, team, position,
                   ROUND(AVG(rating), 2) as avg_rating,
                   COUNT(*) as matches, SUM(goals) + SUM(assists) as g_plus_a,
                   SUM(goals) as goals, SUM(assists) as assists,
                   SUM(tackles) as tackles,
                   SUM(duels_won) as duels_won, SUM(duels_total) as duels_total,
                   SUM(passes_accurate) as passes_accurate,
                   SUM(passes_total) as passes_total,
                   SUM(saves) as saves
            FROM player_ratings
            WHERE rating IS NOT NULL AND minutes >= ?
            GROUP BY player_name
            ORDER BY avg_rating DESC
            LIMIT ?
        """, (min_minutes, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_top_by_position(self, position, limit=5, min_minutes=30):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT player_name, team, ROUND(AVG(rating), 2) as avg_rating,
                   COUNT(*) as matches, SUM(goals) as total_goals,
                   SUM(assists) as total_assists, SUM(saves) as total_saves,
                   AVG(duels_won * 1.0 / NULLIF(duels_total, 0)) as duel_pct
            FROM player_ratings
            WHERE position = ? AND rating IS NOT NULL AND minutes >= ?
            GROUP BY player_name
            ORDER BY avg_rating DESC
            LIMIT ?
        """, (position, min_minutes, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_best_xi(self, matchday=None):
        conn = self._connect()
        c = conn.cursor()
        if matchday:
            where_extra = "AND match_id LIKE ?"
            param = f"MD{matchday}_%"
        else:
            where_extra = ""
            param = None

        def _top(position, extra_clause="", extra_params=()):
            sql = f"""
                SELECT player_name, team, position, ROUND(AVG(rating), 2) as avg_rating,
                       SUM(goals) as goals, SUM(assists) as assists,
                       SUM(saves) as saves, SUM(tackles) as tackles
                FROM player_ratings
                WHERE position = ? AND rating IS NOT NULL AND minutes >= 30
                      {where_extra} {extra_clause}
                GROUP BY player_name
                ORDER BY avg_rating DESC
                LIMIT 1
            """
            params = [position]
            if param:
                params.append(param)
            params.extend(extra_params)
            row = c.execute(sql, params).fetchone()
            return dict(row) if row else None

        # Top GK, top 3 DEF, top 3 MID, top 3 FW
        gk = _top("Arquero")
        defs = c.execute(f"""
            SELECT player_name, team, position, ROUND(AVG(rating), 2) as avg_rating,
                   SUM(goals) as goals, SUM(assists) as assists,
                   SUM(tackles) as tackles
            FROM player_ratings
            WHERE position = 'Defensa' AND rating IS NOT NULL AND minutes >= 30
                  {where_extra}
            GROUP BY player_name
            ORDER BY avg_rating DESC
            LIMIT 3
        """, ([param] if param else [])).fetchall()

        mids = c.execute(f"""
            SELECT player_name, team, position, ROUND(AVG(rating), 2) as avg_rating,
                   SUM(goals) as goals, SUM(assists) as assists
            FROM player_ratings
            WHERE position = 'Mediocampista' AND rating IS NOT NULL AND minutes >= 30
                  {where_extra}
            GROUP BY player_name
            ORDER BY avg_rating DESC
            LIMIT 3
        """, ([param] if param else [])).fetchall()

        fws = c.execute(f"""
            SELECT player_name, team, position, ROUND(AVG(rating), 2) as avg_rating,
                   SUM(goals) as goals, SUM(assists) as assists
            FROM player_ratings
            WHERE position = 'Delantero' AND rating IS NOT NULL AND minutes >= 30
                  {where_extra}
            GROUP BY player_name
            ORDER BY avg_rating DESC
            LIMIT 3
        """, ([param] if param else [])).fetchall()

        conn.close()
        return {
            "gk": dict(gk) if gk else None,
            "def": [dict(r) for r in defs],
            "mid": [dict(r) for r in mids],
            "fw": [dict(r) for r in fws],
        }

    def get_mvp_by_match(self, matchday=None):
        conn = self._connect()
        c = conn.cursor()
        if matchday:
            rows = c.execute("""
                SELECT pr.match_id, pr.player_name, pr.team, pr.rating,
                       m.team_a, m.team_b, m.score_a, m.score_b,
                       pr.goals, pr.assists, pr.duels_won, pr.duels_total,
                       pr.passes_accurate, pr.passes_total, pr.saves,
                       pr.tackles, pr.position
                FROM player_ratings pr
                JOIN matches m ON pr.match_id = m.match_id
                WHERE pr.match_id LIKE ?
                AND pr.rating = (
                    SELECT MAX(rating) FROM player_ratings
                    WHERE match_id = pr.match_id AND rating IS NOT NULL
                )
                ORDER BY pr.match_id
            """, (f"MD{matchday}_%",)).fetchall()
        else:
            rows = c.execute("""
                SELECT pr.match_id, pr.player_name, pr.team, pr.rating,
                       m.team_a, m.team_b, m.score_a, m.score_b,
                       pr.goals, pr.assists, pr.duels_won, pr.duels_total,
                       pr.passes_accurate, pr.passes_total, pr.saves,
                       pr.tackles, pr.position
                FROM player_ratings pr
                JOIN matches m ON pr.match_id = m.match_id
                WHERE pr.rating = (
                    SELECT MAX(rating) FROM player_ratings
                    WHERE match_id = pr.match_id AND rating IS NOT NULL
                )
                ORDER BY pr.match_id
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_top_scorers(self, limit=20):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT player_name, team, SUM(goals) as total_goals,
                   COUNT(*) as matches
            FROM player_ratings
            WHERE goals > 0
            GROUP BY player_name
            ORDER BY total_goals DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_top_assisters(self, limit=20):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT player_name, team, SUM(assists) as total_assists,
                   COUNT(*) as matches
            FROM player_ratings
            WHERE assists > 0
            GROUP BY player_name
            ORDER BY total_assists DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_mejores_por_fase(self):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT m.match_id, m.matchday, m.team_a, m.team_b,
                   m.score_a, m.score_b,
                   pr.player_name, pr.team, pr.rating,
                   pr.goals, pr.assists
            FROM matches m
            JOIN player_ratings pr ON m.match_id = pr.match_id
            WHERE pr.rating = (
                SELECT MAX(rating) FROM player_ratings
                WHERE match_id = m.match_id AND rating IS NOT NULL
            )
            ORDER BY m.matchday, m.match_id
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count_players(self):
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM player_ratings")
        return c.fetchone()[0]

    def get_team_avg_ratings(self, team):
        conn = self._connect()
        c = conn.cursor()
        rows = c.execute("""
            SELECT player_name, ROUND(AVG(rating), 2) as avg_rating
            FROM player_ratings
            WHERE team = ? AND rating IS NOT NULL
            GROUP BY player_name
        """, (team,)).fetchall()
        conn.close()
        return {r["player_name"]: r["avg_rating"] for r in rows}

    def get_team_avg_team_rating(self, team):
        conn = self._connect()
        c = conn.cursor()
        row = c.execute("""
            SELECT ROUND(AVG(rating), 2) as avg_rating
            FROM player_ratings
            WHERE team = ? AND rating IS NOT NULL
        """, (team,)).fetchone()
        conn.close()
        if not row or row["avg_rating"] is None:
            return 0.0
        avg = row["avg_rating"]
        return (avg - 5.0) * 2.0

    def export_standings(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, "jugadores_destacados.json")

        golden_ball = self.get_golden_ball(limit=5, min_minutes=60)
        gk_list = self.get_top_by_position("Arquero", limit=5)
        def_list = self.get_top_by_position("Defensa", limit=5)
        mid_list = self.get_top_by_position("Mediocampista", limit=5)
        fw_list = self.get_top_by_position("Delantero", limit=5)
        best_xi = self.get_best_xi()
        mvp_list = self.get_mvp_by_match()
        scorers = self.get_top_scorers()
        assisters = self.get_top_assisters()
        fases = self.get_mejores_por_fase()

        def _enrich(items):
            out = []
            for d in items:
                d["highlight"] = _compute_highlight(d)
                out.append(d)
            return out

        data = {
            "golden_ball": _enrich(golden_ball),
            "top_positions": {
                "Arquero": _enrich(gk_list),
                "Defensa": _enrich(def_list),
                "Mediocampista": _enrich(mid_list),
                "Delantero": _enrich(fw_list),
            },
            "once_ideal": best_xi,
            "mvp_por_partido": _enrich(mvp_list),
            "goleadores_reales": _enrich(scorers),
            "asistidores_reales": _enrich(assisters),
            "mejores_por_fase": _enrich(fases),
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data


PLAYER_RATINGS_DB = PlayerRatingsDB()
