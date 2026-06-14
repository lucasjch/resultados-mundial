# -*- coding: utf-8 -*-
"""Fix heights and market values for Haiti & Scotland players."""

import json

PATH = "prode_mundial/output/players.json"
with open(PATH, "r", encoding="utf-8") as f:
    pj = json.load(f)

# ── Height corrections ──
height_fixes = {
    "Haiti": {
        "Carlens Arcus": 1.80,
        "Ricardo Adé": 1.90,
        "Ruben Providence": 1.72,
    },
    "Scotland": {
        "Jack Hendry": 1.95,
        "John McGinn": 1.75,
        "Kenny Mclean": 1.83,
        "Che Adams": 1.75,
    },
}

# ── Market values (Transfermarkt) ──
market_values = {
    "Haiti": {
        "Johny Placide": 155000,
        "Alexandre Pierre": 250000,
        "Josu\u00e9 Duverger": 300000,
        "Carlens Arcus": 800000,
        "Keeto Thermoncy": 175000,
        "Ricardo Ad\u00e9": 600000,
        "Hannes Delcroix": 1500000,
        "Martin Exp\u00e9rience": 150000,
        "Markhus Lacroix": 75000,
        "Jean-K\u00e9vin Duverne": 1200000,
        "Wilguens Paugain": 200000,
        "Carl Saint\u00e9": 300000,
        "Jean-Ricner Bellegarde": 17600000,
        "Leverton Pierre": 100000,
        "Danley Jean Jacques": 400000,
        "Dominique Simon": 100000,
        "Woodensky Pierre": 75000,
        "Derrick Etienne Jr.": 2000000,
        "Duckens Nazon": 600000,
        "Louicius Deedson": 250000,
        "Ruben Providence": 1200000,
        "Lenny Joseph": 800000,
        "Wilson Isidor": 2500000,
        "Yassin Fortun\u00e9": 200000,
        "Frantzdy Pierrot": 300000,
        "Josu\u00e9 Casimir": 200000,
    },
    "Scotland": {
        "Angus Gunn": 3000000,
        "Liam Kelly": 500000,
        "Craig Gordon": 500000,
        "Aaron Hickey": 18000000,
        "Andrew Robertson": 35000000,
        "Grant Hanley": 2500000,
        "Kieran Tierney": 15000000,
        "Jack Hendry": 5000000,
        "John Souttar": 3000000,
        "Dominic Hyam": 2000000,
        "Nathan Patterson": 6000000,
        "Anthony Ralston": 2500000,
        "Scott McKenna": 6000000,
        "Scott McTominay": 38000000,
        "John McGinn": 20000000,
        "Tyler Fletcher": 800000,
        "Ryan Christie": 8000000,
        "Lewis Ferguson": 1500000,
        "Kenny Mclean": 2000000,
        "Lyndon Dykes": 8000000,
        "Che Adams": 12000000,
        "Ross Stewart": 3000000,
        "Ben Doak": 15000000,
        "George Hirst": 1500000,
        "Lawrence Shankland": 3000000,
        "Findlay Curtis": 200000,
    },
}

changed = 0
for team_name, fixes in height_fixes.items():
    team = pj.get(team_name, [])
    for player in team:
        name = player["name"]
        if name in fixes:
            old = player.get("height")
            new = fixes[name]
            player["height"] = new
            print(f"  {team_name}/{name}: height {old} -> {new}")
            changed += 1

for team_name, values in market_values.items():
    team = pj.get(team_name, [])
    for player in team:
        name = player["name"]
        if name in values:
            old = player.get("market_value")
            new = values[name]
            player["market_value"] = new
            print(f"  {team_name}/{name}: mv {old} -> {new}")
            changed += 1

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(pj, f, ensure_ascii=False, indent=2)

print(f"\n✅ {changed} fields updated in {PATH}")
