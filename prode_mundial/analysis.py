# -*- coding: utf-8 -*-
"""Generacion de analisis narrativo PRODE para cada partido."""

from prode_mundial.data import get_team, INJURED_OUT, PENALTY_TAKERS, team_name_es
from prode_mundial.friendlies_data import compute_friendly_form
from prode_mundial.top_scorer import get_team_weights

_CONF_LABEL = {
    "CONMEBOL": "sudamericano", "UEFA": "europeo", "CONCACAF": "norteamericano",
    "CAF": "africano", "AFC": "asiatico", "OFC": "oceanico",
}

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

_INTRO_POOL = [
    "conjunto {confed} (ranking {rank}), {form_text}",
    "escuadra {confed} (ranking {rank}), {form_text}",
    "planteel {confed} (ranking {rank}), {form_text}",
]

_FORM_GOOD = [
    "esta en un estado de forma impecable",
    "llega en un gran momento",
    "vive un presente dulce",
    "atraviesa un excepcional momento deportivo",
]

_FORM_OK = [
    "tiene un rendimiento irregular",
    "arrastra resultados mixtos",
    "alterna buenas y malas actuaciones",
]

_FORM_BAD = [
    "esta en un momento preocupante",
    "arrastra resultados negativos",
    "no encuentra regularidad",
]

_FRIENDLY_GOOD = [
    "arraso en los amistosos de preparacion",
    "demostro superioridad en los amistosos",
    "tuvo una preparacion impecable",
    "dejo sensaciones muy positivas en los amistosos",
]

_FRIENDLY_OK = [
    "tuvo una preparacion irregular",
    "mezclo altibajos en los amistosos",
    "cumplio en los amistosos sin brillar",
]

_FRIENDLY_BAD = [
    "preocupo en los amistosos",
    "no logro consolidarse en la preparacion",
    "dejo dudas en los amistosos previos",
]

_BADGE_POOL = [
    "LOCAL INGOBERNABLE", "APUESTA SEGURA", "FAVORITO SIN DISCUSION",
    "VISITANTE ARROLLADOR", "LIGERO FAVORITO", "MONEDA AL AIRE",
    "PARTIDO ABIERTO", "CHOQUE DE TITANES", "CLASICO CONTINENTAL",
    "EMPATE PROBABLE", "PARTIDO TRAMPA", "DUELO DE NECESIDADES",
    "ULTIMA OPORTUNIDAD", "SORPRESA EN MARCHA", "PARTIDO DISPUTADO",
    "Favorito con Cautela", "DEFINICION APRETADA", "DUELO DE ESTILOS",
]

_DEF_GOOD = [
    "Su defensa es un fortin",
    "Su retaguardia es solida",
    "Su linea defensiva es dificil de vulnerar",
]

_DEF_OK = [
    "Su defensa es cumplidora",
    "Su linea de fondo cumple sin sobresaltos",
    "Ofrece seguridad defensiva moderada",
]

_DEF_BAD = [
    "Su defensa es vulnerable",
    "Ha mostrado fragilidades defensivas",
    "Su linea de fondo preocupa",
]

_MID_GOOD = [
    "Su mediocampo es creativo y dinamico",
    "Domina la zona de gestacion",
    "Su mediocampo marca el ritmo del partido",
    "Tiene una medular de primer nivel",
]

_MID_OK = [
    "Su mediocampo es trabajador",
    "Tiene un mediocampo de ida y vuelta",
    "Su zona de armado cumple",
]

_MID_BAD = [
    "Su mediocampo carece de creatividad",
    "Le cuesta generar juego desde la medular",
    "Su mediocampo es superable",
]

_FWD_GOOD = [
    "Su ataque es letal",
    "Tiene un poderio ofensivo arrollador",
    "Su delantera es de primer nivel mundial",
    "Posee una maquina de hacer goles",
]

_FWD_OK = [
    "Su ataque es peligroso",
    "Tiene argumentos ofensivos",
    "Su delantera puede lastimar",
]

_FWD_BAD = [
    "Su ataque carece de contundencia",
    "Le cuesta hacer goles",
    "Su delantera no inspira temor",
]

_VERDICT_A = [
    "Ganador esperado: {team} ({pct:.0f}% de probabilidad)",
    "El modelo favorece claramente a {team} ({pct:.0f}%)",
    "Todo indica que {team} se quedara con el triunfo ({pct:.0f}%)",
]

