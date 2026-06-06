# -*- coding: utf-8 -*-
# Scraper de estadisticas individuales desde Transfermarkt API
# Objetivo: goals, assists, minutes de la temporada 2025-26

import json
import os
import re
import sys
import time
from difflib import SequenceMatcher
import requests

TM_API = "https://tmapi-alpha.transfermarkt.technology"
TM_WEB = "https://www.transfermarkt.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "output", "players.json")
CACHE_FILE = os.path.join(os.path.dirname(__file__), "output", "tm_stats_cache.json")
REQUEST_DELAY = 0.5
TARGET_SEASON = 2025

def _get(url, timeout=20):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

TM_TEAM_OVERRIDES = {
    "USA": "United States",
    "Turkey": "Turkiye",
    "DR Congo": "Democratic Republic of the Congo",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "Curacao": "Curaçao",
    "Ivory Coast": "Côte d'Ivoire",
    "Czechia": "Czech Republic",
    "Cape Verde": "Cabo Verde",
    "South Korea": "Korea Republic",
}

def _get_team_id_map():
    """Get mapping of our team name -> TM team ID for all World Cup teams."""
    data = _get(f"{TM_WEB}/quickselect/teams/FIWC")
    if not data:
        print("ERROR: Could not fetch team list from Transfermarkt")
        return {}
    tm_names = {t["name"]: t["id"] for t in data}
    result = {}
    for our_name, tm_name in TM_TEAM_OVERRIDES.items():
        if tm_name in tm_names:
            result[our_name] = tm_names[tm_name]
    for t in data:
        result[t["name"]] = t["id"]
    return result

def _normalize(name):
    """Normalize name for matching."""
    n = name.lower().strip()
    n = re.sub(r'[áàâãä]', 'a', n)
    n = re.sub(r'[éèêë]', 'e', n)
    n = re.sub(r'[íìîï]', 'i', n)
    n = re.sub(r'[óòôõö]', 'o', n)
    n = re.sub(r'[úùûü]', 'u', n)
    n = re.sub(r'[ñ]', 'n', n)
    n = re.sub(r'[ç]', 'c', n)
    n = re.sub(r'[^a-z0-9]', '', n)
    return n

def _norm_strict(name):
    """Normalize to only letters for fuzzy matching."""
    return re.sub(r'[^a-z]', '', _normalize(name))

SUFFIXES = ["segundo", "primero", "tercero", "mediapunta", "delantero",
            "defensa", "centrocampista", "portero", "lateral", "volante",
            "extremo"]

def _clean_name(name):
    """Remove position/trailing junk from player names."""
    n = name.lower().strip()
    n = re.sub(r'\b(' + '|'.join(SUFFIXES) + r')\b', '', n).strip()
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def _fuzzy_find(name, tm_list, threshold=0.75):
    """Fuzzy match a name against a list of (normalized, id) pairs."""
    n = _norm_strict(name)
    best = None
    best_score = 0
    second_score = 0
    for tm_norm, tm_id, tm_orig in tm_list:
        score = SequenceMatcher(None, n, tm_norm).ratio()
        if score > best_score:
            second_score = best_score
            best_score = score
            best = tm_id
        elif score > second_score:
            second_score = score
    if best_score >= threshold and (best_score - second_score) >= 0.1:
        return best
    return None

def _get_players_for_team(team_id):
    """Get list of players for a team."""
    data = _get(f"{TM_WEB}/quickselect/players/{team_id}")
    if not data:
        return []
    return data

def _build_player_map(tm_players):
    """Build a mapping of normalized name -> TM player ID, plus fuzzy list."""
    mapping = {}
    fuzzy_list = []
    for p in tm_players:
        norm = _normalize(p["name"])
        if norm:
            mapping[norm] = p["id"]
            fuzzy_list.append((_norm_strict(p["name"]), p["id"], p["name"]))
    return mapping, fuzzy_list

