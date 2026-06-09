# -*- coding: utf-8 -*-
"""Generacion de analisis narrativo PRODE para cada partido."""

from prode_mundial.data import get_team, INJURED_OUT, PENALTY_TAKERS
from prode_mundial.friendlies_data import compute_friendly_form
from prode_mundial.top_scorer import get_team_weights

_CONF_LABEL = {
    "CONMEBOL": "sudamericano", "UEFA": "europeo", "CONCACAF": "norteamericano",
    "CAF": "africano", "AFC": "asiatico", "OFC": "oceanico",
}

def _get_star_player(team_name):
    weights = get_team_weights(team_name)
    if weights:
        return weights[0][0]
    return None

def _top_scorer_info(team_name):
    weights = get_team_weights(team_name)
    if not weights:
        return None, 0
    top = weights[0]
    return top[0], top[3]

def _penalty_taker(team_name):
    takers = PENALTY_TAKERS.get(team_name, [])
    return takers[0] if takers else None

def _injured_info(team_name):
    return INJURED_OUT.get(team_name, [])

def _form_description(form_streak):
    if form_streak >= 0.9:
        return "llega en un estado de forma impecable"
    if form_streak >= 0.7:
        return "llega con solidez y buenos resultados"
    if form_streak >= 0.5:
        return "llega con resultados irregulares pero aceptables"
    if form_streak >= 0.3:
        return "llega con dudas y resultados pobres"
    return "llega en su peor momento"

def _friendly_description(team_name):
    ff = compute_friendly_form(team_name)
    if ff >= 8:
        return "arrasó en los amistosos de preparacion"
    if ff >= 5:
        return "tuvo una buena preparacion en amistosos"
    if ff >= 2:
        return "cumplio en los amistosos sin brillar"
    if ff < 0:
        return "tuvo una preparacion preocupante en amistosos"
    return "disputo amistosos sin resultados destacados"

def _build_recommendation(match):
    conf = match.get("confidence", 0)
    prob_draw = match.get("probabilities", {}).get("draw", 0)
    team_a = match["team_a"]
    team_b = match["team_b"]
    probs = match.get("probabilities", {})
    a_win = probs.get("a_win", 0)
    b_win = probs.get("b_win", 0)
    a_data = get_team(team_a)
    b_data = get_team(team_b)
    rank_a = a_data.get("rank", 100) or 100
    rank_b = b_data.get("rank", 100) or 100
    rank_diff = rank_b - rank_a

    if prob_draw >= 32:
        return "EMPATE PROBABLE - Partido muy parejo, el empate paga bien"
    if conf >= 55:
        if a_win >= 55 and rank_diff >= 30:
            return "LOCAL SEGURO - Amplio favorito, resultado confiable"
        if a_win >= 55:
            return "FAVORITO CON CAUTELA - Ventaja solida pero no definitiva"
        if b_win >= 55 and rank_diff <= -30:
            return "VISITANTE SEGURO - Favorito solido como visitante"
        if b_win >= 55:
            return "FAVORITO CON CAUTELA"
    if conf >= 45:
        if a_win > b_win:
            return "LIGERO FAVORITO LOCAL - Partido parejo, ventaja minima"
        return "LIGERO FAVORITO VISITANTE - Partido parejo"
    if a_win > 35 and b_win > 35 and prob_draw > 25:
        return "PARTIDO ABIERTO - Cualquier resultado es posible"
        return "SORPRESA POSIBLE - El menos favorecido puede dar el golpe"

