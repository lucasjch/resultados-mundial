# -*- coding: utf-8 -*-
"""Scraper individual de Wikipedia via API para enriquecer jugadores con caps, trofeos, altura."""

import json
import re
import time
import requests
import os
import sys

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Mundial2026Prode/1.0 (research)"}
CACHE_FILE = os.path.join(os.path.dirname(__file__), "output", "wiki_cache.json")
PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "output", "players.json")

REQUEST_DELAY = 1.0


def _wiki_request(params):
    """Ejecuta request a la API de Wikipedia."""
    params["format"] = "json"
    try:
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [ERROR] Wiki request failed: {e}")
        return None


def fetch_wikitext(page_title):
    """Obtiene wikitext de una pagina de Wikipedia."""
    data = _wiki_request({
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "redirects": 1,
    })
    if data and "parse" in data and "wikitext" in data["parse"]:
        return data["parse"]["wikitext"]["*"]
    return None


def search_page(player_name):
    """Search Wikipedia for a player, return best page title."""
    data = _wiki_request({
        "action": "query",
        "list": "search",
        "srsearch": player_name + " footballer",
        "srlimit": 5,
        "srprop": "",
    })
    if data and "query" in data and data["query"].get("search"):
        for result in data["query"]["search"]:
            title = result["title"]
            if "footballer" in title or "football" in title:
                return title
        return data["query"]["search"][0]["title"]
    return None


def _extract_num(text):
    """Extrae primer entero de texto manejando markup wiki."""
    text = re.sub(r'\[\[[^\]|]+\|', '', text)  # [[Page|56 -> 56
    text = re.sub(r'[^\d]', '', text.split('<!--')[0].split('{{')[0])  # strip non-digits
    return int(text) if text else 0


def parse_infobox(wikitext):
    """Parsea {{Infobox football biography}} extrayendo caps, altura, club."""
    stats = {}

    # Find full infobox (handle nested braces)
    start = wikitext.find('{{Infobox football biography')
    if start < 0:
        return stats
    depth = 1
    end = start + 2
    while depth > 0 and end < len(wikitext) - 1:
        end += 1
        if wikitext[end-1:end+1] == '{{':
            depth += 1
        elif wikitext[end-1:end+1] == '}}':
            depth -= 1
    ib = wikitext[start:end+1]

    # Current club
    m = re.search(r'\|\s*currentclub\s*=\s*(.*?)(?:\n|$)', ib)
    if m:
        club = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', m.group(1))  # [[A|B]] -> B
        club = re.sub(r'\[\[|\]\]', '', club).strip()
        stats["current_club"] = club

    # Collect numbered entries
    years_nums = sorted(set(int(x) for x in re.findall(r'\|?\s*years(\d+)\s*=', ib)))
    nat_years_nums = sorted(set(int(x) for x in re.findall(r'\|?\s*nationalyears(\d+)\s*=', ib)))

    # Caps/goals by entry number
    caps = {}
    goals = {}
    for k, v in re.findall(r'\|\s*caps(\d+)\s*=\s*([^|\n]*)', ib):
        caps[int(k)] = _extract_num(v)
    for k, v in re.findall(r'\|\s*goals(\d+)\s*=\s*([^|\n]*)', ib):
        goals[int(k)] = _extract_num(v)

    nat_caps = {}
    nat_goals = {}
    for k, v in re.findall(r'\|?\s*nationalcaps(\d+)\s*=\s*([^|\n]*)', ib):
        nat_caps[int(k)] = _extract_num(v)
    for k, v in re.findall(r'\|?\s*nationalgoals(\d+)\s*=\s*([^|\n]*)', ib):
        nat_goals[int(k)] = _extract_num(v)

    # Club stats: highest numbered years entry = current club
    if years_nums:
        latest = max(years_nums)
        stats["club_apps"] = caps.get(latest, 0)
        stats["club_goals"] = goals.get(latest, 0)

        m_club = re.search(r'\|?\s*clubs' + str(latest) + r'\s*=\s*(.*?)(?:\n|$)', ib)
        if m_club:
            cn = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', m_club.group(1))
            cn = re.sub(r'\[\[|\]\]', '', cn).strip()
            stats["club_name"] = cn

    # Senior national team: highest numbered entry NOT U## or youth
    senior_num = None
    for n in sorted(nat_years_nums, reverse=True):
        m_team = re.search(r'\|?\s*nationalteam' + str(n) + r'\s*=\s*(.*?)(?:\n|$)', ib)
        if m_team:
            team = m_team.group(1)
            if not re.search(r'\bU\d+\b|youth|amateur|olympic|U23|U20|U19|U17|U16|U15', team):
                senior_num = n
                break

    if senior_num is None and nat_years_nums:
        senior_num = max(nat_years_nums)

    if senior_num:
        stats["intl_caps"] = nat_caps.get(senior_num, 0)
        stats["intl_goals"] = nat_goals.get(senior_num, 0)

    # Height
    m_h = re.search(r'\|\s*height\s*=\s*(.*?)(?:\n|$)', ib)
    if m_h:
        h_text = m_h.group(1).strip()
        m_m = re.search(r'(\d+\.?\d*)\s*m', h_text)
        if m_m:
            stats["height"] = float(m_m.group(1))

    return stats