def _extract_season_stats(perf_data):
    """Extract aggregate stats for the target season from performance data."""
    total_goals = 0
    total_assists = 0
    total_minutes = 0
    games_played = 0

    for g in perf_data:
        info = g.get("gameInformation", {})
        if info.get("seasonId") != TARGET_SEASON:
            continue

        stats = g.get("statistics", {})
        goal_stats = stats.get("goalStatistics", {})
        time_stats = stats.get("playingTimeStatistics", {})
        general = stats.get("generalStatistics", {})

        mins = time_stats.get("playedMinutes") or 0
        if mins == 0:
            continue

        games_played += 1
        total_minutes += mins
        total_goals += goal_stats.get("goalsScoredTotal") or 0
        total_assists += goal_stats.get("assists") or 0

    return {
        "games_2025": games_played,
        "minutes_2025": total_minutes,
        "goals_2025": total_goals,
        "assists_2025": total_assists,
    }

def enrich_with_stats(force=False):
    """Enrich players.json with goals/assists from Transfermarkt."""
    if not os.path.exists(PLAYERS_FILE):
        print(f"ERROR: {PLAYERS_FILE} not found. Run scraper.py first.")
        return

    with open(PLAYERS_FILE, encoding="utf-8") as f:
        all_players = json.load(f)

    # Load cache
    cache = {}
    if os.path.exists(CACHE_FILE) and not force:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)

    # Get team ID mapping
    tm_team_ids = _get_team_id_map()
    print(f"Found {len(tm_team_ids)} teams in Transfermarkt")

    total_players = sum(len(v) for v in all_players.values())
    processed = 0
    found = 0

    for team_name, squad in all_players.items():
        # Find TM team ID
        tm_id = tm_team_ids.get(team_name)
        if not tm_id:
            print(f"\n  {team_name}: No TM team ID found, skipping")
            enriched_count = 0
            for player in squad:
                processed += 1
                if "goals_2025" not in player:
                    player["goals_2025"] = 0
                    player["assists_2025"] = 0
                    player["minutes_2025"] = 0
                    player["games_2025"] = 0
            continue

        # Get TM players for this team
        tm_players = _get_players_for_team(tm_id)
        if not tm_players:
            print(f"\n  {team_name}: Could not fetch TM players")
            continue

        player_map, fuzzy_list = _build_player_map(tm_players)
        enriched_count = 0

        for player in squad:
            pname = player["name"]
            processed += 1

            # Check if already enriched
            if "goals_2025" in player and not force:
                continue

            # Try to match player name - exact, fuzzy, cleaned, then fuzzy cleaned
            norm = _normalize(pname)
            tm_player_id = player_map.get(norm)

            if not tm_player_id:
                tm_player_id = _fuzzy_find(pname, fuzzy_list)

            if not tm_player_id:
                cleaned = _clean_name(pname)
                if cleaned != pname.lower().strip():
                    tm_player_id = player_map.get(_normalize(cleaned))
                    if not tm_player_id:
                        tm_player_id = _fuzzy_find(cleaned, fuzzy_list)

            if not tm_player_id:
                player["goals_2025"] = 0
                player["assists_2025"] = 0
                player["minutes_2025"] = 0
                player["games_2025"] = 0
                continue

            # Check cache
            cache_key = str(tm_player_id)
            if cache_key in cache:
                stats = cache[cache_key]
            else:
                progress = f"\r  [{processed}/{total_players}] {pname:40s}"
                try:
                    sys.stdout.write(progress)
                except UnicodeEncodeError:
                    sys.stdout.write(progress.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
                sys.stdout.flush()

                perf = _get(f"{TM_API}/player/{tm_player_id}/performance-game")
                if not perf or not perf.get("data", {}).get("performance"):
                    player["goals_2025"] = 0
                    player["assists_2025"] = 0
                    player["minutes_2025"] = 0
                    player["games_2025"] = 0
                    continue

                stats = _extract_season_stats(perf["data"]["performance"])
                cache[cache_key] = stats
                time.sleep(REQUEST_DELAY)

            player.update(stats)
            enriched_count += 1
            found += 1

        print(f"\n  {team_name}: {enriched_count}/{len(squad)} players with stats")

        # Save checkpoint after each team
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_players, f, ensure_ascii=False, indent=2)

    print(f"\n\nStats encontrados: {found}/{total_players} jugadores")

    # Final save
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print(f"Cache guardado: {CACHE_FILE}")
    print(f"players.json actualizado: {PLAYERS_FILE}")
    return all_players


if __name__ == "__main__":
    force = "--force" in sys.argv
    enrich_with_stats(force=force)
