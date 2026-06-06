# -*- coding: utf-8 -*-
# Scraper de plantillas completas: Promiedos (28) + Transfermarkt (20)

import json
import os
import re
import urllib.request
import time

TEAM_SOURCES = {
    "Mexico": ("promiedos", "mexico", "fbag"),
    "Czechia": ("promiedos", "czech-republic", "faea"),
    "Canada": ("promiedos", "canada", "cdii"),
    "Switzerland": ("promiedos", "switzerland", "fadc"),
    "Bosnia & Herzegovina": ("promiedos", "bosnia-&-herzegovina", "faei"),
    "Brazil": ("promiedos", "brazil", "cdhj"),
    "Scotland": ("promiedos", "scotland", "fagj"),
    "Haiti": ("promiedos", "haiti", "fecc"),
    "USA": ("promiedos", "usa", "cdij"),
    "Paraguay": ("promiedos", "paraguay", "faha"),
    "Turkey": ("promiedos", "turkiye", "faeh"),
    "Germany": ("promiedos", "germany", "cdhc"),
    "Ecuador": ("promiedos", "ecuador", "fahf"),
    "Curacao": ("promiedos", "curacao", "cedjh"),
    "Netherlands": ("promiedos", "netherlands", "cdhh"),
    "Sweden": ("promiedos", "sweden", "cdhb"),
    "Belgium": ("promiedos", "belgium", "cdhd"),
    "Spain": ("promiedos", "spain", "fafa"),
    "Uruguay": ("promiedos", "uruguay", "fahd"),
    "France": ("promiedos", "france", "fagb"),
    "Norway": ("promiedos", "norway", "cdhg"),
    "Argentina": ("promiedos", "argentina", "cdhi"),
    "Austria": ("promiedos", "austria", "fafj"),
    "Portugal": ("promiedos", "portugal", "faci"),
    "Colombia": ("promiedos", "colombia", "fahb"),
    "England": ("promiedos", "england", "fafe"),
    "Croatia": ("promiedos", "croatia", "faff"),
    "Panama": ("promiedos", "panama", "febe"),
    "South Korea": ("transfermarkt", "sudkorea", 3589),
    "South Africa": ("transfermarkt", "sudafrika", 3806),
    "Qatar": ("transfermarkt", "katar", 14162),
    "Morocco": ("transfermarkt", "marokko", 3575),
    "Australia": ("transfermarkt", "australien", 3433),
    "Ivory Coast": ("transfermarkt", "elfenbeinkuste", 3591),
    "Japan": ("transfermarkt", "japan", 3435),
    "Tunisia": ("transfermarkt", "tunesien", 3670),
    "Egypt": ("transfermarkt", "agypten", 3672),
    "Iran": ("transfermarkt", "iran", 3582),
    "Senegal": ("transfermarkt", "senegal", 3499),
    "Algeria": ("transfermarkt", "algerien", 3614),
    "Jordan": ("transfermarkt", "jordanien", 15737),
    "DR Congo": ("transfermarkt", "demokratische-republik-kongo", 3854),
    "Uzbekistan": ("transfermarkt", "usbekistan", 3563),
    "Ghana": ("transfermarkt", "ghana", 3441),
    "New Zealand": ("transfermarkt", "nueva-zelanda", 9171),
    "Saudi Arabia": ("transfermarkt", "saudi-arabien", 3807),
    "Cape Verde": ("transfermarkt", "kap-verde", 4311),
    "Iraq": ("transfermarkt", "irak", 3560),
}

POSITION_STARTERS = sorted([
    "Arquero", "Portero",
    "Defensa Central", "Defensa Lateral Izquierdo", "Defensa Lateral Derecho", "Defensa",
    "Lateral Izquierdo", "Lateral Derecho", "Lateral",
    "Mediocampista Central", "Mediocampista Ofensivo", "Mediocampista",
    "Mediocentro Ofensivo", "Mediocentro Central", "Mediocentro",
    "Centrocampista defensivo", "Centrocampista",
    "Pivote", "Volante Derecho", "Volante Izquierdo", "Volante",
    "Delantero Centro", "Delantero Derecho", "Delantero Izquierdo", "Delantero",
    "Centro Delantero", "Extremo Izquierdo", "Extremo Derecho", "Extremo",
    "Interior Izquierdo", "Interior Derecho", "Interior",
    "Medio Ofensivo",
], key=len, reverse=True)