_VERDICT_B = [
    "Empate poco probable ({pct:.0f}%)",
    "Riesgo de empate bajo ({pct:.0f}%)",
    "La igualdad es un resultado remoto ({pct:.0f}%)",
]

_VERDICT_B_HIGH = [
    "Cuidado con la igualdad ({pct:.0f}%)",
    "El empate es un resultado probable ({pct:.0f}%)",
    "Hay riesgo de empate ({pct:.0f}%)",
]

_VERDICT_C = [
    "Confianza del modelo: {pct:.0f}%",
    "El modelo respalda esta prediccion con un {pct:.0f}% de confianza",
    "Fiabilidad del pronostico: {pct:.0f}%",
]

_MD1_TEXT = [
    "Ambos equipos arrancan el grupo con la ilusion intacta",
    "Primera fecha del grupo. Todos comienzan con cero presion",
    "Se abre el grupo con dos equipos buscando sumar de a tres",
    "Arranca la fase de grupos. Partido clave para marcar el rumbo",
]

_MD2_TEXT = [
    "Segunda fecha del grupo. Quien gana se acomoda, quien pierde queda contra las cuerdas",
    "Partido crucial en la segunda jornada. Los puntos empiezan a pesar",
    "Mitad de la fase de grupos. Cada resultado define el panorama",
    "Jornada decisiva para acomodarse en la tabla del grupo",
]

_MD3_CONTENDER_TEXT = [
    "Necesita ganar si o si para seguir con vida. La presion esta al maximo",
    "Fecha definitoria. Se juega las ultimas fichas para clasificar",
    "Partido de vida o muerte. No hay margen de error",
]

_MD3_QUALIFIED_TEXT = [
    "Ya esta clasificado, pero buscara asegurar el primer puesto",
    "Matematicamente clasificado. Busca cerrar primero en el grupo",
    "Tiene el pasaje asegurado y va por el primer lugar",
]

_MD3_ELIMINATED_TEXT = [
    "Ya eliminado, juega por el honor y para cerrar su participacion con dignidad",
    "Sin chances de clasificar, pero quiere despedirse con una victoria",
    "Eliminado matematicamente. Juega por el orgullo",
]

_KO_TEXT = [
    "Eliminacion directa. Un paso en falso y te vas a casa",
    "Partido de mata-mata. No hay segunda oportunidad",
    "Todo o nada. El perdedor queda eliminado del Mundial",
]

_TACTICAL_HIGH = [
    "Se espera un partido con llegadas y emocion",
    "Partido que promete goles y espectaculo",
    "Duelo ofensivo con alto potencial de gol",
]

_TACTICAL_MID = [
    "Se espera un partido de ritmo moderado",
    "Partido parejo que se definira por detalles",
    "Duelo tactico donde los pequenos detalles marcaran la diferencia",
]

_TACTICAL_LOW = [
    "Se preve un partido tactico y de pocos goles",
    "Partido cerrado donde un gol puede definir todo",
    "Duelo de baja intensidad ofensiva, predominara el orden",
]


def _pick(seed, pool):
    if not pool:
        return ""
    h = abs(hash(seed)) if seed is not None else 0
    return pool[h % len(pool)]


def _categorize_players(team_data, team_name):
    defenders = []
    midfielders = []
    forwards = []
    injured = INJURED_OUT.get(team_name, [])
    for p in team_data.get("players", []):
        name = p.get("name", "")
        if name in injured:
            continue
        pos = p.get("position", "")
        goals = p.get("goals_2026", 0) or 0
        minutes = p.get("minutes_2026", 0) or 0
        if pos in _DEF_POS:
            defenders.append((name, pos, goals, minutes))
        elif pos in _MID_POS:
            midfielders.append((name, pos, goals, minutes))
        elif pos in _FWD_POS:
            forwards.append((name, pos, goals, minutes))
    return defenders, midfielders, forwards