def _build_narrative(match):
    team_a = match["team_a"]
    team_b = match["team_b"]
    a_data = get_team(team_a)
    b_data = get_team(team_b)
    probs = match.get("probabilities", {})
    a_win = probs.get("a_win", 0)
    b_win = probs.get("b_win", 0)
    prob_draw = probs.get("draw", 0)
    conf = match.get("confidence", 0)
    factors = match.get("factors", {})
    xg_a = match.get("expected_goals_a", 0)
    xg_b = match.get("expected_goals_b", 0)

    parts = []

    # Team A section
    a_confed = _CONF_LABEL.get(a_data.get("confederation", ""), "internacional")
    a_form = a_data.get("form_streak", 0.5)
    a_rank = a_data.get("rank", 100) or 100
    a_form_text = _form_description(a_form)
    a_friendly = _friendly_description(team_a)
    a_star = _get_star_player(team_a)
    a_top_scorer, a_top_goals = _top_scorer_info(team_a)
    a_penalty = _penalty_taker(team_a)
    a_injured = _injured_info(team_a)
    a_wc = a_data.get("wc_history", "")

    parts.append(f"{team_a}, conjunto {a_confed} (ranking {a_rank}), {a_form_text}. {a_friendly.capitalize()}.")
    if a_star:
        star_line = f"Su carta bajo la manga es {a_star}"
        if a_penalty and a_penalty != a_star:
            star_line += f", con {a_penalty} como pateador de penales"
        parts.append(star_line + ".")
    if a_top_goals >= 10 and a_top_scorer:
        parts.append(f" {a_top_scorer} lleva {a_top_goals} goles en la temporada.")
    if a_injured:
        parts.append(f" Bajas importantes: {', '.join(a_injured)}.")
    if a_wc and a_wc.replace("_", " ").lower() not in ("none", "", "primera participacion"):
        parts.append(f" Su historial mundialista: {a_wc.replace('_', ' ')}.")

    parts.append("\n")

    # Team B section
    b_confed = _CONF_LABEL.get(b_data.get("confederation", ""), "internacional")
    b_form = b_data.get("form_streak", 0.5)
    b_rank = b_data.get("rank", 100) or 100
    b_form_text = _form_description(b_form)
    b_friendly = _friendly_description(team_b)
    b_star = _get_star_player(team_b)
    b_top_scorer, b_top_goals = _top_scorer_info(team_b)
    b_penalty = _penalty_taker(team_b)
    b_injured = _injured_info(team_b)
    b_wc = b_data.get("wc_history", "")

    parts.append(f"{team_b}, escuadra {b_confed} (ranking {b_rank}), {b_form_text}. {b_friendly.capitalize()}.")
    if b_star:
        star_line = f"Su carta de presentacion es {b_star}"
        if b_penalty and b_penalty != b_star:
            star_line += f", con {b_penalty} como pateador de penales"
        parts.append(star_line + ".")
    if b_top_goals >= 10 and b_top_scorer:
        parts.append(f" {b_top_scorer} acumula {b_top_goals} goles en el ano.")
    if b_injured:
        parts.append(f" Ausencias sensibles: {', '.join(b_injured)}.")
    if b_wc and b_wc.replace("_", " ").lower() not in ("none", "", "primera participacion"):
        parts.append(f" Su mejor actuacion historica: {b_wc.replace('_', ' ')}.")

    parts.append("\n")

    # Tactical analysis
    xg_total = xg_a + xg_b
    if xg_total >= 4:
        parts.append("Se espera un partido con varios goles")
    elif xg_total >= 2.5:
        parts.append("Se espera un partido de ritmo moderado")
    else:
        parts.append("Se prevé un partido táctico y de pocos goles")
    parts.append(f" (xG total: {xg_total:.2f}).")

    if factors:
        valid_factors = {k: v for k, v in factors.items() if v is not None and k not in ("stakes_a", "stakes_b")}
        if valid_factors:
            sorted_factors = sorted(valid_factors.items(), key=lambda x: abs(x[1]), reverse=True)
            top_factor_name, top_factor_val = sorted_factors[0]
            if abs(top_factor_val) > 1.5:
                factor_labels = {"strength": "calidad de plantilla",
                                 "player_stats": "rendimiento individual",
                                 "home": "factor localía",
                                 "experience": "experiencia internacional",
                                 "friendly_form": "forma en amistosos recientes",
                                 "market_value": "valor de mercado",
                                 "squad_depth": "profundidad del banquillo",
                                 "rest_days": "descanso entre partidos",
                                 "stakes": "presión del momento",
                                 "history": "historial mundialista",
                                 "morale": "moral del equipo",
                                 "trophy_pedigree": "palmarés de sus jugadores",
                                 "height_advantage": "ventaja aerea",
                                 "club_chemistry": "química entre compañeros"}
                label = factor_labels.get(top_factor_name, top_factor_name)
                if top_factor_val > 0:
                    parts.append(f" El factor {label} favorece claramente a {team_a}.")
                else:
                    parts.append(f" El factor {label} favorece claramente a {team_b}.")

    avg_gs_a = a_data.get("goals_scored_avg", 1.5) or 1.5
    avg_gc_a = a_data.get("goals_conceded_avg", 1.2) or 1.2
    avg_gs_b = b_data.get("goals_scored_avg", 1.5) or 1.5
    avg_gc_b = b_data.get("goals_conceded_avg", 1.2) or 1.2

    if avg_gs_a > avg_gc_b:
        parts.append(f" {team_a} tiene poderio ofensivo ({avg_gs_a:.1f} goles/partido)")
        parts.append(" y buscara imponer su juego ofensivo.")

    if avg_gs_b > avg_gs_a:
        parts.append(f" Por su parte, {team_b} cuenta con un ataque peligroso ({avg_gs_b:.1f} goles/partido).")
    elif avg_gs_b > avg_gc_a:
        parts.append(f" {team_b} tiene argumentos para lastimar ({avg_gs_b:.1f} goles/partido).")

    if avg_gc_a < 0.8:
        parts.append(f" {team_a} se destaca por su solidez defensiva ({avg_gc_a:.1f} goles recibidos/partido).")
    if avg_gc_b < 0.8:
        parts.append(f" {team_b} cuenta con una defensa solida ({avg_gc_b:.1f} goles recibidos/partido).")

    parts.append("\n")
    parts.append("--- VEREDICTO PRODE ---")
    if a_win >= 50:
        parts.append(f" Ganador esperado: {team_a} ({a_win:.0f}% de probabilidad)")
    elif b_win >= 50:
        parts.append(f" Ganador esperado: {team_b} ({b_win:.0f}% de probabilidad)")
    else:
        parts.append(f" Partido muy parejo: empate ({prob_draw:.0f}%) o definicion por detalles.")

    if prob_draw >= 28:
        parts.append(f" Riesgo de empate alto ({prob_draw:.0f}%). Cuidado al pronosticar.")
    elif prob_draw <= 20:
        parts.append(f" Empate poco probable ({prob_draw:.0f}%).")
    else:
        parts.append(f" Empate posible ({prob_draw:.0f}%).")
    parts.append(f" Confianza del modelo: {conf:.0f}%.")

    paragraphs = []
    buf = []
    for p in parts:
        if p == "\n":
            if buf:
                paragraphs.append(" ".join(s.strip() for s in buf if s.strip()))
                buf = []
        else:
            buf.append(p.strip())
    if buf:
        paragraphs.append(" ".join(s for s in buf if s))
    return "\n\n".join(paragraphs)

def generate_match_analysis(match):
    try:
        rec = _build_recommendation(match)
        narrative = _build_narrative(match)
        return rec + "\n\n" + narrative
    except Exception:
        return ""