def fetch_url(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        encoding = resp.headers.get_content_charset()
        if encoding:
            return raw.decode(encoding, errors="replace")
        # Try UTF-8 first, then latin-1
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")


def parse_market_value(val_str):
    if not val_str:
        return None
    val_str = val_str.replace(',', '.').replace(' ', '').replace('\u20ac', '').strip()
    val_lower = val_str.lower()
    if 'mio' in val_lower or 'mill' in val_lower:
        m = re.search(r'([\d.]+)', val_str)
        if m:
            return float(m.group(1))
    elif 'mil' in val_lower or 'tsd' in val_lower:
        m = re.search(r'([\d.]+)', val_str)
        if m:
            return float(m.group(1)) / 1000.0
    else:
        m = re.search(r'^([\d.]+)$', val_str)
        if m:
            return float(m.group(1))
    return None


def parse_promiedos(html):
    players = []
    pos_endings = [
        "Lateral Izquierdo", "Lateral Derecho",
        "Central", "Ofensivo",
        "Centro", "Derecho", "Izquierdo",
        "defensivo",
    ]
    base_positions = {
        "Arquero": "Arquero", "Portero": "Arquero",
        "Defensa": "Defensa", "Lateral": "Defensa",
        "Mediocampista": "Mediocampista", "Mediocentro": "Mediocampista",
        "Centrocampista": "Mediocampista", "Volante": "Mediocampista",
        "Pivote": "Mediocampista", "Interior": "Mediocampista",
        "Delantero": "Delantero", "Centro Delantero": "Delantero",
        "Extremo": "Delantero",
    }

    # Extract all rows
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

    for row in rows:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)

        # Skip group headers (colspan=4 means single td row)
        if len(tds) != 4:
            continue

        name_td = re.sub(r'<[^>]+>', ' ', tds[0]).strip()
        name_td = re.sub(r'\s+', ' ', name_td).strip()

        age_str = re.sub(r'<[^>]+>', ' ', tds[1]).strip()
        dob_str = re.sub(r'<[^>]+>', ' ', tds[2]).strip()
        height_str = re.sub(r'<[^>]+>', ' ', tds[3]).strip()

        # Skip coaches (start with DT)
        if name_td.startswith('DT '):
            continue

        # Parse jersey + name + position
        m = re.match(r'(\d{1,2})\s+(.+)', name_td)
        if not m:
            continue

        jersey = int(m.group(1))
        rest = m.group(2).strip()

        # Skip if jersey > 26 (WC squad size limit)
        if jersey > 26:
            continue

        # Extract position from rest
        name = rest
        position = ""

        # Try to find position keyword (all base positions)
        pos_patterns = list(base_positions.keys()) + [
            "Defensa Central", "Defensa Lateral Izquierdo", "Defensa Lateral Derecho",
            "Mediocampista Central", "Mediocampista Ofensivo",
            "Mediocentro Ofensivo", "Mediocentro Central",
            "Centrocampista defensivo",
            "Delantero Centro", "Delantero Derecho", "Delantero Izquierdo",
            "Lateral Izquierdo", "Lateral Derecho",
            "Extremo Izquierdo", "Extremo Derecho",
            "Interior Izquierdo", "Interior Derecho",
            "Volante Derecho", "Volante Izquierdo",
            "Medio Ofensivo",
            "Pivote",
        ]
        pos_patterns = sorted(set(pos_patterns), key=len, reverse=True)

        for pp in pos_patterns:
            idx = rest.find(pp)
            if idx >= 0:
                name = rest[:idx].strip()
                position = base_positions.get(pp, pp)
                break

        # Parse age
        try:
            age = int(age_str)
        except ValueError:
            continue

        players.append({
            "name": name,
            "position": position,
            "jersey": jersey,
            "age": age,
            "dob": dob_str,
            "height": float(height_str) if height_str else None,
            "market_value": None,
        })

    return players