def _line_text(players, team_name, avg_gs, avg_gc, side, pool_good, pool_ok, pool_bad):
    if not players:
        return ""
    key_players = [p for p in players if p[3] > 500]
    if not key_players:
        return ""
    goals_line = sum(p[2] for p in key_players)
    best = max(key_players, key=lambda x: x[2])
    names = ", ".join(p[0] for p in key_players[:2])

    text = ""
    if side == "def":
        if avg_gc < 0.9:
            text = _pick(team_name + "_def_g", pool_good)
        elif avg_gc < 1.3:
            text = _pick(team_name + "_def_ok", pool_ok)
        else:
            text = _pick(team_name + "_def_b", pool_bad)
        text += f". {names} son sus baluartes en esa zona"
    elif side == "mid":
        if len(key_players) >= 3:
            text = _pick(team_name + "_mid_g", pool_good)
        elif len(key_players) >= 2:
            text = _pick(team_name + "_mid_ok", pool_ok)
        else:
            text = _pick(team_name + "_mid_b", pool_bad)
        text += f". {names} comandan la sala de maquinas"
    elif side == "fwd":
        if avg_gs > 1.8:
            text = _pick(team_name + "_fwd_g", pool_good)
        elif avg_gs > 1.2:
            text = _pick(team_name + "_fwd_ok", pool_ok)
        else:
            text = _pick(team_name + "_fwd_b", pool_bad)
        if goals_line > 5:
            text += f". {best[0]} es su principal amenaza ofensiva ({best[2]} goles en la temporada)"
        else:
            text += f". {best[0]} lidera la ofensiva"
    if not text:
        return ""
    return text + "."


def _get_intro(team_data, team_name):
    confed = _CONF_LABEL.get(team_data.get("confederation", ""), "internacional")
    rank = team_data.get("rank", 100) or 100
    form = team_data.get("form_streak", 0.5)
    if form >= 0.8:
        form_text = _pick(team_name + "_form_g", _FORM_GOOD)
    elif form >= 0.5:
        form_text = _pick(team_name + "_form_ok", _FORM_OK)
    else:
        form_text = _pick(team_name + "_form_b", _FORM_BAD)
    intro = _pick(team_name + "_intro", _INTRO_POOL)
    return intro.format(confed=confed, rank=rank, form_text=form_text)


def _friendly_description(team_name):
    ff = compute_friendly_form(team_name)
    if ff >= 8:
        return _pick(team_name + "_fr_g", _FRIENDLY_GOOD).capitalize()
    if ff >= 4:
        return _pick(team_name + "_fr_ok", _FRIENDLY_OK).capitalize()
    if ff < 0:
        return _pick(team_name + "_fr_b", _FRIENDLY_BAD).capitalize()
    return "Disputo amistosos sin resultados destacados"


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


def _format_wc_history(wc_str):
    if not wc_str:
        return "Primera participacion en un Mundial"
    if wc_str.replace("_", " ").lower() in ("none", "", "primera participacion"):
        return "Primera participacion en un Mundial"
    return wc_str.replace("_", " ")


def _match_context(match):
    round_name = match.get("round", "")
    matchday = match.get("matchday")
    factors = match.get("factors", {})
    stakes_a = factors.get("stakes_a") if factors else None
    stakes_b = factors.get("stakes_b") if factors else None
    team_a = match["team_a"]
    team_b = match["team_b"]

    if not round_name.startswith("Group "):
        return _pick(team_a + "_ko", _KO_TEXT)

    if matchday == 3:
        parts_a = []
        parts_b = []
        if stakes_a == "contender":
            parts_a.append(_pick(team_a + "_md3_c", _MD3_CONTENDER_TEXT))
        elif stakes_a == "qualified":
            parts_a.append(_pick(team_a + "_md3_q", _MD3_QUALIFIED_TEXT))
        elif stakes_a == "eliminated":
            parts_a.append(_pick(team_a + "_md3_e", _MD3_ELIMINATED_TEXT))

        if stakes_b == "contender":
            parts_b.append(_pick(team_b + "_md3_c", _MD3_CONTENDER_TEXT))
        elif stakes_b == "qualified":
            parts_b.append(_pick(team_b + "_md3_q", _MD3_QUALIFIED_TEXT))
        elif stakes_b == "eliminated":
            parts_b.append(_pick(team_b + "_md3_e", _MD3_ELIMINATED_TEXT))

        result = "Tercera fecha del grupo. "
        if parts_a:
            result += team_a + ": " + parts_a[0] + ". "
        if parts_b:
            result += team_b + ": " + parts_b[0] + "."
        return result

    if matchday == 1:
        return _pick(team_a + "_md1", _MD1_TEXT) + "."
    if matchday == 2:
        return _pick(team_a + "_md2", _MD2_TEXT) + "."

    return "Partido correspondiente a la fase de grupos del Mundial 2026."