def parse_honours(wikitext):
    """Parsea seccion de honores/trofeos del wikitext."""
    honours = []

    match = re.search(r'==\s*Honours?\s*==\s*\n(.*?)(?:\n==\s|\Z)', wikitext, re.DOTALL)
    if not match:
        return honours

    text = match.group(1)
    category = "General"

    for line in text.split('\n'):
        line = line.strip()
        if line.startswith("'''") and "'''" in line[3:]:
            cat = line.strip("'")
            if cat:
                category = cat
        elif line.startswith('*') and not line.startswith('**'):
            item = line.lstrip('* ').strip()
            item = re.sub(r'\[\[|\]\]|<[^>]+?>', '', item)
            item = re.sub(r'\{\{[^}]+\}\}', '', item)
            item = item.strip()
            if item and len(item) > 3:
                honours.append({"cat": category, "title": item})

    return honours


def scrape_player(player_name):
    """Scrapea estadisticas de un jugador desde Wikipedia."""
    result = {"name": player_name}

    wikitext = fetch_wikitext(player_name)
    if not wikitext:
        # Try searching
        found = search_page(player_name)
        if found:
            wikitext = fetch_wikitext(found)
            result["wiki_page"] = found

    if not wikitext:
        return None

    if "{{Infobox football biography" not in wikitext:
        return None

    stats = parse_infobox(wikitext)
    if stats:
        result.update(stats)

    honours = parse_honours(wikitext)
    if honours:
        result["honours"] = honours
        result["trophy_count"] = len(honours)

    return result


def scrape_all_players(force=False):
    """Scrapea todos los jugadores de players.json agregando datos de Wikipedia."""
    if not os.path.exists(PLAYERS_FILE):
        print("ERROR: players.json not found. Run scraper.py first.")
        return

    with open(PLAYERS_FILE, encoding="utf-8") as f:
        all_players = json.load(f)

    # Load cache
    cache = {}
    if os.path.exists(CACHE_FILE) and not force:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)

    total = sum(len(v) for v in all_players.values())
    done = 0
    found = 0
    enriched = {}
    SAVE_INTERVAL = 50

    for team, squad in all_players.items():
        enriched[team] = []
        for player in squad:
            pname = player["name"]
            done += 1

            if pname in cache:
                wiki_data = cache[pname]
            else:
                sys.stdout.write(f"\r  [{done}/{total}] {pname:40s}")
                sys.stdout.flush()
                wiki_data = scrape_player(pname)
                cache[pname] = wiki_data if wiki_data else {}
                time.sleep(REQUEST_DELAY)

            if wiki_data:
                found += 1
                player["intl_caps"] = wiki_data.get("intl_caps", 0)
                player["intl_goals"] = wiki_data.get("intl_goals", 0)
                player["club_apps"] = wiki_data.get("club_apps", 0)
                player["club_goals"] = wiki_data.get("club_goals", 0)
                player["current_club"] = wiki_data.get("current_club", "")
                player["club_name"] = wiki_data.get("club_name", "")
                player["trophy_count"] = wiki_data.get("trophy_count", 0)
                if "height" in wiki_data and not player.get("height"):
                    player["height"] = wiki_data["height"]

            enriched[team].append(player)

            # Sanity check caps and goals
            if player.get("intl_caps", 0) > 300:
                sys.stdout.write(f"\n  [CAPS WARN] {pname:40s} intl_caps={player['intl_caps']}\n")
                sys.stdout.flush()
            if player.get("intl_goals", 0) > 200:
                sys.stdout.write(f"\n  [GOALS WARN] {pname:40s} intl_goals={player['intl_goals']}\n")
                sys.stdout.flush()

            # Save incrementally every SAVE_INTERVAL players
            if done % SAVE_INTERVAL == 0:
                os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(enriched, f, ensure_ascii=False, indent=2)
                sys.stdout.write(f"\n  [CHECKPOINT] {done}/{total} guardado\n")
                sys.stdout.flush()

    print(f"\n\nResultados: {found}/{total} jugadores encontrados en Wikipedia")

    # Save cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # Save enriched players
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"Cache guardado: {CACHE_FILE}")
    print(f"players.json actualizado: {PLAYERS_FILE}")
    return enriched


if __name__ == "__main__":
    scrape_all_players(force="--force" in sys.argv)