def clean_text(html):
    import html as html_module
    text = re.sub(r'<[^>]+>', ' ', html)
    text = html_module.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_items_table(html):
    """Extract the items table HTML, handling nested <table> tags."""
    table_open = re.search(r'<table[^>]*class="[^"]*items[^"]*"[^>]*>', html, re.DOTALL)
    if not table_open:
        return None

    depth = 1
    i = table_open.end()
    while i < len(html) and depth > 0:
        next_open = html.find('<table', i)
        next_close = html.find('</table>', i)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            close_gt = html.find('>', next_open)
            if close_gt == -1:
                break
            i = close_gt + 1
        else:
            depth -= 1
            i = next_close + 8

    if depth != 0:
        return None
    return html[table_open.start():i]


def parse_transfermarkt(html):
    players = []

    table_html = extract_items_table(html)
    if not table_html:
        return players

    text = clean_text(table_html)

    pos_keywords_list = [
        'Portero', 'Arquero',
        'Defensa central', 'Defensa lateral', 'Lateral izquierdo', 'Lateral derecho',
        'Mediocentro ofensivo', 'Mediocentro defensivo', 'Mediocentro',
        'Mediocampista central', 'Mediocampista ofensivo', 'Mediocampista defensivo',
        'Centrocampista defensivo', 'Centrocampista',
        'Volante ofensivo', 'Volante defensivo', 'Volante',
        'Interior izquierdo', 'Interior derecho',
        'Pivote',
        'Delantero centro', 'Delantero',
        'Extremo izquierdo', 'Extremo derecho', 'Extremo',
        'Centro delantero',
    ]
    pos_keywords = sorted(set(p.lower() for p in pos_keywords_list), key=len, reverse=True)

    # Find player entries: jersey + name/position + DOB(age) + value
    for m in re.finditer(
        r'(\d{1,2})\s+'
        r'(.+?)\s+'
        r'(\d{2}/\d{2}/\d{4})\s*\((\d+)\)\s*'
        r'([\d.,]+\s*(?:mill?\.?|Mio|mil|tsd\.)\s*€)',
        text, re.DOTALL
    ):
        jersey = int(m.group(1))
        name_pos = m.group(2).strip()
        dob = m.group(3)
        age = int(m.group(4))
        value_str = m.group(5)
        market_value = parse_market_value(value_str)

        if jersey > 26 or age > 45:
            continue

        name = name_pos
        position = ""
        for pk in pos_keywords:
            idx2 = name_pos.lower().find(pk)
            if idx2 >= 0:
                name = name_pos[:idx2].strip()
                position = name_pos[idx2:].strip()
                position = position.title()
                break

        lower_name = name.lower()
        if 'dt ' in lower_name or 'entrenador' in lower_name or 'asistente' in lower_name:
            continue

        players.append({
            "name": name,
            "position": position,
            "jersey": jersey,
            "age": age,
            "dob": dob,
            "height": None,
            "market_value": market_value,
        })

    return players


def scrape_all():
    results = {}

    for team_name, (source, slug, ident) in TEAM_SOURCES.items():
        print(f"Scraping {team_name}...", end=" ")
        try:
            if source == "promiedos":
                url = f"https://www.promiedos.com.ar/team/{slug}/{ident}"
                html = fetch_url(url)
                players = parse_promiedos(html)
            else:
                url = f"https://www.transfermarkt.com.ar/{slug}/startseite/verein/{ident}"
                html = fetch_url(url)
                players = parse_transfermarkt(html)

            print(f"{len(players)} jugadores")
            results[team_name] = players
        except Exception as e:
            print(f"ERROR: {e}")
            results[team_name] = []

        time.sleep(0.5)

    total = sum(len(v) for v in results.values())
    print(f"\nTotal: {total} jugadores de {len(results)} equipos")

    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "players.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {out_path}")

    return results


if __name__ == "__main__":
    scrape_all()