def _build_recommendation(match):
    conf = match.get("confidence", 0)
    team_a = match["team_a"]
    team_b = match["team_b"]
    probs = match.get("probabilities", {})
    a_win = probs.get("a_win", 0)
    b_win = probs.get("b_win", 0)
    prob_draw = probs.get("draw", 0)
    matchday = match.get("matchday")
    factors = match.get("factors", {})
    stakes_a = factors.get("stakes_a") if factors else None
    stakes_b = factors.get("stakes_b") if factors else None
    a_data = get_team(team_a)
    b_data = get_team(team_b)
    rank_a = a_data.get("rank", 100) or 100
    rank_b = b_data.get("rank", 100) or 100

    is_contender_vs_contender = (
        matchday == 3 and stakes_a == "contender" and stakes_b == "contender"
    )
    is_contender_vs_eliminated = (
        matchday == 3 and (
            (stakes_a == "contender" and stakes_b == "eliminated") or
            (stakes_a == "eliminated" and stakes_b == "contender")
        )
    )
    same_confed = (
        a_data.get("confederation") == b_data.get("confederation")
        and a_data.get("confederation")
    )
    both_top10 = rank_a <= 10 and rank_b <= 10

    if both_top10 and abs(conf - 50) < 10:
        return "CHOQUE DE TITANES - Dos potencias mundiales frente a frente"
    if same_confed and conf < 55:
        return "CLASICO CONTINENTAL - Duelo de maxima rivalidad regional"
    if is_contender_vs_contender:
        return "DUELO DE NECESIDADES - El que pierde se despide del Mundial"
    if is_contender_vs_eliminated:
        return "ULTIMA OPORTUNIDAD - Un equipo se juega la clasificacion"
    if conf >= 70 and a_win >= 55:
        return "LOCAL INGOBERNABLE - Favorito absoluto, resultado casi asegurado"
    if conf >= 70 and b_win >= 55:
        return "VISITANTE ARROLLADOR - Favorito solido como visitante"
    if conf >= 65:
        return "APUESTA SEGURA - Alta confianza en el resultado"
    if conf >= 60:
        if a_win >= 55:
            return "FAVORITO SIN DISCUSION - Ventaja solida pero no definitiva"
        return "FAVORITO SIN DISCUSION"
    if prob_draw >= 32:
        return "EMPATE PROBABLE - Partido muy parejo, la igualdad paga bien"
    if prob_draw >= 25:
        return "PARTIDO TRAMPA - Cuidado con la igualdad"
    if conf >= 52:
        if a_win > b_win:
            return "LIGERO FAVORITO - Ligera ventaja del que juega en casa"
        return "LIGERO FAVORITO - Ventaja minima del visitante"
    if 45 <= conf < 52:
        return "MONEDA AL AIRE - Partido parejo, cualquier resultado es posible"
    if conf < 45 and abs(rank_a - rank_b) <= 10:
        return "PARTIDO ABIERTO - Partido de pronostico reservado"
    if conf < 40:
        return "SORPRESA EN MARCHA - El modelo anticipa un resultado inesperado"
    return "PARTIDO DISPUTADO - Partido sin un favorito claro"


