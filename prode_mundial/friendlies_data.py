# -*- coding: utf-8 -*-
"""Amistosos internacionales previos al Mundial 2026 (22 May - 10 Jun).
Provee datos de resultados, goleadores y tarjetas para factor friendly_form."""

import json
import os

FRIENDLIES = [
    {
        "date": "2026-05-22",
        "home": "Mexico", "away": "Ghana",
        "home_score": 2, "away_score": 0,
        "home_scorers": [{"player": "Brian Gutierrez", "minute": 2}, {"player": "Guillermo Martinez", "minute": 54}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-24",
        "home": "Spain", "away": "Iraq",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Pedri", "minute": 23}],
        "away_scorers": [{"player": "Mohanad Ali", "minute": 67}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },

    {
        "date": "2026-05-28",
        "home": "Egypt", "away": "Russia",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Mohamed Salah", "minute": 33}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-29",
        "home": "Iran", "away": "Gambia",
        "home_score": 3, "away_score": 1,
        "home_scorers": [{"player": "Mehdi Taremi", "minute": 18}, {"player": "Sardar Azmoun", "minute": 45}, {"player": "Alireza Jahanbakhsh", "minute": 77}],
        "away_scorers": [{"player": "Modou Jallow", "minute": 52}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-29",
        "home": "Iraq", "away": "Andorra",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Aymen Hussein", "minute": 41}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-29",
        "home": "South Africa", "away": "Nicaragua",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-29",
        "home": "Bosnia & Herzegovina", "away": "North Macedonia",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-30",
        "home": "Scotland", "away": "Curacao",
        "home_score": 4, "away_score": 1,
        "home_scorers": [
            {"player": "Findlay Curtis", "minute": 45},
            {"player": "Lawrence Shankland", "minute": 59},
            {"player": "Lawrence Shankland", "minute": 64},
            {"player": "Ryan Christie", "minute": 81},
        ],
        "away_scorers": [{"player": "Tahith Chong", "minute": 17}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Ecuador", "away": "Saudi Arabia",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Jackson Porozo", "minute": 35}, {"player": "Anthony Valencia", "minute": 51}],
        "away_scorers": [{"player": "Sultan Mandash", "minute": 87}],
        "cards": {"home_yellow": 1, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "South Korea", "away": "Trinidad and Tobago",
        "home_score": 5, "away_score": 0,
        "home_scorers": [
            {"player": "Son Heung-min", "minute": 40},
            {"player": "Son Heung-min", "minute": 43},
            {"player": "Cho Gue-sung", "minute": 55},
            {"player": "Cho Gue-sung", "minute": 72},
            {"player": "Hwang Hee-chan", "minute": 78},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Mexico", "away": "Australia",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Johan Vasquez", "minute": 28}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Japan", "away": "Iceland",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Koki Ogawa", "minute": 87}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 1, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Switzerland", "away": "Jordan",
        "home_score": 4, "away_score": 1,
        "home_scorers": [
            {"player": "Breel Embolo", "minute": 28},
            {"player": "Dan Ndoye", "minute": 33},
            {"player": "Granit Xhaka", "minute": 45},
            {"player": "Christian Fassnacht", "minute": 79},
        ],
        "away_scorers": [{"player": "Odeh Fakhouri", "minute": 52}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Czechia", "away": "Kosovo",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Tomas Ladra", "minute": 12}, {"player": "Adam Hlozek", "minute": 32}],
        "away_scorers": [{"player": "Lindon Emerllahu", "minute": 80}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Cape Verde", "away": "Serbia",
        "home_score": 3, "away_score": 0,
        "home_scorers": [{"player": "Ryan Mendes", "minute": 22}, {"player": "Jamiro Monteiro", "minute": 45}, {"player": "Gilson Benchimol", "minute": 78}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Germany", "away": "Finland",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Deniz Undav", "minute": 34},
            {"player": "Florian Wirtz", "minute": 48},
            {"player": "Deniz Undav", "minute": 57},
            {"player": "Jamal Musiala", "minute": 63},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "USA", "away": "Senegal",
        "home_score": 3, "away_score": 2,
        "home_scorers": [
            {"player": "Sergino Dest", "minute": 7},
            {"player": "Christian Pulisic", "minute": 20},
            {"player": "Folarin Balogun", "minute": 63},
        ],
        "away_scorers": [{"player": "Sadio Mane", "minute": 44}, {"player": "Sadio Mane", "minute": 52}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-05-31",
        "home": "Brazil", "away": "Panama",
        "home_score": 6, "away_score": 2,
        "home_scorers": [
            {"player": "Vinicius Junior", "minute": 2},
            {"player": "Casemiro", "minute": 39},
            {"player": "Rayan", "minute": 53},
            {"player": "Lucas Paqueta", "minute": 60},
            {"player": "Igor Thiago", "minute": 63},
            {"player": "Danilo", "minute": 81},
        ],
        "away_scorers": [{"player": "Matheus Cunha", "minute": 14}, {"player": "Carlos Harvey", "minute": 84}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-01",
        "home": "Austria", "away": "Tunisia",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Marcel Sabitzer", "minute": 63}],
        "away_scorers": [],
        "cards": {"home_yellow": 2, "home_red": 1, "away_yellow": 1, "away_red": 0},
    },
    {
        "date": "2026-06-01",
        "home": "Norway", "away": "Sweden",
        "home_score": 3, "away_score": 1,
        "home_scorers": [
            {"player": "Jorgen Strand Larsen", "minute": 8},
            {"player": "Antonio Nusa", "minute": 18},
            {"player": "Jorgen Strand Larsen", "minute": 37},
        ],
        "away_scorers": [{"player": "Alexander Isak", "minute": 76}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-01",
        "home": "Turkey", "away": "North Macedonia",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Orkun Kokcu", "minute": 2},
            {"player": "Can Uzun", "minute": 16},
            {"player": "Deniz Gul", "minute": 53},
            {"player": "Baris Alper Yilmaz", "minute": 70},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-02",
        "home": "Colombia", "away": "Costa Rica",
        "home_score": 3, "away_score": 1,
        "home_scorers": [{"player": "Luis Diaz", "minute": 15}, {"player": "James Rodriguez", "minute": 44}, {"player": "Rafael Santos Borre", "minute": 67}],
        "away_scorers": [{"player": "Joel Campbell", "minute": 52}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-02",
        "home": "Canada", "away": "Uzbekistan",
        "home_score": 2, "away_score": 0,
        "home_scorers": [{"player": "Jonathan Osorio", "minute": 58}, {"player": "Jayden Nelson", "minute": 90}],
        "away_scorers": [],
        "cards": {"home_yellow": 2, "home_red": 0, "away_yellow": 2, "away_red": 0},
    },
    {
        "date": "2026-06-02",
        "home": "Croatia", "away": "Belgium",
        "home_score": 0, "away_score": 2,
        "home_scorers": [],
        "away_scorers": [{"player": "Youri Tielemans", "minute": 38}, {"player": "Romelu Lukaku", "minute": 90}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 2, "away_red": 0},
    },
    {
        "date": "2026-06-02",
        "home": "Morocco", "away": "Madagascar",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Hakim Ziyech", "minute": 14},
            {"player": "Youssef En-Nesyri", "minute": 33},
            {"player": "Sofiane Boufal", "minute": 62},
            {"player": "Ayoub El Kaabi", "minute": 78},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-03",
        "home": "Haiti", "away": "New Zealand",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Ruben Providence", "minute": 12},
            {"player": "Lenny Joseph", "minute": 51},
            {"player": "Frantzdy Pierrot", "minute": 62},
            {"player": "Duke Lacroix", "minute": 87},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-03",
        "home": "DR Congo", "away": "Denmark",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-03",
        "home": "Netherlands", "away": "Algeria",
        "home_score": 0, "away_score": 1,
        "home_scorers": [],
        "away_scorers": [{"player": "Anis Hadj Moussa", "minute": 86}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "South Korea", "away": "El Salvador",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Lee Dong-gyeong", "minute": 57}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "Spain", "away": "Iraq",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Mikel Oyarzabal", "minute": 38}],
        "away_scorers": [{"player": "Ibrahim Bayesh", "minute": 72}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "Iran", "away": "Mali",
        "home_score": 2, "away_score": 0,
        "home_scorers": [{"player": "Saeid Ezatolahi", "minute": 12}, {"player": "Ramin Rezaeian", "minute": 55}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "Sweden", "away": "Greece",
        "home_score": 2, "away_score": 2,
        "home_scorers": [{"player": "Viktor Gyokeres", "minute": 30}, {"player": "Emil Forsberg", "minute": 62}],
        "away_scorers": [{"player": "Georgios Masouras", "minute": 45}, {"player": "Anastasios Bakasetas", "minute": 78}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "France", "away": "Ivory Coast",
        "home_score": 1, "away_score": 2,
        "home_scorers": [{"player": "Kylian Mbappe", "minute": 33}],
        "away_scorers": [{"player": "Sebastien Haller", "minute": 41}, {"player": "Franck Kessie", "minute": 67}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-04",
        "home": "Panama", "away": "Dominican Republic",
        "home_score": 4, "away_score": 2,
        "home_scorers": [{"player": "Jose Fajardo", "minute": 18}, {"player": "Adalberto Carrasquilla", "minute": 45}, {"player": "Cecilio Waterman", "minute": 67}, {"player": "Edgar Barcenas", "minute": 88}],
        "away_scorers": [{"player": "Dorny Romero", "minute": 33}, {"player": "Rafael Nunez", "minute": 71}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-05",
        "home": "Mexico", "away": "Serbia",
        "home_score": 5, "away_score": 1,
        "home_scorers": [
            {"player": "Johan Vasquez", "minute": 34},
            {"player": "Stefan Bukinac", "minute": 45},
            {"player": "Raul Jimenez", "minute": 57},
            {"player": "Adem Avdic", "minute": 72},
            {"player": "Luis Chavez", "minute": 90},
        ],
        "away_scorers": [{"player": "Petar Stanic", "minute": 19}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-05",
        "home": "Paraguay", "away": "Nicaragua",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Kaku", "minute": 17},
            {"player": "Miguel Almiron", "minute": 42},
            {"player": "Hector Galarza", "minute": 62},
            {"player": "Allan Maydana", "minute": 67},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-05",
        "home": "Guatemala", "away": "Czechia",
        "home_score": 1, "away_score": 3,
        "home_scorers": [{"player": "Jose Morales", "minute": 44}],
        "away_scorers": [{"player": "Patrik Schick", "minute": 18}, {"player": "Adam Hlozek", "minute": 52}, {"player": "Pavel Sulc", "minute": 76}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Canada", "away": "Republic of Ireland",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Jake O'Brien", "minute": 24}],
        "away_scorers": [{"player": "Chiedozie Ogbene", "minute": 60}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Haiti", "away": "Peru",
        "home_score": 1, "away_score": 2,
        "home_scorers": [{"player": "Wilson Isidor", "minute": 16}],
        "away_scorers": [{"player": "Renzo Garces", "minute": 81}, {"player": "Jairo Velez", "minute": 84}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Belgium", "away": "Tunisia",
        "home_score": 5, "away_score": 0,
        "home_scorers": [
            {"player": "Leandro Trossard", "minute": 10},
            {"player": "Charles De Ketelaere", "minute": 27},
            {"player": "Kevin De Bruyne", "minute": 42},
            {"player": "Dodi Lukebakio", "minute": 65},
            {"player": "Nicolas Raskin", "minute": 80},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 1},
    },
    {
        "date": "2026-06-06",
        "home": "Portugal", "away": "Chile",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Goncalo Guedes", "minute": 35}, {"player": "Bruno Fernandes", "minute": 58}],
        "away_scorers": [{"player": "Lucas Cepeda", "minute": 82}],
        "cards": {"home_yellow": 0, "home_red": 1, "away_yellow": 0, "away_red": 1},
    },
    {
        "date": "2026-06-06",
        "home": "USA", "away": "Germany",
        "home_score": 1, "away_score": 2,
        "home_scorers": [{"player": "Antonee Robinson", "minute": 36}],
        "away_scorers": [{"player": "Kai Havertz", "minute": 2}, {"player": "Leroy Sane", "minute": 57}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Australia", "away": "Switzerland",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Tete Yengi", "minute": 56}],
        "away_scorers": [{"player": "Dan Ndoye", "minute": 14}],
        "cards": {"home_yellow": 1, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Panama", "away": "Bosnia & Herzegovina",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Jiovany Ramos", "minute": 45}],
        "away_scorers": [{"player": "Nikola Katic", "minute": 23}],
        "cards": {"home_yellow": 1, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Scotland", "away": "Bolivia",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Lawrence Shankland", "minute": 5},
            {"player": "Scott McTominay", "minute": 23},
            {"player": "Che Adams", "minute": 30},
            {"player": "Che Adams", "minute": 45},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "England", "away": "New Zealand",
        "home_score": 1, "away_score": 0,
        "home_scorers": [{"player": "Harry Kane", "minute": 45}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "El Salvador", "away": "Qatar",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Brazil", "away": "Egypt",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Bruno Guimaraes", "minute": 8}, {"player": "Endrick", "minute": 64}],
        "away_scorers": [{"player": "Mostafa Ziko", "minute": 11}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-06",
        "home": "Venezuela", "away": "Turkey",
        "home_score": 1, "away_score": 2,
        "home_scorers": [{"player": "Gleiker Mendoza", "minute": 13}],
        "away_scorers": [{"player": "Baris Alper Yilmaz", "minute": 44}, {"player": "Yunus Akgun", "minute": 54}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-07",
        "home": "Argentina", "away": "Honduras",
        "home_score": 2, "away_score": 0,
        "home_scorers": [{"player": "Lautaro Martinez", "minute": 37}, {"player": "Giuliano Simeone", "minute": 54}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-07",
        "home": "Croatia", "away": "Slovenia",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Luka Modric", "minute": 51}, {"player": "Mario Pasalic", "minute": 90}],
        "away_scorers": [{"player": "Andraz Sporar", "minute": 83}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-07",
        "home": "Morocco", "away": "Norway",
        "home_score": 1, "away_score": 1,
        "home_scorers": [{"player": "Brahim Diaz", "minute": 8}],
        "away_scorers": [{"player": "Martin Odegaard", "minute": 75}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-07",
        "home": "Ecuador", "away": "Guatemala",
        "home_score": 3, "away_score": 0,
        "home_scorers": [
            {"player": "Jordy Caicedo", "minute": 19},
            {"player": "Nilson Angulo", "minute": 73},
            {"player": "Pervis Estupinan", "minute": 78},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-07",
        "home": "Curacao", "away": "Aruba",
        "home_score": 4, "away_score": 0,
        "home_scorers": [
            {"player": "Joshua Brenet", "minute": 54},
            {"player": "Jeremy Antonisse", "minute": 61},
            {"player": "Livano Comenencia", "minute": 73},
            {"player": "Juninho Bacuna", "minute": 88},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-08",
        "home": "Colombia", "away": "Jordan",
        "home_score": 2, "away_score": 0,
        "home_scorers": [{"player": "Jhon Arias", "minute": 41}, {"player": "Jhon Arias", "minute": 55}],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 1, "away_red": 1},
    },
    {
        "date": "2026-06-08",
        "home": "Netherlands", "away": "Uzbekistan",
        "home_score": 2, "away_score": 1,
        "home_scorers": [{"player": "Cody Gakpo", "minute": 32}, {"player": "Cody Gakpo", "minute": 90}],
        "away_scorers": [{"player": "Igor Sergeev", "minute": 90}],
        "cards": {"home_yellow": 1, "home_red": 1, "away_yellow": 1, "away_red": 0},
    },
    {
        "date": "2026-06-08",
        "home": "France", "away": "Northern Ireland",
        "home_score": 3, "away_score": 1,
        "home_scorers": [
            {"player": "Michael Olise", "minute": 41},
            {"player": "Michael Olise", "minute": 49},
            {"player": "Michael Olise", "minute": 74},
        ],
        "away_scorers": [{"player": "Patrick Kelly", "minute": 64}],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-09",
        "home": "Peru", "away": "Spain",
        "home_score": 1, "away_score": 3,
        "home_scorers": [{"player": "Jairo Velez", "minute": 66}],
        "away_scorers": [
            {"player": "Mikel Oyarzabal", "minute": 2},
            {"player": "Pedri", "minute": 32},
        ],
        "cards": {"home_yellow": 1, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-09",
        "home": "DR Congo", "away": "Chile",
        "home_score": 1, "away_score": 2,
        "home_scorers": [{"player": "Joris Kayembe", "minute": 88}],
        "away_scorers": [
            {"player": "Dario Osorio", "minute": 51},
            {"player": "Matias Sepulveda", "minute": 86},
        ],
        "cards": {"home_yellow": 1, "home_red": 0, "away_yellow": 3, "away_red": 0},
    },
    {
        "date": "2026-06-09",
        "home": "Argentina", "away": "Iceland",
        "home_score": 3, "away_score": 0,
        "home_scorers": [
            {"player": "Valentin Barco", "minute": 8},
            {"player": "Lionel Messi", "minute": 72},
            {"player": "Thiago Almada", "minute": 86},
        ],
        "away_scorers": [],
        "cards": {"home_yellow": 2, "home_red": 0, "away_yellow": 5, "away_red": 0},
    },
    {
        "date": "2026-06-09",
        "home": "Saudi Arabia", "away": "Senegal",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 3, "home_red": 0, "away_yellow": 2, "away_red": 1},
    },
    {
        "date": "2026-06-09",
        "home": "Iraq", "away": "Venezuela",
        "home_score": 0, "away_score": 2,
        "home_scorers": [],
        "away_scorers": [
            {"player": "Cristian Casseres", "minute": 17},
            {"player": "Jesus Ramirez", "minute": 46},
        ],
        "cards": {"home_yellow": 0, "home_red": 1, "away_yellow": 0, "away_red": 0},
    },
    {
        "date": "2026-06-09",
        "home": "England", "away": "Costa Rica",
        "home_score": 0, "away_score": 0,
        "home_scorers": [],
        "away_scorers": [],
        "cards": {"home_yellow": 0, "home_red": 0, "away_yellow": 0, "away_red": 0},
    },
]


def _is_wc_team(team_name):
    """Verifica si un equipo participa en el Mundial 2026."""
    from prode_mundial.data import TEAMS
    return team_name in TEAMS


def _team_friendly_stats(team_name):
    """Retorna estadisticas de amistosos para un equipo."""
    if not _is_wc_team(team_name):
        return {"gp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0}
    gp = 0
    wins = draws = losses = 0
    gf = ga = 0
    for m in FRIENDLIES:
        if m["home"] == team_name:
            gp += 1
            gf += m["home_score"]
            ga += m["away_score"]
            if m["home_score"] > m["away_score"]:
                wins += 1
            elif m["home_score"] == m["away_score"]:
                draws += 1
            else:
                losses += 1
        elif m["away"] == team_name:
            gp += 1
            gf += m["away_score"]
            ga += m["home_score"]
            if m["away_score"] > m["home_score"]:
                wins += 1
            elif m["away_score"] == m["home_score"]:
                draws += 1
            else:
                losses += 1
    gd = gf - ga
    pts = wins * 3 + draws
    return {"gp": gp, "w": wins, "d": draws, "l": losses, "gf": gf, "ga": ga, "gd": gd, "pts": pts}


def compute_friendly_form(team_name):
    """Calcula factor friendly_form (-10 a 10) basado en rendimiento en amistosos.

    Escala:
      - Diferencia de goles por partido * 3 (max +/- 10)
      - Bonus por pts/partido: > 2 = +2, > 1.5 = +1, < 0.5 = -2
    """
    stats = _team_friendly_stats(team_name)
    if stats["gp"] == 0:
        return 0
    gd_per_game = stats["gd"] / max(stats["gp"], 1)
    base = gd_per_game * 3
    ppg = stats["pts"] / stats["gp"]
    if ppg > 2.3:
        base += 3
    elif ppg > 1.9:
        base += 1.5
    elif ppg > 1.5:
        base += 0.5
    elif ppg < 0.5:
        base -= 2
    elif ppg < 0.8:
        base -= 1
    return max(-10, min(10, base))


def get_friendly_scorers(team_name):
    """Retorna dict {player_name: total_goles} para un equipo en amistosos."""
    if not _is_wc_team(team_name):
        return {}
    scorers = {}
    for m in FRIENDLIES:
        if m["home"] == team_name:
            for s in m["home_scorers"]:
                name = s["player"]
                scorers[name] = scorers.get(name, 0) + 1
        elif m["away"] == team_name:
            for s in m["away_scorers"]:
                name = s["player"]
                scorers[name] = scorers.get(name, 0) + 1
    return scorers


def get_all_friendly_scorers():
    """Retorna dict {player_name: total_goles} para TODOS los equipos."""
    scorers = {}
    for m in FRIENDLIES:
        for s in m["home_scorers"]:
            name = s["player"]
            scorers[name] = scorers.get(name, 0) + 1
        for s in m["away_scorers"]:
            name = s["player"]
            scorers[name] = scorers.get(name, 0) + 1
    return scorers
