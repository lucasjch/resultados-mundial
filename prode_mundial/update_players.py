import json

import os
base = os.path.dirname(os.path.abspath(__file__))
pj = os.path.normpath(os.path.join(base, "output", "players.json"))
with open(pj, "r", encoding="utf-8") as f:
    players = json.load(f)

# === BRAZIL: market_value = null → Sofascore value ===
brazil_updates = {
    "Alisson": 18.7,
    "Roger Ibanez": 16.5,
    "Marquinhos": 29,
    "Gabriel Magalhaes": 70,
    "Douglas Santos": 7,
    "Casemiro": 7.3,
    "Bruno Guimarães": 77,
    "Lucas Paquetá": 36,
    "Raphinha": 72,
    "Vinicius": 156,
    "Igor Thiago": 52,
    "Danilo": None,  # two Danilos, handle by position/jersey
}
for p in players["Brazil"]:
    if p["name"] in brazil_updates and brazil_updates[p["name"]] is not None:
        p["market_value"] = brazil_updates[p["name"]]
    # Danilo #18 CM (jersey 18, Mediocampista Central)
    if p["name"] == "Danilo" and p["jersey"] == 18 and p["position"] == "Mediocampista Central":
        p["market_value"] = 25

# === MOROCCO: Issa Diop height null → 1.94 ===
for p in players["Morocco"]:
    if p["name"] == "Issa Diop":
        p["height"] = 1.94

# === SWITZERLAND: all market_value null → Sofascore value ===
swiss_updates = {
    "Gregor Kobel": 41,
    "Yvon Mvogo": 3.1,
    "Marvin Keller": 6.8,
    "Miro Muheim": 5.3,
    "Silvan Widmer": 0.73,
    "Nico Elvedi": 7.3,
    "Manuel Akanji": 15.5,
    "Ricardo Rodriguez": 1.6,
    "Eray Cümart": 2.7,
    "Aurèle Amenda": 8.2,
    "Luca Jaquez": 10.7,
    "Denis Zakaria": 26,
    "Remo Freuler": 3.1,
    "Johan Manzambi": 54,
    "Granit Xhaka": 10.6,
    "Ardon Jashari": 24,
    "Djibril Sow": 7.1,
    "Christian Fassnacht": 2.1,
    "Michel Aebischer": 4.2,
    "Fabian Rieder": 11.1,
    "Breel Embolo": 13.6,
    "Dan Ndoye": 34,
    "Ruben Vargas": 11.1,
    "Noah Okafor": 19.8,
    "Zeki Amdouni": 9.7,
}
for p in players["Switzerland"]:
    if p["name"] in swiss_updates and swiss_updates[p["name"]] is not None:
        p["market_value"] = swiss_updates[p["name"]]

if "Cedric Itten" in swiss_updates:
    pass  # already in dict
for p in players["Switzerland"]:
    if p["name"] == "Cedric Itten":
        p["market_value"] = 1.6

# === QATAR: height null → Sofascore value (only if currently null or missing) ===
qatar_height_updates = {
    "Boualem Khoukhi": 1.83,
    "Pedro Miguel": 1.88,
    "Homam Al-Amin": 1.86,
    "Edmílson Junior": 1.80,
    "Ahmed Fathi": 1.66,
    "Hasan Al-Haydos": 1.74,
}
for p in players["Qatar"]:
    if p["name"] in qatar_height_updates:
        current = p.get("height")
        if current is None:
            p["height"] = qatar_height_updates[p["name"]]

with open(pj, "w", encoding="utf-8") as f:
    json.dump(players, f, indent=2, ensure_ascii=False)

print("✅ players.json updated")
updated_brazil = sum(1 for p in players["Brazil"] if p.get("market_value") is not None)
updated_swiss = sum(1 for p in players["Switzerland"] if p.get("market_value") is not None)
qatar_heights = sum(1 for p in players["Qatar"] if p.get("height") is not None)
print(f"  Brazil: {updated_brazil}/26 with market_value")
print(f"  Switzerland: {updated_swiss}/26 with market_value")
print(f"  Qatar: {qatar_heights}/26 with height")
print(f"  Morocco: Issa Diop height={players['Morocco'][4]['height']}")