def _team_block(team_name, team_data, intro, friendly, star, top_scorer, top_goals, penalty, injured, wc, defs, mids, fwds, gs, gc):
    lines = []
    lines.append(f"{team_name}, {intro}.")
    if friendly:
        lines.append(friendly + ".")
    def_text = _line_text(defs, team_name, gs, gc, "def", _DEF_GOOD, _DEF_OK, _DEF_BAD)
    if def_text:
        lines.append(def_text)
    mid_text = _line_text(mids, team_name, gs, gc, "mid", _MID_GOOD, _MID_OK, _MID_BAD)
    if mid_text:
        lines.append(mid_text)
    fwd_text = _line_text(fwds, team_name, gs, gc, "fwd", _FWD_GOOD, _FWD_OK, _FWD_BAD)
    if fwd_text:
        lines.append(fwd_text)
    extras = []
    if penalty:
        extras.append(f"{penalty} es el pateador de penales designado")
    if injured:
        extras.append(f"Bajas: {', '.join(injured)}")
    if extras:
        lines.append(". ".join(extras) + ".")
    if top_goals >= 10 and top_scorer:
        lines.append(f"{top_scorer} lleva {top_goals} goles en la temporada.")
    lines.append(wc + ".")
    return " ".join(lines)


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

    results = []

    # --- Team A ---
    a_def, a_mid, a_fwd = _categorize_players(a_data, team_a)
    a_gs = a_data.get("goals_scored_avg", 1.5) or 1.5
    a_gc = a_data.get("goals_conceded_avg", 1.2) or 1.2
    results.append(
        _team_block(
            team_a, a_data,
            _get_intro(a_data, team_a),
            _friendly_description(team_a),
            _get_star_player(team_a),
            *_top_scorer_info(team_a),
            _penalty_taker(team_a),
            _injured_info(team_a),
            _format_wc_history(a_data.get("wc_history", "")),
            a_def, a_mid, a_fwd, a_gs, a_gc,
        )
    )

    # --- Team B ---
    b_def, b_mid, b_fwd = _categorize_players(b_data, team_b)
    b_gs = b_data.get("goals_scored_avg", 1.5) or 1.5
    b_gc = b_data.get("goals_conceded_avg", 1.2) or 1.2
    results.append(
        _team_block(
            team_b, b_data,
            _get_intro(b_data, team_b),
            _friendly_description(team_b),
            _get_star_player(team_b),
            *_top_scorer_info(team_b),
            _penalty_taker(team_b),
            _injured_info(team_b),
            _format_wc_history(b_data.get("wc_history", "")),
            b_def, b_mid, b_fwd, b_gs, b_gc,
        )
    )

    # --- Context ---
    results.append(_match_context(match))

    # --- Tactical ---
    parts = []
    xg_total = xg_a + xg_b
    if xg_total >= 4:
        tact = _pick(team_a + "_tact_h", _TACTICAL_HIGH)
    elif xg_total >= 2.5:
        tact = _pick(team_a + "_tact_m", _TACTICAL_MID)
    else:
        tact = _pick(team_a + "_tact_l", _TACTICAL_LOW)
    tact += f" (xG total: {xg_total:.2f})."
    parts.append(tact)

    if factors:
        valid_factors = {k: v for k, v in factors.items() if v is not None and k not in ("stakes_a", "stakes_b")}
        if valid_factors:
            sorted_factors = sorted(valid_factors.items(), key=lambda x: abs(x[1]), reverse=True)
            top_factor_name, top_factor_val = sorted_factors[0]
            if abs(top_factor_val) > 1.5:
                factor_labels = {
                    "strength": "calidad de plantilla",
                    "player_stats": "rendimiento individual",
                    "home": "factor localia",
                    "experience": "experiencia internacional",
                    "friendly_form": "forma en amistosos recientes",
                    "market_value": "valor de mercado",
                    "squad_depth": "profundidad del banquillo",
                    "rest_days": "descanso entre partidos",
                    "stakes": "presion del momento",
                    "history": "historial mundialista",
                    "travel_fatigue": "desgaste por viajes",
                    "morale": "moral del equipo",
                    "trophy_pedigree": "palmares de sus jugadores",
                    "height_advantage": "ventaja aerea",
                    "club_chemistry": "quimica entre companeros",
                    "climate": "adaptacion climatica",
                    "odds": "cuotas de mercado",
                    "foreign_pct": "experiencia en ligas extranjeras",
                }
                label = factor_labels.get(top_factor_name, top_factor_name)
                if top_factor_val > 0:
                    parts.append(f"El factor {label} favorece claramente a {team_a}.")
                else:
                    parts.append(f"El factor {label} favorece claramente a {team_b}.")

    if a_gs > b_gc and a_gs > 1.2:
        parts.append(f"{team_a} tiene poderio ofensivo ({a_gs:.1f} goles/partido) y buscara imponer su juego.")
    if b_gs > a_gc and b_gs > 1.2:
        parts.append(f"{team_b} cuenta con un ataque peligroso ({b_gs:.1f} goles/partido).")
    if a_gc < 0.8:
        parts.append(f"{team_a} se destaca por su solidez defensiva ({a_gc:.1f} goles recibidos/partido).")
    if b_gc < 0.8:
        parts.append(f"{team_b} cuenta con una defensa solida ({b_gc:.1f} goles recibidos/partido).")

    results.append(" ".join(parts))

    # --- Penalty context (solo KO) ---
    round_name = match.get("round", "")
    if not round_name.startswith("Group "):
        gk_a_name = a_data.get("gk_name", "")
        gk_b_name = b_data.get("gk_name", "")
        gk_a_rat = a_data.get("gk_penalty_save", 5.0)
        gk_b_rat = b_data.get("gk_penalty_save", 5.0)
        pen_lines = []

        if prob_draw >= 25:
            pen_lines.append(
                "El porcentaje de empate es alto, "
                "lo que podria llevar el partido a tiempo extra y posiblemente a penales."
            )

        if gk_a_rat >= 8.0 and gk_b_rat >= 8.0:
            pen_lines.append(
                f"Ambos arqueros son especialistas: "
                f"{gk_a_name} ({gk_a_rat:.1f}/10) y {gk_b_name} ({gk_b_rat:.1f}/10). "
                "Si la definicion es desde los 12 pasos, seria un duelo de alto nivel."
            )
        elif gk_a_rat >= 8.0:
            pen_lines.append(
                f"{team_a} cuenta con {gk_a_name}, "
                f"especialista en atajar penales ({gk_a_rat:.1f}/10). "
                f"Si el partido llega a los penales, la ventaja es para {team_a}."
            )
        elif gk_b_rat >= 8.0:
            pen_lines.append(
                f"{team_b} cuenta con {gk_b_name}, "
                f"especialista en atajar penales ({gk_b_rat:.1f}/10). "
                f"Si el partido llega a los penales, la ventaja es para {team_b}."
            )
        elif gk_a_rat >= 7.0 or gk_b_rat >= 7.0:
            best = team_a if gk_a_rat >= gk_b_rat else team_b
            best_name = gk_a_name if gk_a_rat >= gk_b_rat else gk_b_name
            pen_lines.append(
                f"En los penales, {best} cuenta con {best_name}, "
                "un arquero con experiencia en situaciones de presion."
            )

        if pen_lines:
            results.append(" ".join(pen_lines))

    # --- Veredict ---
    if a_win >= 50:
        ver_winner = _pick(team_a + "_v_a", _VERDICT_A).format(team=team_a, pct=a_win)
    elif b_win >= 50:
        ver_winner = _pick(team_b + "_v_a", _VERDICT_A).format(team=team_b, pct=b_win)
    else:
        winner = match.get("winner")
        if winner and winner != "Empate":
            wp = a_win if winner == team_a else b_win
            ver_winner = f"Partido muy parejo, pero el modelo se inclina por {winner} ({wp:.0f}% de probabilidad)."
        else:
            ver_winner = f"Partido muy parejo: empate ({prob_draw:.0f}%) o definicion por detalles."

    if prob_draw >= 28:
        ver_draw = _pick(team_a + "_v_b_high", _VERDICT_B_HIGH).format(pct=prob_draw)
    elif prob_draw <= 20:
        ver_draw = _pick(team_a + "_v_b_low", _VERDICT_B).format(pct=prob_draw)
    else:
        ver_draw = f"Empate posible ({prob_draw:.0f}%)."

    ver_conf = _pick(team_a + "_v_c", _VERDICT_C).format(pct=conf)

    results.append(f"--- VEREDICTO PRODE ---\n{ver_winner}\n{ver_draw}\n{ver_conf}")

    return "\n\n".join(results)


_REAL_BADGE_POOL = [
    "VICTORIA CONTUNDENTE", "TRIUNFO MERECIDO",
    "VICTORIA SUFRIDA", "PALIZA", "ROBO",
    "EMPATE JUSTO", "EMPATE INJUSTO", "EMPATE SIN GOLES",
    "EMPATE EMOCIONANTE", "PARTIDAZO", "PARTIDO CALIENTE",
    "VICTORIA CON HOMBRE DE MAS",
]

def _build_real_recommendation(match):
    sa = match["score_a"]
    sb = match["score_b"]
    stats = match.get("result_stats", {})
    ta = match["team_a"]
    tb = match["team_b"]
    total_goals = sa + sb

    total_cards = 0
    for team_name in (ta, tb):
        team_st = stats.get(team_name, {})
        total_cards += len(team_st.get("yellow_cards", []))
        total_cards += len(team_st.get("red_cards", []))

    if total_goals >= 5:
        return "PARTIDAZO"
    if total_cards >= 5:
        return "PARTIDO CALIENTE"

    red_a = len(stats.get(ta, {}).get("red_cards", []))
    red_b = len(stats.get(tb, {}).get("red_cards", []))

    def _dom(team):
        st = stats.get(team, {})
        return (
            st.get("xG", 0) or 0,
            st.get("possession", 0) or 0,
            st.get("total_shots", 0) or 0,
        )

    dom_a = _dom(ta)
    dom_b = _dom(tb)
    xg_ratio = dom_a[0] / max(dom_b[0], 0.01)
    poss_diff = dom_a[1] - dom_b[1]
    shot_diff = dom_a[2] - dom_b[2]
    strong_dom = xg_ratio >= 1.8 and poss_diff >= 8 and shot_diff >= 5
    slight_dom = xg_ratio >= 1.3 or poss_diff >= 5 or shot_diff >= 3

    if sa > sb:
        if red_b > 0:
            return "VICTORIA CON HOMBRE DE MAS"
        if sa - sb >= 3:
            return "PALIZA"
        if strong_dom:
            return "VICTORIA CONTUNDENTE"
        if slight_dom:
            return "TRIUNFO MERECIDO"
        return "VICTORIA SUFRIDA"
    elif sb > sa:
        if red_a > 0:
            return "VICTORIA CON HOMBRE DE MAS"
        if sb - sa >= 3:
            return "PALIZA"
        dom_a, dom_b = dom_b, dom_a
        xg_ratio = dom_a[0] / max(dom_b[0], 0.01)
        poss_diff = dom_a[1] - dom_b[1]
        shot_diff = dom_a[2] - dom_b[2]
        strong_dom = xg_ratio >= 1.8 and poss_diff >= 8 and shot_diff >= 5
        slight_dom = xg_ratio >= 1.3 or poss_diff >= 5 or shot_diff >= 3
        if strong_dom:
            return "VICTORIA CONTUNDENTE"
        if slight_dom:
            return "TRIUNFO MERECIDO"
        return "VICTORIA SUFRIDA"
    else:
        if sa == 0 and sb == 0:
            return "EMPATE SIN GOLES"
        if total_goals >= 4:
            return "EMPATE EMOCIONANTE"
        if strong_dom or slight_dom:
            return "EMPATE INJUSTO"
        return "EMPATE JUSTO"


def _build_real_narrative(match):
    ta = match["team_a"]
    tb = match["team_b"]
    sa = match["score_a"]
    sb = match["score_b"]
    stats = match.get("result_stats", {})
    xg_a = match.get("expected_goals_a", 0) or 0
    xg_b = match.get("expected_goals_b", 0) or 0
    winner = match.get("winner", "Empate")

    fragments = []

    # --- Summary ---
    if winner == "Empate":
        fragments.append(
            f"RESULTADO FINAL: {team_name_es(ta)} {sa}-{sb} {team_name_es(tb)}. "
            f"Empate en un partido que deja a ambos equipos sumando un punto."
        )
    else:
        loser = match.get("loser", "")
        fragments.append(
            f"RESULTADO FINAL: {team_name_es(ta)} {sa}-{sb} {team_name_es(tb)}. "
            f"{team_name_es(winner)} se queda con la victoria en un "
            f"{'partidazo' if sa + sb >= 5 else 'partido'} que "
            f"{'domino de principio a fin' if abs(xg_a - xg_b) > 0.8 else 'se definio por detalles'}."
        )

    # --- Goals ---
    for team_name in (ta, tb):
        team_st = stats.get(team_name, {})
        goals_list = team_st.get("goals", [])
        if goals_list:
            parts = []
            for g in goals_list:
                g_player = g.get("player", "?")
                g_min = g.get("minute", "")
                g_assist = g.get("assist", "")
                if g_assist:
                    parts.append(f"{g_player} {g_min}' (asistencia: {g_assist})")
                else:
                    parts.append(f"{g_player} {g_min}'")
            fragments.append(
                f"Goles de {team_name_es(team_name)}: {'; '.join(parts)}."
            )

    # --- Stats comparison ---
    st_a = stats.get(ta, {})
    st_b = stats.get(tb, {})
    poss_a = st_a.get("possession", 0) or 0
    poss_b = st_b.get("possession", 0) or 0
    shots_a = st_a.get("total_shots", 0) or 0
    shots_b = st_b.get("total_shots", 0) or 0
    sot_a = st_a.get("shots_on_target", 0) or 0
    sot_b = st_b.get("shots_on_target", 0) or 0
    pa_a = st_a.get("passes_accurate", 0) or 0
    pt_a = st_a.get("passes_total", 1) or 1
    pa_b = st_b.get("passes_accurate", 0) or 0
    pt_b = st_b.get("passes_total", 1) or 1
    corn_a = st_a.get("corners", 0) or 0
    corn_b = st_b.get("corners", 0) or 0
    saves_a = st_a.get("saves", 0) or 0
    saves_b = st_b.get("saves", 0) or 0
    fouls_a = st_a.get("fouls", 0) or 0
    fouls_b = st_b.get("fouls", 0) or 0
    aer_a_w = st_a.get("aerial_duels_won", 0) or 0
    aer_a_t = st_a.get("aerial_duels_total", 1) or 1
    aer_b_w = st_b.get("aerial_duels_won", 0) or 0
    aer_b_t = st_b.get("aerial_duels_total", 1) or 1

    pct_a = int(pa_a / pt_a * 100) if pt_a else 0
    pct_b = int(pa_b / pt_b * 100) if pt_b else 0
    aer_pct_a = int(aer_a_w / aer_a_t * 100) if aer_a_t else 0
    aer_pct_b = int(aer_b_w / aer_b_t * 100) if aer_b_t else 0

    stat_lines = []
    stat_lines.append(
        f"Posesion: {team_name_es(ta)} {poss_a}% vs {poss_b}% {team_name_es(tb)}"
    )
    stat_lines.append(
        f"xG: {team_name_es(ta)} {xg_a:.2f} vs {xg_b:.2f} {team_name_es(tb)}"
    )
    stat_lines.append(
        f"Tiros: {shots_a} ({sot_a} al arco) vs {shots_b} ({sot_b} al arco)"
    )
    stat_lines.append(
        f"Pases precisos: {pa_a}/{pt_a} ({pct_a}%) vs {pa_b}/{pt_b} ({pct_b}%)"
    )
    stat_lines.append(
        f"Corneres: {corn_a} vs {corn_b}"
    )
    stat_lines.append(
        f"Atajadas: {saves_a} vs {saves_b}"
    )
    stat_lines.append(
        f"Duelos aereos ganados: {aer_a_w}/{aer_a_t} ({aer_pct_a}%) vs "
        f"{aer_b_w}/{aer_b_t} ({aer_pct_b}%)"
    )
    stat_lines.append(
        f"Faltas cometidas: {fouls_a} vs {fouls_b}"
    )

    fragments.append("Estadisticas del partido:\n" + "\n".join(stat_lines))

    # --- Cards ---
    card_parts = []
    for team_name in (ta, tb):
        team_st = stats.get(team_name, {})
        ycs = team_st.get("yellow_cards", [])
        rcs = team_st.get("red_cards", [])
        if ycs:
            names = [c.get("player", "?") for c in ycs]
            card_parts.append(
                f"{team_name_es(team_name)}: {', '.join(names)} ({'1 amarilla' if len(names)==1 else f'{len(names)} amarillas'})"
            )
        if rcs:
            names = [c.get("player", "?") for c in rcs]
            card_parts.append(
                f"{team_name_es(team_name)}: {', '.join(names)} ({'1 roja' if len(names)==1 else f'{len(names)} rojas'})"
            )
    if card_parts:
        fragments.append("Tarjetas: " + " | ".join(card_parts))
    else:
        fragments.append("Tarjetas: el partido se jugo sin amonestaciones.")

    # --- Errors ---
    err_a = st_a.get("errors_leading_to_shot", 0) or 0
    err_a_g = st_a.get("errors_leading_to_goal", 0) or 0
    err_b = st_b.get("errors_leading_to_shot", 0) or 0
    err_b_g = st_b.get("errors_leading_to_goal", 0) or 0
    err_parts = []
    if err_a or err_a_g:
        err_parts.append(
            f"{team_name_es(ta)}: {err_a} error(es) que llevaron a tiro, "
            f"{err_a_g} que llevaron a gol"
        )
    if err_b or err_b_g:
        err_parts.append(
            f"{team_name_es(tb)}: {err_b} error(es) que llevaron a tiro, "
            f"{err_b_g} que llevaron a gol"
        )
    if err_parts:
        fragments.append("Errores defensivos: " + " | ".join(err_parts))

    # --- Context ---
    round_name = match.get("round", "")
    if winner == "Empate":
        fragments.append(
            f"Con este empate, {team_name_es(ta)} y {team_name_es(tb)} suman 1 punto "
            f"en {round_name or 'el grupo'}."
        )
    else:
        fragments.append(
            f"{team_name_es(winner)} suma 3 puntos vitales en "
            f"{round_name or 'el grupo'}."
        )

    return "\n\n".join(fragments)


def generate_match_analysis(match):
    try:
        if match.get("result_type") == "real":
            rec = _build_real_recommendation(match)
            narrative = _build_real_narrative(match)
            return rec + "\n\n" + narrative
        rec = _build_recommendation(match)
        narrative = _build_narrative(match)
        return rec + "\n\n" + narrative
    except Exception:
        return ""
