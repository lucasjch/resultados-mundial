# -*- coding: utf-8 -*-
"""GUI tkinter para visualizar el prode del Mundial 2026."""

import json
import math
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import urllib.request
import ctypes

import sv_ttk
from prode_mundial.data import team_name_es, TEAM_ES

if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS')
    sys.path.insert(0, os.path.join(BASE_DIR, "prode_mundial"))
    OUTPUT_DIR = os.path.join(BASE_DIR, "prode_mundial", "output")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)
    parent_of_pkg = os.path.dirname(BASE_DIR)
    if parent_of_pkg not in sys.path:
        sys.path.insert(0, parent_of_pkg)
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FLAGS_DIR = os.path.join(OUTPUT_DIR, "flags")

# ── Font system ──────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    FONT_DIR = os.path.join(sys._MEIPASS, "prode_mundial", "assets", "fonts")
else:
    FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
_BEBAS_PATH = os.path.join(FONT_DIR, "BebasNeue-Regular.ttf")
_TEKO_PATH = os.path.join(FONT_DIR, "Teko-Bold.ttf")
_FONT_URLS = {
    _BEBAS_PATH: "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    _TEKO_PATH: "https://github.com/google/fonts/raw/main/ofl/teko/Teko%5Bwght%5D.ttf",
}

def _ensure_fonts():
    for path, url in _FONT_URLS.items():
        if not os.path.exists(path):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                urllib.request.urlretrieve(url, path)
            except Exception:
                pass

_ensure_fonts()

def _load_fonts():
    loaded = 0
    try:
        gdi32 = ctypes.windll.gdi32
        for path in _FONT_URLS:
            if os.path.exists(path):
                r = gdi32.AddFontResourceExW(path, 0x10, 0)
                if r:
                    loaded += 1
    except Exception:
        pass
    return loaded == len(_FONT_URLS)

_FONTS_OK = _load_fonts()

_TEAM_FLAGS = {
    "Mexico":"mx","South Korea":"kr","South Africa":"za","Czechia":"cz",
    "Canada":"ca","Switzerland":"ch","Qatar":"qa","Bosnia & Herzegovina":"ba",
    "Brazil":"br","Morocco":"ma","Scotland":"gb-sct","Haiti":"ht","USA":"us",
    "Paraguay":"py","Australia":"au","Turkey":"tr","Germany":"de",
    "Ecuador":"ec","Ivory Coast":"ci","Curacao":"cw","Netherlands":"nl",
    "Japan":"jp","Sweden":"se","Tunisia":"tn","Belgium":"be","Egypt":"eg",
    "Iran":"ir","New Zealand":"nz","Spain":"es","Uruguay":"uy",
    "Saudi Arabia":"sa","Cape Verde":"cv","France":"fr","Norway":"no",
    "Senegal":"sn","Iraq":"iq","Argentina":"ar","Algeria":"dz",
    "Austria":"at","Jordan":"jo","Portugal":"pt","Colombia":"co",
    "Uzbekistan":"uz","DR Congo":"cd","England":"gb-eng","Croatia":"hr",
    "Ghana":"gh","Panama":"pa",
}

_COLORS = {
    "bg":           "#0d1117",
    "fg":           "#e6edf3",
    "accent":       "#c9a84c",       # dorado Copa del Mundo
    "accent2":      "#1a6b3a",       # verde césped
    "card_bg":      "#161b22",
    "card_border":  "#30363d",
    "score_bg":     "#1a6b3a",       # verde para el marcador
    "star":         "#ffd700",
    "btn_face":     "#238636",       # verde botón
    "btn_shadow":   "#145522",       # sombra botón
    "btn_hover":    "#2ea043",
    "btn_fg":       "#ffffff",
    "green":        "#3fb950",
    "red":          "#f85149",
    "yellow":       "#d29922",
    "subtitle":     "#8b949e",
    "badge_win":    "#1a6b3a",
    "badge_draw":   "#9e6a03",
    "badge_upset":  "#8b1a1a",
    "tab_active":   "#c9a84c",
    "accent_green": "#00FF66",
    "accent_purple":"#9b59b6",
}

_FONT_H = ("Corbel", 24, "bold")
_FONT_SH = ("Corbel", 14)
_FONT_M = ("Corbel", 11)
_FONT_S = ("Corbel", 9)
_FONT_SCORE = ("Corbel", 32, "bold")
_FONT_TEAM = ("Corbel", 20, "bold")
_FONT_TAB = ("Consolas", 10)
_FONT_TAB_H = ("Consolas", 10, "bold")
_FONT_BTN = ("Segoe UI", 11, "bold italic")

if _FONTS_OK:
    _FONT_H = ("Bebas Neue", 22)
    _FONT_SH = ("Corbel", 14)
    _FONT_M = ("Corbel", 11)
    _FONT_S = ("Corbel", 9)
    _FONT_SCORE = ("Teko", 36, "bold")
    _FONT_TEAM = ("Teko", 20, "bold")
else:
    _FONT_H = ("Corbel", 24, "bold")
    _FONT_SH = ("Corbel", 14)
    _FONT_M = ("Corbel", 11)
    _FONT_S = ("Corbel", 9)
    _FONT_SCORE = ("Corbel", 32, "bold")
    _FONT_TEAM = ("Corbel", 20, "bold")

def _safe(text):
    return str(text)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
if not os.path.exists(FLAGS_DIR):
    os.makedirs(FLAGS_DIR, exist_ok=True)


def load_json(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flag(name):
    code = _TEAM_FLAGS.get(name, "")
    if code and len(code) == 2:
        return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))
    return ""


def flag_name(name):
    f = flag(name)
    return f"{f} {name}" if f else name


def stars_html(pct):
    filled = int(pct / 20)
    return "★" * filled + "☆" * (5 - filled)


def _poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)

    def _enter(self, _):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.text, justify=tk.LEFT,
                       background="#1a1a3a", foreground="#e0e0e0",
                       relief=tk.SOLID, borderwidth=1, font=("Consolas", 9))
        lbl.pack()

    def _leave(self, _):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ProdeGUI:
    def __init__(self, root, pre_data=None):
        self.root = root
        root.title("Prode Mundial 2026")
        root.configure(bg=_COLORS["bg"])
        root.geometry("1100x720")
        root.resizable(True, True)
        try:
            root.state('zoomed')
        except Exception:
            try:
                w = root.winfo_screenwidth()
                h = root.winfo_screenheight()
                root.geometry(f"{w}x{h}")
            except Exception:
                pass

        if pre_data:
            groups = pre_data.get("groups", [])
            knockout = pre_data.get("knockout", [])
            tables = pre_data.get("tables", {})
            goleadores = pre_data.get("goleadores", [])
        else:
            groups = knockout = tables = prode = goleadores = None
            try:
                import prode_mundial.bracket as _pmb
                import prode_mundial.top_scorer as _pmt
                import prode_mundial.output as _pmo
                import prode_mundial.real_results as _pmr
                import prode_mundial.data as _pmd
                import prode_mundial.player_ratings as _pmpr
                _rr_path = os.path.join(OUTPUT_DIR, "real_results.json")
                _real_results = _pmr.load_real_results(_rr_path) if os.path.exists(_rr_path) else None
                _apr = {}
                _atr = {}
                try:
                    _pmpr.PLAYER_RATINGS_DB.seed_if_empty()
                    for _t in _pmd.TEAMS:
                        _a = _pmpr.PLAYER_RATINGS_DB.get_team_avg_ratings(_t)
                        if _a:
                            _apr[_t] = _a
                        _r = _pmpr.PLAYER_RATINGS_DB.get_team_avg_team_rating(_t)
                        if _r != 0.0:
                            _atr[_t] = _r
                except ImportError:
                    pass
                gp, gr, kp = _pmb.run_full_simulation(quiet=True, real_results=_real_results,
                                                       avg_player_ratings=_apr, avg_team_ratings=_atr)
                scorers, _ = _pmt.compute_top_scorers(gp, kp, top_n=20)
                goleadores = [{"player": p, "team": t, "goals": g} for p, t, g in scorers]
                tables = gr
                _pmo.export_all(gp, gr, kp)
                groups = load_json("fase_grupos.json") or gp or []
                knockout = load_json("eliminatorias.json") or kp or []
            except Exception:
                import traceback; traceback.print_exc()

            groups = groups or load_json("fase_grupos.json") or []
            knockout = knockout or load_json("eliminatorias.json") or []
            tables = tables or load_json("tabla_posiciones.json") or {}
            goleadores = goleadores or self._load_goleadores(groups, knockout)

        self.data = {
            "groups": groups,
            "knockout": knockout,
            "tables": tables,
            "prode": groups + knockout,
            "goleadores": goleadores,
            "jugadores": load_json("jugadores_destacados.json") or {},
        }
        self._idx = {"groups": 0, "knockout": 0}
        self._flag_cache = {}
        self._build_ui()

    def _load_goleadores(self, gp, kp):
        if gp or kp:
            try:
                from prode_mundial.top_scorer import compute_top_scorers
                scorers, _ = compute_top_scorers(gp, kp, top_n=20)
                return [{"player": p, "team": t, "goals": g} for p, t, g in scorers]
            except Exception:
                import traceback; traceback.print_exc()
        return []

    def _get_flag(self, team, width=24, height=18):
        code = _TEAM_FLAGS.get(team, "")
        if not code:
            return None
        key = f"{code}_{width}x{height}"
        if key in self._flag_cache:
            return self._flag_cache[key]
        flag_path = os.path.join(FLAGS_DIR, f"{code}.png")
        if not os.path.exists(flag_path):
            try:
                import requests
                url = f"https://flagcdn.com/24x18/{code}.png"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(flag_path, "wb") as f:
                        f.write(r.content)
            except Exception:
                return None
        if not os.path.exists(flag_path):
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(flag_path).resize((width, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._flag_cache[key] = photo
            return photo
        except Exception:
            return None

    def _styled_btn(self, parent, text, cmd):
        btn = tk.Button(
            parent, text=text, font=_FONT_BTN,
            bg=_COLORS["btn_face"], fg=_COLORS["btn_fg"],
            activebackground=_COLORS["btn_hover"],
            activeforeground="#ffffff",
            relief=tk.RAISED, bd=3,
            padx=18, pady=6,
            cursor="hand2",
            command=cmd
        )
        def _press(e):
            btn.config(relief=tk.SUNKEN, bg=_COLORS["btn_shadow"])
        def _release(e):
            btn.config(relief=tk.RAISED, bg=_COLORS["btn_face"])
        def _enter(e):
            btn.config(bg=_COLORS["btn_hover"])
        def _leave(e):
            btn.config(bg=_COLORS["btn_face"], relief=tk.RAISED)
        btn.bind("<ButtonPress-1>", _press)
        btn.bind("<ButtonRelease-1>", _release)
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)
        return btn

    def _build_ui(self):
        header = tk.Frame(self.root, bg=_COLORS["bg"], height=70)
        header.pack(fill=tk.X, padx=15, pady=(10, 0))
        header.pack_propagate(False)

        imput_dir = os.path.join(BASE_DIR, "prode_mundial", "imput") if getattr(sys, 'frozen', False) else os.path.join(BASE_DIR, "imput")
        imput_path = os.path.join(imput_dir, "fifa_world_cup_2026_cover.jpg")
        if os.path.exists(imput_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(imput_path)
                target_h = 64
                ratio = target_h / img.height
                display_w = int(img.width * ratio)
                img = img.resize((display_w, target_h), Image.Resampling.LANCZOS)
                self._banner_img = ImageTk.PhotoImage(img)
                lbl_banner = tk.Label(header, image=self._banner_img, bg=_COLORS["bg"])
                lbl_banner.pack(side=tk.LEFT, padx=5)
            except Exception:
                pass
        else:
            tk.Label(header, text="⚽ Mundial 2026",
                     font=("Corbel", 26, "bold"), bg=_COLORS["bg"],
                     fg=_COLORS["accent"]).pack(side=tk.LEFT, padx=15)
            tk.Label(header, text="Predicciones PRODE",
                     font=("Corbel", 13), bg=_COLORS["bg"],
                     fg=_COLORS["accent2"]).pack(side=tk.LEFT, padx=5, pady=(14, 0))
        tk.Label(header, text="por Lucas Congil Hadla",
                 font=("Corbel", 9), bg=_COLORS["bg"],
                 fg=_COLORS["subtitle"]).pack(side=tk.RIGHT, padx=15, pady=(14, 0))

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        style = ttk.Style()
        sv_ttk.set_theme("dark")
        style.configure("Vertical.TScrollbar", background="#1a1a4a", troughcolor=_COLORS["bg"],
                         arrowcolor=_COLORS["fg"], gripcount=0)
        style.configure("TNotebook", background=_COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=_COLORS["card_bg"],
                        foreground=_COLORS["fg"],
                        padding=[20, 8],
                        font=("Corbel", 12, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", _COLORS["tab_active"])],
                  foreground=[("selected", "#000000")])

        self._tab_info = ttk.Frame(nb)
        self._tab_groups = ttk.Frame(nb)
        self._tab_ko = ttk.Frame(nb)
        self._tab_stats = ttk.Frame(nb)
        self._tab_goleadores = ttk.Frame(nb)
        self._tab_jugadores = ttk.Frame(nb)
        self._tab_bonus = ttk.Frame(nb)

        nb.add(self._tab_info, text=" Info ")
        nb.add(self._tab_groups, text=" Grupos ")
        nb.add(self._tab_ko, text=" KO ")
        nb.add(self._tab_stats, text=" Stats ")
        nb.add(self._tab_goleadores, text=" Goleadores ")
        nb.add(self._tab_jugadores, text=" Jugadores ")
        nb.add(self._tab_bonus, text=" Bonus ")

        for _tab_name, _tab_builder in [
            ("info", self._build_info_tab),
            ("groups", self._build_groups_tab),
            ("ko", self._build_ko_tab),
            ("stats", self._build_stats_tab),
            ("goleadores", self._build_goleadores_tab),
            ("jugadores", self._build_jugadores_tab),
            ("bonus", self._build_bonus_tab),
        ]:
            try:
                _tab_builder()
            except Exception as _e:
                import traceback
                traceback.print_exc()
                _ef = tk.Frame(getattr(self, f"_tab_{_tab_name}"), bg=_COLORS["bg"])
                _ef.pack(fill=tk.BOTH, expand=True)
                tk.Label(_ef, text=f"Error al cargar esta pestana:\n{_e}",
                         font=_FONT_M, bg=_COLORS["bg"],
                         fg=_COLORS["red"]).pack(expand=True)

        status = tk.Label(self.root, text="Prode Mundial 2026 — Desarrollado por Lucas Congil Hadla",
                          bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                          anchor=tk.W, padx=15)
        status.pack(fill=tk.X)

    def _nav_frame(self, parent, tab_name):
        f = tk.Frame(parent, bg=_COLORS["bg"])
        f.pack(fill=tk.X, pady=5)
        btn_prev = self._styled_btn(f, " ◀ ", lambda: self._nav(tab_name, -1))
        btn_prev.pack(side=tk.LEFT, padx=5)
        lbl = tk.Label(f, text="", font=_FONT_M, bg=_COLORS["bg"],
                       fg=_COLORS["fg"])
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)
        setattr(self, f"_lbl_{tab_name}", lbl)
        btn_next = self._styled_btn(f, " ▶ ", lambda: self._nav(tab_name, 1))
        btn_next.pack(side=tk.RIGHT, padx=5)
        return f

    def _nav(self, tab_name, delta):
        items = self.data.get(tab_name, [])
        if not items:
            return
        if tab_name == "groups":
            filtered = self._filtered_group_indices
            n = len(filtered)
        else:
            n = len(items)
        idx = self._idx[tab_name]
        self._idx[tab_name] = (idx + delta) % n
        show = {"groups": "_show_group_match", "knockout": "_show_ko_match"}.get(tab_name)
        if show:
            getattr(self, show)()

    def _match_card(self, parent, match, idx, total):
        team_a = match.get("team_a", "?")
        team_b = match.get("team_b", "?")
        score_a = match.get("score_a", 0)
        score_b = match.get("score_b", 0)
        venue   = match.get("venue", "")
        conf    = match.get("confidence", 0)
        probs   = match.get("probabilities", {})
        prob_a  = probs.get("a_win", 0)
        prob_b  = probs.get("b_win", 0)
        prob_d  = probs.get("draw", 0)

        # Contenedor externo con borde dorado
        outer = tk.Frame(parent, bg=_COLORS["accent"], padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        card = tk.Frame(outer, bg=_COLORS["card_bg"])
        card.pack(fill=tk.BOTH, expand=True)
        card.columnconfigure(0, weight=1)

        row = 0

        # ── ANÁLISIS NARRATIVO ──────────────────────────────────────────────
        analysis = match.get("analysis", "")
        if analysis:
            rec_text, _, narrative = analysis.partition("\n\n")

            rt_lower = rec_text.lower()
            if "seguro" in rt_lower or "favorito" in rt_lower:
                badge_color = _COLORS["badge_win"]
            elif "empate" in rt_lower:
                badge_color = _COLORS["badge_draw"]
            elif "sorpresa" in rt_lower:
                badge_color = _COLORS["badge_upset"]
            else:
                badge_color = _COLORS["accent2"]

            badge_frame = tk.Frame(card, bg=badge_color)
            badge_frame.grid(row=row, column=0, sticky="ew")
            row += 1
            tk.Label(
                badge_frame, text=f"  {rec_text}  ",
                font=("Corbel", 11, "bold"),
                bg=badge_color, fg="#ffffff",
                anchor=tk.W, pady=6
            ).pack(fill=tk.X, padx=15)

            text_frame = tk.Frame(card, bg="#1c2128")
            text_frame.grid(row=row, column=0, sticky="nsew")
            card.rowconfigure(row, weight=1)
            row += 1

            text_w = tk.Text(
                text_frame, wrap=tk.WORD,
                bg="#1c2128", fg=_COLORS["fg"],
                font=("Corbel", 10), relief=tk.FLAT,
                highlightthickness=0, bd=0,
                padx=15, pady=8
            )
            text_w.pack(fill=tk.BOTH, expand=True)

            for eng, esp in sorted(TEAM_ES.items(), key=lambda x: -len(x[0])):
                narrative = narrative.replace(eng, esp)
            text_w.insert("1.0", narrative)
            text_w.config(state=tk.DISABLED)

        # ── SEPARADOR ────────────────────────────────────────────────────────
        sep = tk.Frame(card, bg=_COLORS["accent"], height=2)
        sep.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        row += 1

        # ── PROBABILIDADES ───────────────────────────────────────────────────
        prob_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        prob_frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        row += 1

        def _prob_pill(parent, team, prob, color):
            f = tk.Frame(parent, bg=color, padx=10, pady=3)
            f.pack(side=tk.LEFT, padx=4)
            pf = self._get_flag(team, 14, 10)
            if pf:
                tk.Label(f, image=pf, bg=color).pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(f, text=f"{team_name_es(team)}: {prob:.0f}%",
                     font=("Corbel", 10, "bold"), bg=color, fg="#ffffff").pack(side=tk.LEFT)

        win_color = _COLORS["accent2"] if prob_a >= prob_b else _COLORS["red"]
        _prob_pill(prob_frame, team_a, prob_a, win_color if prob_a >= prob_b else "#3a3a3a")
        draw_f = tk.Frame(prob_frame, bg="#3a3a3a", padx=10, pady=3)
        draw_f.pack(side=tk.LEFT, padx=4)
        tk.Label(draw_f, text=f"Empate: {prob_d:.0f}%",
                 font=("Corbel", 10), bg="#3a3a3a", fg=_COLORS["subtitle"]).pack()
        _prob_pill(prob_frame, team_b, prob_b, win_color if prob_b > prob_a else "#3a3a3a")

        # ── ESTRELLAS DE CONFIANZA ───────────────────────────────────────────
        stars = stars_html(conf)
        star_lbl = tk.Label(card, text=stars, font=("Corbel", 22),
                            bg=_COLORS["card_bg"], fg=_COLORS["star"])
        star_lbl.grid(row=row, column=0, sticky="ew", pady=4)
        ToolTip(star_lbl, f"Confianza: {conf:.0f}%\nBasada en 1500 simulaciones Poisson")
        row += 1

        # ── SCORE ROW ────────────────────────────────────────────────────────
        vs_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        vs_frame.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        vs_frame.columnconfigure(0, weight=1)
        vs_frame.columnconfigure(1, weight=0)
        vs_frame.columnconfigure(2, weight=1)
        row += 1

        # Columna 0: equipo A (sticky="e" → derecha, pegado al score)
        tf_a = tk.Frame(vs_frame, bg=_COLORS["card_bg"])
        tf_a.grid(row=0, column=0, sticky="e", padx=(0, 10))
        flag_a = self._get_flag(team_a, 32, 24)
        if flag_a:
            tk.Label(tf_a, image=flag_a, bg=_COLORS["card_bg"]).pack()
        tk.Label(tf_a, text=team_name_es(team_a).upper(), font=_FONT_TEAM,
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack()

        # Columna 1: score (centrado, no expande)
        sf = tk.Frame(vs_frame, bg=_COLORS["score_bg"],
                      highlightbackground=_COLORS["accent"],
                      highlightthickness=2, padx=8, pady=6)
        sf.grid(row=0, column=1)
        tk.Label(sf, text=f"{score_a} – {score_b}",
                 font=_FONT_SCORE,
                 bg=_COLORS["score_bg"], fg="#ffffff").pack()

        # Columna 2: equipo B (sticky="w" → izquierda, pegado al score)
        tf_b = tk.Frame(vs_frame, bg=_COLORS["card_bg"])
        tf_b.grid(row=0, column=2, sticky="w", padx=(10, 0))
        flag_b = self._get_flag(team_b, 32, 24)
        if flag_b:
            tk.Label(tf_b, image=flag_b, bg=_COLORS["card_bg"]).pack()
        tk.Label(tf_b, text=team_name_es(team_b).upper(), font=_FONT_TEAM,
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack()

        # ── GOLES EN PARTIDOS REALES ─────────────────────────────────────────
        goals = match.get("goals_scorers", {})
        if goals:
            goals_parts = []
            for t in [team_a, team_b]:
                tg = goals.get(t, [])
                if tg:
                    desc = "; ".join(
                        f"{g['player']} {g['minute']}'" +
                        (f" ({g['assist']})" if g.get('assist') else "")
                        for g in tg
                    )
                    goals_parts.append(f"{team_name_es(t)}: {desc}")
                else:
                    goals_parts.append(f"{team_name_es(t)}: —")
            goals_lbl = tk.Label(
                vs_frame, text="  ⚽  " + "  |  ".join(goals_parts),
                font=("Corbel", 10), bg=_COLORS["card_bg"],
                fg=_COLORS["subtitle"]
            )
            goals_lbl.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        # ── FOOTER ────────────────────────────────────────────────────────────
        round_label = match.get("round", "")
        grp_label = f"{round_label}  |  " if round_label else ""
        tk.Label(card,
                 text=f"  {grp_label} 📍 {venue}   ·   Partido {idx+1}/{total}",
                 font=("Corbel", 9), bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        return card

    def _compact_match_card(self, parent, match, idx, total):
        team_a = match.get("team_a", "?")
        team_b = match.get("team_b", "?")
        score_a = match.get("score_a", 0)
        score_b = match.get("score_b", 0)
        venue   = match.get("venue", "")
        conf    = match.get("confidence", 0)
        probs   = match.get("probabilities", {})
        prob_a  = probs.get("a_win", 0)
        prob_b  = probs.get("b_win", 0)

        analysis = match.get("analysis", "")
        if analysis:
            rec_text = analysis.split("\n\n")[0]
            rt_lower = rec_text.lower()
            if "seguro" in rt_lower or "favorito" in rt_lower:
                badge_color = _COLORS["badge_win"]
            elif "empate" in rt_lower:
                badge_color = _COLORS["badge_draw"]
            elif "sorpresa" in rt_lower:
                badge_color = _COLORS["badge_upset"]
            else:
                badge_color = _COLORS["accent2"]
        else:
            rec_text = ""
            badge_color = _COLORS["card_border"]

        outer = tk.Frame(parent, bg=_COLORS["card_border"], padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        card = tk.Frame(outer, bg=_COLORS["card_bg"])
        card.pack(fill=tk.BOTH, expand=True)

        # Badge row
        if rec_text:
            bf = tk.Frame(card, bg=badge_color)
            bf.pack(fill=tk.X)
            tk.Label(bf, text=f"  {rec_text}  ",
                     font=("Corbel", 8, "bold"),
                     bg=badge_color, fg="#ffffff",
                     anchor=tk.W, pady=2).pack(fill=tk.X, padx=8)

        # Score row
        vs = tk.Frame(card, bg=_COLORS["card_bg"])
        vs.pack(fill=tk.X, pady=(6, 2))
        f_a = self._get_flag(team_a, 20, 15)
        f_b = self._get_flag(team_b, 20, 15)

        tk.Label(vs, text=team_name_es(team_a).upper(), font=_FONT_TEAM,
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(8, 4))
        if f_a:
            tk.Label(vs, image=f_a, bg=_COLORS["card_bg"]).pack(side=tk.LEFT)
        tk.Label(vs, text=f"  {score_a} – {score_b}  ",
                 font=_FONT_SCORE, bg=_COLORS["card_bg"],
                 fg=_COLORS["accent_green"]).pack(side=tk.LEFT)
        if f_b:
            tk.Label(vs, image=f_b, bg=_COLORS["card_bg"]).pack(side=tk.LEFT)
        tk.Label(vs, text=team_name_es(team_b).upper(), font=_FONT_TEAM,
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(4, 8))

        # Confidence stars + probabilities pill
        meta = tk.Frame(card, bg=_COLORS["card_bg"])
        meta.pack(fill=tk.X, pady=(0, 4))
        stars_text = stars_html(conf)
        tk.Label(meta, text=stars_text, font=("Corbel", 14),
                 bg=_COLORS["card_bg"], fg=_COLORS["star"]).pack(side=tk.LEFT, padx=(8, 6))
        ToolTip(meta, f"Confianza: {conf:.0f}%")
        if prob_a >= prob_b:
            tk.Label(meta, text=f"{prob_a:.0f}%", font=_FONT_S,
                     bg=_COLORS["card_bg"], fg=_COLORS["accent_green"]).pack(side=tk.LEFT)
        else:
            tk.Label(meta, text=f"{prob_b:.0f}%", font=_FONT_S,
                     bg=_COLORS["card_bg"], fg=_COLORS["accent_green"]).pack(side=tk.LEFT)

        # Goals in real matches
        goals = match.get("goals_scorers", {})
        if goals:
            goals_parts = []
            for t in [team_a, team_b]:
                tg = goals.get(t, [])
                if tg:
                    desc = "; ".join(
                        f"{g['player']} {g['minute']}'" +
                        (f" ({g['assist']})" if g.get('assist') else "")
                        for g in tg
                    )
                    goals_parts.append(f"{team_name_es(t)}: {desc}")
                else:
                    goals_parts.append(f"{team_name_es(t)}: —")
            goals_lbl = tk.Label(
                card,
                text="  ⚽  " + "  |  ".join(goals_parts),
                font=("Corbel", 8), bg=_COLORS["card_bg"],
                fg=_COLORS["subtitle"]
            )
            goals_lbl.pack(fill=tk.X, padx=10, pady=(0, 2))

        # Footer
        round_label = match.get("round", "")
        grp_label = f"{round_label}  |  " if round_label else ""
        footer_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        footer_frame.pack(fill=tk.X, padx=10, pady=(0, 4))
        tk.Label(footer_frame, text=f"  {grp_label}📍 {venue}",
                 font=("Corbel", 8), bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
        if analysis:
            btn = tk.Button(footer_frame, text="LEER SINOPSIS",
                            font=("Corbel", 7, "bold"),
                            bg=_COLORS["accent2"], fg=_COLORS["bg"],
                            bd=0, padx=4, pady=1, cursor="hand2",
                            command=lambda m=match: self._show_synopsis_popup(m))
            btn.pack(side=tk.RIGHT)

    def _show_synopsis_popup(self, match):
        analysis = match.get("analysis", "")
        if not analysis:
            return
        team_a = team_name_es(match.get("team_a", "?"))
        team_b = team_name_es(match.get("team_b", "?"))
        score_a = match.get("score_a", 0)
        score_b = match.get("score_b", 0)
        popup = tk.Toplevel(self.root)
        popup.title(f"Sinopsis - {team_a} {score_a}-{score_b} {team_b}")
        popup.geometry("480x400")
        popup.configure(bg=_COLORS["bg"])
        popup.transient(self.root)
        popup.grab_set()
        rec_text = analysis.split("\n\n")[0]
        narrative = analysis.split("\n\n", 1)[1] if "\n\n" in analysis else ""
        rt_lower = rec_text.lower()
        if "seguro" in rt_lower or "favorito" in rt_lower:
            badge_color = _COLORS["badge_win"]
        elif "empate" in rt_lower:
            badge_color = _COLORS["badge_draw"]
        elif "sorpresa" in rt_lower:
            badge_color = _COLORS["badge_upset"]
        else:
            badge_color = _COLORS["accent2"]
        badge_frame = tk.Frame(popup, bg=badge_color)
        badge_frame.pack(fill=tk.X)
        tk.Label(badge_frame, text=f"  {rec_text}  ",
                 font=("Corbel", 11, "bold"),
                 bg=badge_color, fg="#ffffff",
                 anchor=tk.W, pady=5).pack(fill=tk.X, padx=10)
        text_frame = tk.Frame(popup, bg=_COLORS["bg"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 4))
        text_w = tk.Text(text_frame, wrap=tk.WORD,
                         font=("Corbel", 10),
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"],
                         relief=tk.FLAT, bd=6,
                         padx=10, pady=10)
        text_w.pack(fill=tk.BOTH, expand=True)
        text_w.insert("1.0", narrative)
        text_w.config(state=tk.DISABLED)
        btn_frame = tk.Frame(popup, bg=_COLORS["bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Button(btn_frame, text="CERRAR",
                  font=("Corbel", 9, "bold"),
                  bg=_COLORS["accent_green"], fg=_COLORS["bg"],
                  bd=0, padx=16, pady=4, cursor="hand2",
                  command=popup.destroy).pack()

    def _build_groups_tab(self):
        parent = self._tab_groups
        self._group_filter = None
        self._filtered_group_indices = list(range(len(self.data["groups"])))

        filter_frame = tk.Frame(parent, bg=_COLORS["bg"])
        filter_frame.pack(fill=tk.X, padx=15, pady=(8, 0))
        tk.Label(filter_frame, text="Grupo:", font=_FONT_M, bg=_COLORS["bg"],
                 fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 5))
        groups_list = ["Todos"] + [chr(65 + i) for i in range(12)]
        self._group_combo = ttk.Combobox(filter_frame, values=groups_list,
                                          state="readonly", width=10,
                                          font=("Corbel", 10))
        self._group_combo.current(0)
        self._group_combo.pack(side=tk.LEFT)
        self._group_combo.bind("<<ComboboxSelected>>", self._on_group_filter)

        # Canvas + Scrollbar for grid
        self._group_canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        self._group_scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                               command=self._group_canvas.yview)
        self._card_frame_groups = tk.Frame(self._group_canvas, bg=_COLORS["bg"])
        self._card_frame_groups.bind("<Configure>", lambda e: self._group_canvas.configure(
            scrollregion=self._group_canvas.bbox("all")))
        self._group_canvas.create_window((0, 0), window=self._card_frame_groups, anchor="nw")
        self._group_canvas.configure(yscrollcommand=self._group_scrollbar.set)
        self._group_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._group_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._group_canvas.bind("<Enter>",
            lambda e: self._group_canvas.bind_all("<MouseWheel>",
                lambda ev: self._group_canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        self._group_canvas.bind("<Leave>",
            lambda e: self._group_canvas.unbind_all("<MouseWheel>"))

        self._show_group_grid()

    def _on_group_filter(self, event=None):
        sel = self._group_combo.get()
        if sel == "Todos":
            self._group_filter = None
            self._filtered_group_indices = list(range(len(self.data["groups"])))
        else:
            self._group_filter = sel
            self._filtered_group_indices = [
                i for i, m in enumerate(self.data["groups"])
                if m.get("round", "").endswith(sel)
            ]
        self._show_group_grid()

    def _show_group_grid(self):
        for w in self._card_frame_groups.winfo_children():
            w.destroy()
        matches = self.data["groups"]
        if not matches:
            tk.Label(self._card_frame_groups, text="No hay datos. Ejecute main.py primero.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return
        filtered = self._filtered_group_indices
        cols = 3
        for ci in range(cols):
            self._card_frame_groups.columnconfigure(ci, weight=1, uniform="gp")
        for i, mi in enumerate(filtered):
            m = matches[mi]
            row_idx = i // cols
            col_idx = i % cols
            card_f = tk.Frame(self._card_frame_groups, bg=_COLORS["bg"])
            card_f.grid(row=row_idx, column=col_idx, sticky="nsew", padx=4, pady=4)
            self._compact_match_card(card_f, m, mi, len(filtered))

    def _build_ko_tab(self):
        parent = self._tab_ko
        self._ko_canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        self._ko_scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                            command=self._ko_canvas.yview)
        self._card_frame_ko = tk.Frame(self._ko_canvas, bg=_COLORS["bg"])
        self._card_frame_ko.bind("<Configure>", lambda e: self._ko_canvas.configure(
            scrollregion=self._ko_canvas.bbox("all")))
        self._ko_canvas.create_window((0, 0), window=self._card_frame_ko, anchor="nw")
        self._ko_canvas.configure(yscrollcommand=self._ko_scrollbar.set)
        self._ko_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._ko_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._ko_canvas.bind("<Enter>",
            lambda e: self._ko_canvas.bind_all("<MouseWheel>",
                lambda ev: self._ko_canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        self._ko_canvas.bind("<Leave>",
            lambda e: self._ko_canvas.unbind_all("<MouseWheel>"))
        self._show_ko_grid()

    def _show_ko_grid(self):
        for w in self._card_frame_ko.winfo_children():
            w.destroy()
        matches = self.data["knockout"]
        if not matches:
            tk.Label(self._card_frame_ko, text="No hay datos. Ejecute main.py primero.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return
        rounds_order = ["R32", "R16", "QF", "SF", "3°", "Final"]
        rounds_map = {}
        for m in matches:
            r = m.get("round", "KO")
            rounds_map.setdefault(r, []).append(m)
        cols = 3
        for ci in range(cols):
            self._card_frame_ko.columnconfigure(ci, weight=1, uniform="ko")
        row_idx = 0
        for r_name in rounds_order:
            if r_name not in rounds_map:
                continue
            r_matches = rounds_map[r_name]
            round_label = tk.Label(self._card_frame_ko, text=f"  {r_name}  ",
                                   font=("Corbel", 11, "bold"),
                                   bg=_COLORS["card_bg"],
                                   fg=_COLORS["accent"])
            round_label.grid(row=row_idx, column=0, columnspan=cols,
                             sticky="ew", padx=4, pady=(10, 2))
            row_idx += 1
            for i, m in enumerate(r_matches):
                col_idx = i % cols
                card_f = tk.Frame(self._card_frame_ko, bg=_COLORS["bg"])
                card_f.grid(row=row_idx, column=col_idx, sticky="nsew", padx=4, pady=4)
                self._compact_match_card(card_f, m, i, len(r_matches))
                if (i + 1) % cols == 0:
                    row_idx += 1
            if len(r_matches) % cols != 0:
                row_idx += 1

    def _build_stats_tab(self):
        parent = self._tab_stats
        tables = self.data.get("tables", {})
        if not tables:
            tk.Label(parent, text="No hay tabla de posiciones.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return

        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _on_stats_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_stats_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        sorted_groups = sorted(tables.keys())
        cols = 3
        outer = tk.Frame(scroll_frame, bg=_COLORS["bg"])
        outer.pack(fill=tk.X, padx=10, pady=5)

        for ci in range(cols):
            outer.columnconfigure(ci, weight=1, uniform="grpcol")

        for ci, g in enumerate(sorted_groups):
            row_idx = ci // cols
            col_idx = ci % cols
            grp_frame = tk.Frame(outer, bg=_COLORS["card_bg"],
                                 highlightbackground=_COLORS["card_border"],
                                 highlightthickness=1, padx=8, pady=4)
            grp_frame.grid(row=row_idx, column=col_idx, sticky="nsew",
                           padx=4, pady=4)

            tk.Label(grp_frame, text=f"Grupo {g}",
                     font=("Corbel", 12, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["accent"]).pack(anchor=tk.W)

            hdr_row = tk.Frame(grp_frame, bg=_COLORS["card_bg"])
            hdr_row.pack(fill=tk.X)
            tk.Label(hdr_row, text="", font=_FONT_TAB_H,
                     bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                     width=2).pack(side=tk.LEFT)
            tk.Label(hdr_row, text="", font=_FONT_TAB_H,
                     bg=_COLORS["card_bg"], width=3).pack(side=tk.LEFT)
            tk.Label(hdr_row, text="Equipo", font=_FONT_TAB_H,
                     bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                     width=20, anchor=tk.W).pack(side=tk.LEFT)
            for col, w in [("Pts", 3), ("GD", 3), ("GF", 3), ("GA", 4)]:
                tk.Label(hdr_row, text=col, font=_FONT_TAB_H,
                         bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                         width=w, anchor=tk.CENTER).pack(side=tk.RIGHT)

            teams = tables[g]
            for rank, entry in enumerate(teams, 1):
                if isinstance(entry, dict) and "team" in entry:
                    team_name = entry.get("team", "?")
                    pts = entry.get("pts", 0)
                    gd = entry.get("gd", 0)
                    gf = entry.get("gf", 0)
                    ga = entry.get("ga", 0)
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    team_name = entry[0]
                    d = entry[1]
                    pts = d.get("pts", 0)
                    gd = d.get("gd", 0)
                    gf = d.get("gf", 0)
                    ga = d.get("ga", 0)
                else:
                    continue
                clr = _COLORS["green"] if rank <= 2 else _COLORS["fg"]
                row_f = tk.Frame(grp_frame, bg=_COLORS["card_bg"])
                row_f.pack(fill=tk.X)
                rflag = self._get_flag(team_name, 16, 12)
                tk.Label(row_f, text="★" if rank <= 2 else " ",
                         font=_FONT_TAB, bg=_COLORS["card_bg"], fg=clr,
                         width=2).pack(side=tk.LEFT)
                if rflag:
                    tk.Label(row_f, image=rflag, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(2, 3))
                tk.Label(row_f, text=team_name_es(team_name), font=_FONT_TAB,
                         bg=_COLORS["card_bg"], fg=clr,
                         width=20, anchor=tk.W).pack(side=tk.LEFT)
                for val, w in [(str(pts), 3), (f"{gd:+d}", 3), (str(gf), 3), (str(ga), 4)]:
                    tk.Label(row_f, text=val, font=_FONT_TAB,
                             bg=_COLORS["card_bg"], fg=clr,
                             width=w, anchor=tk.CENTER).pack(side=tk.RIGHT)

        third = self._compute_third_placed(tables)
        if third:
            sep = tk.Frame(scroll_frame, bg=_COLORS["card_border"], height=1)
            sep.pack(fill=tk.X, padx=15, pady=(15, 5))
            tk.Label(scroll_frame, text="MEJORES TERCEROS (8 CLASIFICAN A 32VOS)",
                     font=_FONT_H, bg=_COLORS["bg"],
                     fg=_COLORS["accent_green"]).pack(pady=(5, 5))

            hdr3 = tk.Frame(scroll_frame, bg=_COLORS["bg"])
            hdr3.pack(fill=tk.X, padx=20)
            for txt, w in [("", 4), ("Equipo", 24), ("Grp", 4), ("Pts", 5), ("GD", 5), ("GF", 5)]:
                tk.Label(hdr3, text=txt, font=_FONT_TAB_H,
                         bg=_COLORS["bg"], fg=_COLORS["subtitle"],
                         width=w, anchor=tk.W).pack(side=tk.LEFT)

            for rank3, (grp, tm, pts3, gd3, gf3) in enumerate(third, 1):
                qualifies = rank3 <= 4
                row_bg = _COLORS["card_bg"] if rank3 % 2 == 0 else _COLORS["bg"]
                row3 = tk.Frame(scroll_frame, bg=row_bg)
                row3.pack(fill=tk.X, padx=20)
                icon = "★" if qualifies else " "
                clr3 = _COLORS["green"] if qualifies else _COLORS["fg"]
                tk.Label(row3, text=icon, font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=3).pack(side=tk.LEFT)
                tflag = self._get_flag(tm, 16, 12)
                if tflag:
                    tk.Label(row3, image=tflag, bg=row_bg).pack(side=tk.LEFT, padx=(0, 3))
                tk.Label(row3, text=team_name_es(tm), font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=24, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(row3, text=grp, font=_FONT_TAB, bg=row_bg,
                         fg=_COLORS["subtitle"], width=4).pack(side=tk.LEFT)
                tk.Label(row3, text=str(pts3), font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=5).pack(side=tk.LEFT)
                tk.Label(row3, text=f"{gd3:+d}", font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=5).pack(side=tk.LEFT)
                tk.Label(row3, text=str(gf3), font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=5).pack(side=tk.LEFT)

    def _compute_third_placed(self, tables):
        third = []
        for g in sorted(tables.keys()):
            teams = tables[g]
            if len(teams) < 3:
                continue
            entry = teams[2]
            if isinstance(entry, dict) and "team" in entry:
                tm = entry["team"]
                pts = entry["pts"]
                gd = entry["gd"]
                gf = entry["gf"]
            elif isinstance(entry, (list, tuple)):
                tm = entry[0]
                d = entry[1]
                pts = d["pts"]
                gd = d["gd"]
                gf = d["gf"]
            else:
                continue
            third.append((g, tm, pts, gd, gf))
        third.sort(key=lambda x: (-x[2], -x[3], -x[4]))
        return third[:8]

    def _build_goleadores_tab(self):
        parent = self._tab_goleadores
        header = tk.Frame(parent, bg=_COLORS["bg"])
        header.pack(fill=tk.X, padx=15, pady=8)
        tk.Label(header, text="TABLA DE GOLEADORES",
                 font=_FONT_H, bg=_COLORS["bg"],
                 fg=_COLORS["accent_green"]).pack(side=tk.LEFT)

        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _on_goals_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_goals_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        scorers = self.data.get("goleadores", [])
        if not scorers:
            tk.Label(scroll_frame, text="No hay datos de goleadores.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return

        hdr = tk.Frame(scroll_frame, bg=_COLORS["card_bg"])
        hdr.pack(fill=tk.X, padx=15, pady=(5, 0))
        for txt, w in [("#", 4), ("Jugador", 30), ("Equipo", 24), ("Goles", 8)]:
            tk.Label(hdr, text=txt, font=_FONT_TAB_H,
                     bg=_COLORS["card_bg"], fg=_COLORS["accent"],
                     width=w, anchor=tk.W).pack(side=tk.LEFT)

        for rank, s in enumerate(scorers, 1):
            player = s.get("player", "?")
            team = s.get("team", "")
            goles = s.get("raw_goals", s.get("goals", 0))
            if goles == 0:
                break
            row = tk.Frame(scroll_frame, bg=_COLORS["card_bg"] if rank % 2 == 0
                           else _COLORS["bg"])
            row.pack(fill=tk.X, padx=15)
            tk.Label(row, text=str(rank), font=_FONT_TAB,
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=4, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=_safe(player), font=_FONT_TAB,
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=30, anchor=tk.W).pack(side=tk.LEFT)
            tflag = self._get_flag(team, 16, 12)
            if tflag:
                tk.Label(row, image=tflag, bg=row["bg"]).pack(side=tk.LEFT, padx=(0, 3))
            tk.Label(row, text=team_name_es(team), font=_FONT_TAB,
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=22, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(goles), font=_FONT_TAB_H,
                     bg=row["bg"], fg=_COLORS["star"],
                     width=8, anchor=tk.W).pack(side=tk.LEFT)

    def _build_jugadores_tab(self):
        parent = self._tab_jugadores
        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _on_jug_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_jug_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        data = self.data.get("jugadores", {})

        header = tk.Frame(scroll_frame, bg=_COLORS["bg"])
        header.pack(fill=tk.X, padx=15, pady=(15, 5))
        tk.Label(header, text="Jugadores destacados (datos reales de Sofascore)",
                 font=("Corbel", 18, "bold"), bg=_COLORS["bg"],
                 fg=_COLORS["accent"]).pack(side=tk.LEFT)

        # ── GOLDEN BALL ────────────────────────────────────────────
        gb_list = data.get("golden_ball", [])
        if gb_list:
            gb = gb_list[0]
            card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                            highlightbackground=_COLORS["star"],
                            highlightthickness=2, padx=12, pady=8)
            card.pack(fill=tk.X, padx=15, pady=6)
            tk.Label(card, text="\U0001F3C6  GOLDEN BALL (mejor promedio de rating)",
                     font=("Corbel", 16, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["star"]).pack(anchor=tk.W)

            gb_team = gb.get("team", "")
            gf = self._get_flag(gb_team, 32, 24)
            gb_vf = tk.Frame(card, bg=_COLORS["card_bg"])
            gb_vf.pack(anchor=tk.W, pady=4)
            if gf:
                tk.Label(gb_vf, image=gf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(gb_vf, text=f"{team_name_es(gb_team)}  |  {gb.get('player_name', '')}",
                     font=("Corbel", 18, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 15))
            tk.Label(gb_vf, text=f"Rating: {gb.get('avg_rating', 0)}",
                     font=("Corbel", 22, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["star"]).pack(side=tk.LEFT)
            tk.Label(card, text=gb.get("highlight", ""),
                     font=("Corbel", 11), bg=_COLORS["card_bg"],
                     fg=_COLORS["subtitle"]).pack(anchor=tk.W)
            tk.Label(card, text=f"{gb.get('matches', 0)} partido(s)  ·  G+A: {gb.get('g_plus_a', 0)}",
                     font=("Corbel", 10), bg=_COLORS["card_bg"],
                     fg=_COLORS["subtitle"]).pack(anchor=tk.W)
        else:
            self._empty_msg(scroll_frame, "Golden Ball", "")

        # ── TOP BY POSITION (2x2 grid) ─────────────────────────────
        top_pos = data.get("top_positions", {})
        if any(top_pos.values()):
            pos_grid = tk.Frame(scroll_frame, bg=_COLORS["bg"])
            pos_grid.pack(fill=tk.X, padx=15, pady=6)
            pos_names = [
                ("\U0001F9E2  ARQUERO", "Arquero", _COLORS["green"]),
                ("\U0001F6E1  DEFENSA", "Defensa", _COLORS["yellow"]),
                ("\u26A1  MEDIOCAMPISTA", "Mediocampista", _COLORS["accent"]),
                ("\U0001F3AF  DELANTERO", "Delantero", _COLORS["red"]),
            ]
            for ci, (title, key, color) in enumerate(pos_names):
                row_idx = ci // 2
                col_idx = ci % 2
                players = top_pos.get(key, [])
                pos_card = tk.Frame(pos_grid, bg=_COLORS["card_bg"],
                                    highlightbackground=_COLORS["card_border"],
                                    highlightthickness=1, padx=8, pady=4)
                pos_card.grid(row=row_idx, column=col_idx, sticky="nsew",
                              padx=3, pady=3)
                pos_grid.columnconfigure(col_idx, weight=1)

                tk.Label(pos_card, text=title, font=("Corbel", 12, "bold"),
                         bg=_COLORS["card_bg"], fg=color).pack(anchor=tk.W)
                if players:
                    for rank, p in enumerate(players, 1):
                        row_f = tk.Frame(pos_card, bg=_COLORS["card_bg"])
                        row_f.pack(fill=tk.X, pady=1)
                        pf = self._get_flag(p.get("team", ""), 14, 10)
                        tk.Label(row_f, text=f"{rank}.", font=_FONT_TAB,
                                 bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                                 width=2).pack(side=tk.LEFT)
                        if pf:
                            tk.Label(row_f, image=pf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 2))
                        tk.Label(row_f, text=_safe(p.get("player_name", "?")),
                                 font=_FONT_TAB, bg=_COLORS["card_bg"],
                                 fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 4))
                        tk.Label(row_f, text=f"★{p.get('avg_rating', 0)}",
                                 font=_FONT_TAB_H, bg=_COLORS["card_bg"],
                                 fg=_COLORS["star"]).pack(side=tk.RIGHT)
                else:
                    tk.Label(pos_card, text="⏳ Sin datos a\u00fan",
                             font=_FONT_M, bg=_COLORS["card_bg"],
                             fg=_COLORS["subtitle"]).pack(anchor=tk.W, pady=4)
        else:
            self._empty_msg(scroll_frame, "Posiciones", "")

        # ── ONCE IDEAL ─────────────────────────────────────────────
        xi = data.get("once_ideal", {})
        if xi.get("gk"):
            xi_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                               highlightbackground=_COLORS["accent"],
                               highlightthickness=2, padx=12, pady=8)
            xi_card.pack(fill=tk.X, padx=15, pady=6)
            tk.Label(xi_card, text="\U0001F451  ONCE IDEAL (mejores ratings por posici\u00f3n)",
                     font=("Corbel", 14, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["accent"]).pack(anchor=tk.W)

            def _xi_row(label, entry):
                if not entry:
                    return
                rf = tk.Frame(xi_card, bg=_COLORS["card_bg"])
                rf.pack(fill=tk.X, pady=1)
                tk.Label(rf, text=f"  {label}  ", font=_FONT_TAB_H,
                         bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
                xf = self._get_flag(entry.get("team", ""), 14, 10)
                if xf:
                    tk.Label(rf, image=xf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 2))
                hl = entry.get("highlight", "")
                detail = f"{entry.get('player_name', '')} \u2605{entry.get('avg_rating', 0)}"
                if hl:
                    detail += f"  |  {hl}"
                tk.Label(rf, text=detail, font=_FONT_M,
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT)

            _xi_row("\U0001F9E2 GK", xi.get("gk"))
            def_names = [d.get("player_name", "?") for d in xi.get("def", [])]
            _xi_row("\U0001F6E1 DEF", {"player_name": ", ".join(def_names), "team": "", "avg_rating": "", "highlight": ""})
            mid_names = [m.get("player_name", "?") for m in xi.get("mid", [])]
            _xi_row("\u26A1 MID", {"player_name": ", ".join(mid_names), "team": "", "avg_rating": "", "highlight": ""})
            fw_names = [f.get("player_name", "?") for f in xi.get("fw", [])]
            _xi_row("\U0001F3AF FW", {"player_name": ", ".join(fw_names), "team": "", "avg_rating": "", "highlight": ""})
        else:
            self._empty_msg(scroll_frame, "Once Ideal", "")

        # ── MEJORES POR FASE ───────────────────────────────────────
        fases = data.get("mejores_por_fase", [])
        if fases:
            fs_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                               highlightbackground=_COLORS["card_border"],
                               highlightthickness=1, padx=12, pady=8)
            fs_card.pack(fill=tk.X, padx=15, pady=6)
            tk.Label(fs_card, text="\U0001F4C5  Mejores por fase",
                     font=("Corbel", 14, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["green"]).pack(anchor=tk.W)
            for f in fases:
                ff = tk.Frame(fs_card, bg=_COLORS["card_bg"])
                ff.pack(fill=tk.X, pady=2)
                mid = f.get("match_id", "?")
                ta = f.get("team_a", "")
                tb = f.get("team_b", "")
                sa = f.get("score_a", 0)
                sb = f.get("score_b", 0)
                player = f.get("player_name", "?")
                pteam = f.get("team", "")
                rating = f.get("rating", 0)
                hl = f.get("highlight", "")
                pf = self._get_flag(pteam, 14, 10)
                tk.Label(ff, text=f"  {mid}  {team_name_es(ta)} {sa}-{sb} {team_name_es(tb)}",
                         font=_FONT_TAB, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
                if pf:
                    tk.Label(ff, image=pf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(3, 2))
                tk.Label(ff, text=f"MVP: {player} \u2605{rating}",
                         font=_FONT_TAB_H, bg=_COLORS["card_bg"],
                         fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(4, 0))
                if hl:
                    tk.Label(ff, text=f"  |  {hl}", font=_FONT_TAB,
                             bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
        else:
            self._empty_msg(scroll_frame, "Mejores por fase", "")

        # ── MVP POR PARTIDO ────────────────────────────────────────
        mvps = data.get("mvp_por_partido", [])
        if mvps:
            mvp_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                                highlightbackground=_COLORS["card_border"],
                                highlightthickness=1, padx=12, pady=8)
            mvp_card.pack(fill=tk.X, padx=15, pady=6)
            tk.Label(mvp_card, text="\U0001F3C6  MVP por partido",
                     font=("Corbel", 14, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["accent"]).pack(anchor=tk.W)
            for m in mvps:
                mf = tk.Frame(mvp_card, bg=_COLORS["card_bg"])
                mf.pack(fill=tk.X, pady=2)
                mid = m.get("match_id", "?")
                player = m.get("player_name", "?")
                pteam = m.get("team", "")
                rating = m.get("rating", 0)
                hl = m.get("highlight", "")
                ta = m.get("team_a", "")
                tb = m.get("team_b", "")
                sa = m.get("score_a", 0)
                sb = m.get("score_b", 0)
                pf = self._get_flag(pteam, 14, 10)
                tk.Label(mf, text=f"  {mid}  {team_name_es(ta)} {sa}-{sb} {team_name_es(tb)}",
                         font=_FONT_TAB, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
                if pf:
                    tk.Label(mf, image=pf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(3, 2))
                tk.Label(mf, text=f"{player} \u2605{rating}",
                         font=_FONT_TAB_H, bg=_COLORS["card_bg"],
                         fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(4, 0))
                if hl:
                    tk.Label(mf, text=f"  |  {hl}", font=_FONT_TAB,
                             bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
        else:
            self._empty_msg(scroll_frame, "MVP por partido", "")

        # ── GOLEADORES REALES + ASISTIDORES REALES ──────────────────
        scorers = data.get("goleadores_reales", [])
        assisters = data.get("asistidores_reales", [])
        if scorers or assisters:
            stats_frame = tk.Frame(scroll_frame, bg=_COLORS["bg"])
            stats_frame.pack(fill=tk.X, padx=15, pady=6)

            # Goleadores
            g_frame = tk.Frame(stats_frame, bg=_COLORS["card_bg"],
                               highlightbackground=_COLORS["card_border"],
                               highlightthickness=1, padx=10, pady=6)
            g_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
            tk.Label(g_frame, text="\u26BD  Goleadores reales",
                     font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["star"]).pack(anchor=tk.W)
            if scorers:
                for rank, s in enumerate(scorers, 1):
                    sf = tk.Frame(g_frame, bg=_COLORS["card_bg"])
                    sf.pack(fill=tk.X, pady=1)
                    sf_flag = self._get_flag(s.get("team", ""), 14, 10)
                    tk.Label(sf, text=f"  {rank}.", font=_FONT_TAB,
                             bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                             width=3).pack(side=tk.LEFT)
                    if sf_flag:
                        tk.Label(sf, image=sf_flag, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 2))
                    tk.Label(sf, text=_safe(s.get("player_name", "?")),
                             font=_FONT_TAB, bg=_COLORS["card_bg"],
                             fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 4))
                    tk.Label(sf, text=f"{s.get('total_goals', 0)} goles",
                             font=_FONT_TAB_H, bg=_COLORS["card_bg"],
                             fg=_COLORS["star"]).pack(side=tk.RIGHT)
            else:
                tk.Label(g_frame, text="⏳ Sin datos a\u00fan",
                         font=_FONT_M, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(anchor=tk.W, pady=4)

            # Asistidores
            a_frame = tk.Frame(stats_frame, bg=_COLORS["card_bg"],
                               highlightbackground=_COLORS["card_border"],
                               highlightthickness=1, padx=10, pady=6)
            a_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(3, 0))
            tk.Label(a_frame, text="\U0001F9E1  Asistidores reales",
                     font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["accent"]).pack(anchor=tk.W)
            if assisters:
                for rank, a in enumerate(assisters, 1):
                    af = tk.Frame(a_frame, bg=_COLORS["card_bg"])
                    af.pack(fill=tk.X, pady=1)
                    af_flag = self._get_flag(a.get("team", ""), 14, 10)
                    tk.Label(af, text=f"  {rank}.", font=_FONT_TAB,
                             bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                             width=3).pack(side=tk.LEFT)
                    if af_flag:
                        tk.Label(af, image=af_flag, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 2))
                    tk.Label(af, text=_safe(a.get("player_name", "?")),
                             font=_FONT_TAB, bg=_COLORS["card_bg"],
                             fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 4))
                    tk.Label(af, text=f"{a.get('total_assists', 0)} asistencias",
                             font=_FONT_TAB_H, bg=_COLORS["card_bg"],
                             fg=_COLORS["accent"]).pack(side=tk.RIGHT)
            else:
                tk.Label(a_frame, text="⏳ Sin datos a\u00fan",
                         font=_FONT_M, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(anchor=tk.W, pady=4)
        else:
            self._empty_msg(scroll_frame, "Goleadores/Asistidores", "")

    def _empty_msg(self, parent, title, _unused):
        card = tk.Frame(parent, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=1, padx=12, pady=8)
        card.pack(fill=tk.X, padx=15, pady=6)
        tk.Label(card, text=f"{title}",
                 font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).pack(anchor=tk.W)
        tk.Label(card, text="\u23F3 Sin datos a\u00fan",
                 font=("Corbel", 11), bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).pack(anchor=tk.W, pady=4)

    def _compute_bonus_data(self):
        ko = self.data.get("knockout", [])
        groups = self.data.get("groups", [])
        scorers = self.data.get("goleadores", [])
        tables = self.data.get("tables", {})
        bonus = {}

        if ko:
            final = ko[-1]
            bonus["champion"] = final.get("winner", "?")
            bonus["champion_conf"] = final.get("confidence", 0)
            bonus["runner_up"] = final.get("loser", "?")
            bonus["final_score"] = f"{final.get('score_a', 0)}-{final.get('score_b', 0)}"
            if len(ko) >= 2:
                third = ko[-2]
                bonus["third_place"] = third.get("winner", "?")
                bonus["third_score"] = f"{third.get('score_a', 0)}-{third.get('score_b', 0)}"
            if len(ko) >= 30:
                sf1 = ko[28]
                sf2 = ko[29]
                bonus["semifinalists"] = [
                    sf1.get("team_a", "?"), sf1.get("team_b", "?"),
                    sf2.get("team_a", "?"), sf2.get("team_b", "?"),
                ]

        if scorers:
            ts = scorers[0]
            bonus["top_scorer"] = ts.get("player", "?")
            bonus["top_scorer_team"] = ts.get("team", "")
            bonus["top_scorer_goals"] = ts.get("raw_goals", ts.get("goals", 0))

        if tables:
            classified = {}
            for g in sorted(tables.keys()):
                teams = tables[g]
                top2 = []
                for rank, entry in enumerate(teams, 1):
                    if rank > 2:
                        break
                    if isinstance(entry, dict) and "team" in entry:
                        top2.append(entry["team"])
                    elif isinstance(entry, (list, tuple)):
                        top2.append(entry[0])
                if top2:
                    classified[g] = top2
            bonus["classified"] = classified

        all_matches = groups + ko
        gs = {}
        gc = {}
        max_total = 0
        best_match = {}
        for m in all_matches:
            a = m.get("team_a", "?")
            b = m.get("team_b", "?")
            sa = m.get("score_a", 0)
            sb = m.get("score_b", 0)
            gs[a] = gs.get(a, 0) + sa
            gs[b] = gs.get(b, 0) + sb
            gc[a] = gc.get(a, 0) + sb
            gc[b] = gc.get(b, 0) + sa
            total = sa + sb
            if total > max_total:
                max_total = total
                best_match = {"teams": f"{a} vs {b}", "score": f"{sa}-{sb}", "goals": total}

        if gs:
            bonus["most_goals_team"] = max(gs, key=lambda k: gs[k])
            bonus["most_goals_total"] = gs[bonus["most_goals_team"]]
        if gc:
            bonus["best_defense"] = min(gc, key=lambda k: gc[k])
            bonus["best_defense_ga"] = gc[bonus["best_defense"]]
        if best_match:
            bonus["best_match"] = best_match

        return bonus

    def _bonus_card(self, parent, title, value, detail, color, flag_team=None):
        card = tk.Frame(parent, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=1, relief=tk.FLAT)
        card.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(card, text=title, font=("Corbel", 13, "bold"),
                 bg=_COLORS["card_bg"], fg=color).pack(anchor=tk.W, padx=15, pady=(8, 0))

        vf = tk.Frame(card, bg=_COLORS["card_bg"])
        vf.pack(anchor=tk.W, padx=15, pady=2)
        if flag_team:
            bf = self._get_flag(flag_team, 24, 18)
            if bf:
                tk.Label(vf, image=bf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(vf, text=value, font=("Corbel", 17, "bold"),
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT)

        tk.Label(card, text=detail, font=_FONT_M,
                 bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(anchor=tk.W, padx=15, pady=(0, 8))

    def _build_bonus_tab(self):
        parent = self._tab_bonus
        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _on_bonus_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_bonus_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        bonus = self._compute_bonus_data()

        tk.Label(scroll_frame, text="PREDICCIONES BONUS",
                 font=_FONT_H, bg=_COLORS["bg"],
                 fg=_COLORS["accent_green"]).pack(pady=(20, 5))

        # Scoring rules
        rules_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                              highlightbackground=_COLORS["card_border"],
                              highlightthickness=1, relief=tk.FLAT)
        rules_card.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(rules_card, text="Sistema de Puntuacion",
                 font=("Corbel", 14, "bold"), bg=_COLORS["card_bg"],
                 fg=_COLORS["star"]).pack(anchor=tk.W, padx=15, pady=(8, 2))
        rules_text = (
            "Por partido:\n"
            "  ●  3 pts  - Resultado exacto\n"
            "  ●  1 pt   - Resultado acertado (ganador o empate)\n"
            "  ●  0 pts  - No acertaste\n\n"
            "Predicciones Bonus:\n"
            "  ●  Campeon: ? pts\n"
            "  ●  Goleador: ? pts\n"
            "  ●  Cada clasificado de grupo: 1 pt\n"
            "  ●  Cada semifinalista correcto: 1 pt"
        )
        tk.Label(rules_card, text=rules_text, font=_FONT_M,
                 bg=_COLORS["card_bg"],
                 fg=_COLORS["fg"], justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 8))

        # Champion, runner-up, third place
        items = [
            ("\U0001F3C6  Campeon", team_name_es(bonus.get("champion", "?")),
             f"Confianza: {bonus.get('champion_conf', 0):.0f}%",
             _COLORS["star"]),
            ("\U0001F948  Subcampeon", team_name_es(bonus.get("runner_up", "?")),
             f"Final: {bonus.get('final_score', '')}",
             _COLORS["subtitle"]),
            ("\U0001F949  Tercer Puesto", team_name_es(bonus.get("third_place", "?")),
             f"3er puesto: {bonus.get('third_score', '')}",
             _COLORS["subtitle"]),
        ]
        for label, value, detail, color in items:
            self._bonus_card(scroll_frame, label, str(value), detail, color)

        # Top scorer
        ts = bonus.get("top_scorer", "")
        if ts:
            ts_team = bonus.get("top_scorer_team", "")
            ts_goals = bonus.get("top_scorer_goals", 0)
            self._bonus_card(scroll_frame, "⚽  Goleador",
                             f"{ts} ({ts_team})",
                             f"Goles: {ts_goals}",
                             _COLORS["yellow"], flag_team=ts_team)

        # 4 Semifinalists
        sfs = bonus.get("semifinalists", [])
        if sfs:
            sf_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                               highlightbackground=_COLORS["card_border"],
                               highlightthickness=1, relief=tk.FLAT)
            sf_card.pack(fill=tk.X, padx=20, pady=6)
            tk.Label(sf_card, text="\U0001F3C6  4 Semifinalistas",
                     font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["green"]).pack(anchor=tk.W, padx=15, pady=(8, 0))
            sf_vf = tk.Frame(sf_card, bg=_COLORS["card_bg"])
            sf_vf.pack(anchor=tk.W, padx=15, pady=2)
            for i, sf_t in enumerate(sfs):
                if i > 0:
                    tk.Label(sf_vf, text="  |  ", font=("Corbel", 17, "bold"),
                             bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT)
                sf_flag = self._get_flag(sf_t, 24, 18)
                if sf_flag:
                    tk.Label(sf_vf, image=sf_flag, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 4))
                tk.Label(sf_vf, text=team_name_es(sf_t), font=("Corbel", 17, "bold"),
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT)
            tk.Label(sf_card, text="1 pt por cada acierto", font=_FONT_M,
                     bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(anchor=tk.W, padx=15, pady=(0, 8))

        # Classified per group
        classified = bonus.get("classified", {})
        if classified:
            card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                             highlightbackground=_COLORS["card_border"],
                             highlightthickness=1, relief=tk.FLAT)
            card.pack(fill=tk.X, padx=20, pady=6)
            tk.Label(card, text="Clasificados por Grupo",
                     font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["green"]).pack(anchor=tk.W, padx=15, pady=(8, 2))
            for g in sorted(classified.keys()):
                t1, t2 = classified[g]
                c_line = tk.Frame(card, bg=_COLORS["card_bg"])
                c_line.pack(anchor=tk.W, padx=15, pady=1)
                tk.Label(c_line, text=f"  {g}:  ", font=_FONT_M,
                         bg=_COLORS["card_bg"], fg=_COLORS["subtitle"]).pack(side=tk.LEFT)
                for ct in (t1, t2):
                    cf = self._get_flag(ct, 16, 12)
                    if cf:
                        tk.Label(c_line, image=cf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(2, 3))
                    tk.Label(c_line, text=team_name_es(ct), font=_FONT_M,
                             bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 8))

        # x2 recommendations
        try:
            from prode_mundial.optimizer import analyze_x2
            x2_data = analyze_x2(group_predictions=self.data["groups"])
            if x2_data:
                x2_card = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                                    highlightbackground=_COLORS["card_border"],
                                    highlightthickness=1, relief=tk.FLAT)
                x2_card.pack(fill=tk.X, padx=20, pady=6)
                tk.Label(x2_card, text="Multiplicador x2 - Top 3 Recomendados",
                         font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                         fg=_COLORS["accent"]).pack(anchor=tk.W, padx=15, pady=(8, 2))
                tk.Label(x2_card,
                         text="Poner x2 hasta en 3 partidos. Si acertas, duplica los puntos (3→6, 1→4).",
                         font=_FONT_S, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(anchor=tk.W, padx=15, pady=(0, 2))
                for i, r in enumerate(x2_data[:3], 1):
                    x2_line = tk.Frame(x2_card, bg=_COLORS["card_bg"])
                    x2_line.pack(fill=tk.X, padx=15, pady=2)
                    tk.Label(x2_line, text=f"  {i}.  ", font=_FONT_M,
                             bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT)
                    for x2t in (r["team_a"], r["team_b"]):
                        xf = self._get_flag(x2t, 16, 12)
                        if xf:
                            tk.Label(x2_line, image=xf, bg=_COLORS["card_bg"]).pack(side=tk.LEFT, padx=(0, 3))
                    tk.Label(x2_line, text=f"{team_name_es(r['team_a'])} vs {team_name_es(r['team_b'])}  |  "
                             f"Pronostico: {r['predicted']}  |  "
                             f"P(acierto): {r['p_result_pct']:.0f}%  |  "
                             f"EV gain: +{r['ev_gain']:.3f}",
                             font=_FONT_M, bg=_COLORS["card_bg"],
                             fg=_COLORS["fg"], anchor=tk.W).pack(side=tk.LEFT, padx=(4, 0))
        except Exception:
            pass

        # Extra stats
        mt = bonus.get("most_goals_team", "")
        if mt:
            self._bonus_card(scroll_frame, "\U0001F525  Equipo con mas goles",
                             team_name_es(mt),
                             f"Total: {bonus.get('most_goals_total', 0)} goles",
                             _COLORS["green"], flag_team=mt)
        bd = bonus.get("best_defense", "")
        if bd:
            self._bonus_card(scroll_frame, "\U0001F6E1  Mejor defensa",
                             team_name_es(bd),
                             f"Solo {bonus.get('best_defense_ga', 0)} goles recibidos",
                             _COLORS["green"], flag_team=bd)
        bm = bonus.get("best_match", {})
        if bm:
            self._bonus_card(scroll_frame, "\U0001F4A5  Partido con mas goles",
                             f"{bm.get('teams', '')}",
                             f"{bm.get('score', '')} ({bm.get('goals', 0)} goles)",
                             _COLORS["accent"])

    def _build_info_tab(self):
        parent = self._tab_info
        text = tk.Text(parent, wrap=tk.WORD, bg=_COLORS["card_bg"],
                       fg=_COLORS["fg"], font=("Corbel", 12),
                       relief=tk.FLAT, bd=0, highlightthickness=0,
                       padx=25, pady=20, spacing1=6, spacing2=3)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.tag_configure("title", font=("Bebas Neue" if _FONTS_OK else "Corbel", 20), foreground=_COLORS["accent"],
                           spacing1=10, spacing3=15)
        text.tag_configure("subtitle", font=("Corbel", 15, "bold"), foreground=_COLORS["accent2"],
                           spacing1=15, spacing3=8)
        text.tag_configure("bold", font=("Corbel", 12, "bold"), foreground=_COLORS["fg"])
        text.tag_configure("normal", font=("Corbel", 12), foreground=_COLORS["fg"])
        text.tag_configure("disclaimer_title", font=("Corbel", 14, "bold"),
                           foreground=_COLORS["accent"], spacing1=20, spacing3=8)
        text.tag_configure("disclaimer", font=("Corbel", 12, "italic"),
                           foreground=_COLORS["subtitle"], spacing1=4, spacing3=4)
        text.tag_configure("footer", font=("Corbel", 10), foreground=_COLORS["subtitle"],
                           spacing1=15, spacing3=5)
        text.insert(tk.END, "¿Cómo funciona este sistema de predicciones?\n", "title")
        text.insert(tk.END, "\n")
        text.insert(tk.END, "Este sistema analiza los 135 partidos del Mundial 2026 y te ayuda a completar tu PRODE. No es magia: es ", "normal")
        text.insert(tk.END, "matemática aplicada al fútbol", "bold")
        text.insert(tk.END, ", alimentada con datos reales de los ", "normal")
        text.insert(tk.END, "1248 jugadores", "bold")
        text.insert(tk.END, " que disputan el torneo.\n\n", "normal")
        text.insert(tk.END, "La recolección de datos\n", "subtitle")
        text.insert(tk.END, "Primero se armó una base de datos con los 1248 jugadores de las 48 selecciones. Para eso se usaron tres fuentes: ", "normal")
        text.insert(tk.END, "Promiedos", "bold")
        text.insert(tk.END, ", ", "normal")
        text.insert(tk.END, "Transfermarkt", "bold")
        text.insert(tk.END, " y ", "normal")
        text.insert(tk.END, "Wikipedia", "bold")
        text.insert(tk.END, ". De cada jugador se obtuvo su nombre, edad, altura, posición, club actual y valor de mercado. Pero no quedó ahí: de Wikipedia se extrajeron los partidos y goles internacionales de cada uno, su club actual, sus títulos profesionales y su altura exacta. De Transfermarkt se consiguieron las estadísticas de la temporada 2025/26: ", "normal")
        text.insert(tk.END, "goles, asistencias y minutos jugados", "bold")
        text.insert(tk.END, ". En total se recolectaron datos de los 1248 jugadores con estadísticas de temporada completas, lo que da una cobertura del 100% del torneo.\n\n", "normal")
        text.insert(tk.END, "Después se cargó la ", "normal")
        text.insert(tk.END, "historia de cada selección en los Mundiales", "bold")
        text.insert(tk.END, ": qué equipo fue campeón, cuál llegó a final, a semifinales, a cuartos. Brasil con cinco títulos, Alemania con cuatro, Argentina con tres, Francia con dos, Uruguay con dos, Inglaterra con uno y España con uno. También se registraron las ", "normal")
        text.insert(tk.END, "16 sedes del torneo", "bold")
        text.insert(tk.END, ": estadios repartidos entre Estados Unidos, México y Canadá, desde el Azteca a 2240 metros de altura hasta el BC Place de Vancouver con techo cerrado. Se anotaron las ", "normal")
        text.insert(tk.END, "bases operativas", "bold")
        text.insert(tk.END, " de cada selección, porque no es lo mismo dormir en Kansas City que en Cancún. Y se cargaron ", "normal")
        text.insert(tk.END, "57 partidos amistosos", "bold")
        text.insert(tk.END, " que se jugaron entre mayo y junio de 2026 para medir la preparación de cada equipo.\n\n", "normal")
        text.insert(tk.END, "Los diecinueve factores\n", "subtitle")
        text.insert(tk.END, "Cada partido se analiza con ", "normal")
        text.insert(tk.END, "diecinueve factores distintos", "bold")
        text.insert(tk.END, ". Cada factor tiene un peso que indica qué tanto influye en el resultado final. Te los cuento:\n\n", "normal")
        text.insert(tk.END, "El factor más importante es la ", "normal")
        text.insert(tk.END, "fuerza del equipo", "bold")
        text.insert(tk.END, ", que mira el ranking FIFA y el tier en el que está clasificada cada selección. Pesa un 15%. Le siguen las ", "normal")
        text.insert(tk.END, "estadísticas individuales", "bold")
        text.insert(tk.END, " de los jugadores: goles y asistencias de la temporada, con un 11%. Después viene el ", "normal")
        text.insert(tk.END, "valor de mercado", "bold")
        text.insert(tk.END, " de la plantilla, porque un equipo lleno de jugadores de Manchester City, Real Madrid y Bayern suele ser mejor que uno con jugadores de ligas chicas. Eso pesa un 10%.\n\n", "normal")
        text.insert(tk.END, "La ", "normal")
        text.insert(tk.END, "experiencia internacional", "bold")
        text.insert(tk.END, " de los jugadores (los partidos que jugaron con su selección) pesa un 6%. La ", "normal")
        text.insert(tk.END, "localía", "bold")
        text.insert(tk.END, " también pesa 6%, pero solo cuando el equipo juega cerca de su país o tiene mucha diáspora en Estados Unidos. Los ", "normal")
        text.insert(tk.END, "días de descanso", "bold")
        text.insert(tk.END, " entre partidos pesan otro 6%: jugar cada tres días desgasta. La ", "normal")
        text.insert(tk.END, "profundidad del banco", "bold")
        text.insert(tk.END, " de suplentes pesa 6% también, porque en un Mundial se hacen cinco cambios por partido.\n\n", "normal")
        text.insert(tk.END, "El ", "normal")
        text.insert(tk.END, "clima", "bold")
        text.insert(tk.END, " pesa 5%: no es lo mismo jugar en el calor de Monterrey a 37 grados que en el techo cerrado de Dallas. El ", "normal")
        text.insert(tk.END, "porcentaje de jugadores en el extranjero", "bold")
        text.insert(tk.END, " pesa 2%. Los ", "normal")
        text.insert(tk.END, "kilómetros acumulados", "bold")
        text.insert(tk.END, " viajando entre sedes pesan 4%. La ", "normal")
        text.insert(tk.END, "historia mundialista", "bold")
        text.insert(tk.END, " de cada selección pesa 3%. La ", "normal")
        text.insert(tk.END, "moral del equipo", "bold")
        text.insert(tk.END, " (si viene ganando o perdiendo) pesa 1%. La ", "normal")
        text.insert(tk.END, "preparación en amistosos", "bold")
        text.insert(tk.END, " previos pesa otro 2%.\n\n", "normal")
        text.insert(tk.END, "La cantidad de ", "normal")
        text.insert(tk.END, "títulos", "bold")
        text.insert(tk.END, " que tienen los jugadores en sus carreras pesa 4%. Las ", "normal")
        text.insert(tk.END, "cuotas de las casas de apuestas", "bold")
        text.insert(tk.END, " antes del torneo pesan 2%. La ", "normal")
        text.insert(tk.END, "altura promedio", "bold")
        text.insert(tk.END, " del equipo (ventaja en pelotas paradas) pesa 3%. La ", "normal")
        text.insert(tk.END, "química entre jugadores", "bold")
        text.insert(tk.END, " que comparten club pesa 3%. La ", "normal")
        text.insert(tk.END, "distancia al estadio", "bold")
        text.insert(tk.END, " desde la base operativa pesa 2%. Y por último, la ", "normal")
        text.insert(tk.END, "presión del partido", "bold")
        text.insert(tk.END, ": si un equipo ya está clasificado, si necesita ganar o si ya está eliminado. Eso pesa 4% y solo aplica en la tercera fecha de la fase de grupos.\n\n", "normal")
        text.insert(tk.END, "Y por último, la ", "normal")
        text.insert(tk.END, "forma real en el torneo", "bold")
        text.insert(tk.END, ": si un equipo ya jugó su primer partido, el resultado real (más los goles, la posesión, los tiros, etc.) se incorpora al modelo con un peso del 5%. Esto permite que las predicciones se ajusten a lo que realmente pasó en la cancha.\n\n", "normal")
        text.insert(tk.END, "Cómo se calcula el resultado\n", "subtitle")
        text.insert(tk.END, "Con esos diecinueve factores se calcula una diferencia total entre los dos equipos. Esa diferencia se aplica sobre los goles que cada equipo suele hacer y recibir. Si el equipo A anota en promedio 2 goles por partido y el equipo B recibe 1, el promedio base es 1.5. Después se ajusta para arriba o para abajo según los factores.\n\n", "normal")
        text.insert(tk.END, "Con ese promedio de goles esperados se usa la ", "normal")
        text.insert(tk.END, "distribución de Poisson", "bold")
        text.insert(tk.END, ", que es una fórmula matemática que calcula la probabilidad de cada resultado posible: 0-0, 1-0, 1-1, 2-0, y así hasta 15-15. Además se aplica una corrección llamada ", "normal")
        text.insert(tk.END, "Dixon-Coles", "bold")
        text.insert(tk.END, ", que ajusta las probabilidades de los resultados más comunes: aumenta la chance de 0-0 y 1-1, y reduce la de 1-0 y 0-1, porque en el fútbol real los empates son más frecuentes de lo que dice la Poisson sola.\n\n", "normal")
        text.insert(tk.END, "Cada partido se ", "normal")
        text.insert(tk.END, "simula 1500 veces", "bold")
        text.insert(tk.END, ". De esas 1500 simulaciones se saca el promedio de goles de cada equipo, y ese es el resultado final. Las probabilidades de que gane cada equipo son el porcentaje de simulaciones que ganó cada uno.\n\n", "normal")
        text.insert(tk.END, "El torneo completo\n", "subtitle")
        text.insert(tk.END, "Se simulan los 72 partidos de la fase de grupos. Después se arma la tabla de cada grupo con los puntos, y si hay empate se aplican los criterios de desempate de la FIFA: primero el que ganó el partido entre ellos, después la diferencia de gol entre ellos, después los goles entre ellos, después la diferencia de gol general, después los goles generales, después el ", "normal")
        text.insert(tk.END, "Fair Play", "bold")
        text.insert(tk.END, " (tarjetas amarillas y rojas), y por último el ranking FIFA.\n\n", "normal")
        text.insert(tk.END, "Se clasifican los dos primeros de cada grupo y los ocho mejores terceros. Con esos 32 equipos se arma el bracket de octavos de final, después cuartos, semifinales, el partido por el tercer puesto y la final. En las eliminatorias no hay empate: si el modelo da empate después de 1500 simulaciones, se define por ranking FIFA.\n\n", "normal")
        text.insert(tk.END, "Los goleadores\n", "subtitle")
        text.insert(tk.END, "Los goles de cada equipo se distribuyen entre sus jugadores usando una fórmula que premia a las estrellas. El que mete más goles en su equipo tiene más chances de llevarse la Bota de Oro. Además reciben un plus los ", "normal")
        text.insert(tk.END, "pateadores de penales", "bold")
        text.insert(tk.END, " (porque los penales son goles casi seguros), los que juegan en clubes de las ", "normal")
        text.insert(tk.END, "cinco grandes ligas", "bold")
        text.insert(tk.END, " (Premier League, La Liga, Serie A, Bundesliga, Ligue 1), y los que hicieron ", "normal")
        text.insert(tk.END, "goles en amistosos", "bold")
        text.insert(tk.END, " previos al Mundial. Todo esto sin castigar a los que juegan en ligas menores como la MLS o la liga saudí.\n\n", "normal")
        text.insert(tk.END, "El análisis narrativo\n", "subtitle")
        text.insert(tk.END, "Cada partido incluye un texto pensado para ayudarte a llenar tu PRODE. Tiene tres partes: una ", "normal")
        text.insert(tk.END, "recomendación", "bold")
        text.insert(tk.END, " en una línea (Local seguro, Favorito con cautela, Sorpresa posible, etc.), un ", "normal")
        text.insert(tk.END, "análisis", "bold")
        text.insert(tk.END, " del partido con las cartas bajo la manga de cada equipo, y un ", "normal")
        text.insert(tk.END, "veredicto", "bold")
        text.insert(tk.END, " con el ganador esperado, el riesgo de empate y la confianza del modelo.\n\n", "normal")
        text.insert(tk.END, "Una última cosa\n", "subtitle")
        text.insert(tk.END, "Todo esto corre ", "normal")
        text.insert(tk.END, "completamente offline", "bold")
        text.insert(tk.END, ". No depende de internet, no usa APIs externas. Y el modelo es ", "normal")
        text.insert(tk.END, "determinista", "bold")
        text.insert(tk.END, ": con los mismos datos, siempre da el mismo resultado. No hay suerte, no hay random: la pelota no entra por casualidad.\n\n", "normal")
        text.insert(tk.END, "Datos reales del torneo\n", "subtitle")
        text.insert(tk.END, "A medida que avanza el Mundial se cargan los ", "normal")
        text.insert(tk.END, "resultados reales", "bold")
        text.insert(tk.END, " de los partidos ya jugados. Actualmente hay ", "normal")
        text.insert(tk.END, "4 partidos cargados", "bold")
        text.insert(tk.END, " (Mexico vs Sudafrica, Corea del Sur vs Republica Checa, Canada vs Bosnia y Herzegovina, Estados Unidos vs Paraguay) con estadisticas detalladas de Sofascore: goles esperados, posecion, tiros, pases, duelos, tarjetas y mas.\n\n", "normal")
        text.insert(tk.END, "Estos datos no solo alimentan la ", "normal")
        text.insert(tk.END, "narrativa post-partido", "bold")
        text.insert(tk.END, " que ves en la pestana Grupos, sino que tambien alimentan la ", "normal")
        text.insert(tk.END, "base de datos de jugadores", "bold")
        text.insert(tk.END, " (SQLite). En la pestana ", "normal")
        text.insert(tk.END, "Jugadores", "bold")
        text.insert(tk.END, " podes ver:\n\n", "normal")
        text.insert(tk.END, "  \u2022  ", "normal")
        text.insert(tk.END, "Golden Ball", "bold")
        text.insert(tk.END, ": el jugador con mejor promedio de rating del torneo\n", "normal")
        text.insert(tk.END, "  \u2022  ", "normal")
        text.insert(tk.END, "Top por posicion", "bold")
        text.insert(tk.END, ": los 5 mejores Arquero, Defensa, Mediocampista y Delantero\n", "normal")
        text.insert(tk.END, "  \u2022  ", "normal")
        text.insert(tk.END, "Once Ideal", "bold")
        text.insert(tk.END, ": el mejor equipo con los ratings mas altos por posicion\n", "normal")
        text.insert(tk.END, "  \u2022  ", "normal")
        text.insert(tk.END, "MVP por partido", "bold")
        text.insert(tk.END, ": el jugador destacado de cada encuentro\n", "normal")
        text.insert(tk.END, "  \u2022  ", "normal")
        text.insert(tk.END, "Goleadores y Asistidores reales", "bold")
        text.insert(tk.END, ": los que metieron goles y dieron asistencias\n\n", "normal")
        text.insert(tk.END, "La base de datos se actualiza automaticamente cada vez que se agrega un nuevo resultado real. Tambien podes editarla manualmente abriendo ", "normal")
        text.insert(tk.END, "output/db_ratings.db", "bold")
        text.insert(tk.END, " con DB Browser for SQLite.\n\n", "normal")
        text.insert(tk.END, "ADVERTENCIA\n", "disclaimer_title")
        text.insert(tk.END, "Este proyecto es meramente informativo y fue realizado por hobby, con amor al fútbol y a los datos. Los resultados son simulaciones basadas en estadísticas, no profecías. En el fútbol puede pasar cualquier cosa, por eso es el deporte más lindo del mundo.\n\n", "disclaimer")
        text.insert(tk.END, "Úsalo bajo tu propio riesgo. No nos hacemos responsables si Argentina no sale campeón, si tu cuñado te gana el prode o si Messi te clava un 0-0 en la final.\n\n", "disclaimer")
        text.insert(tk.END, "Disfruta el Mundial 2026.\n\n", "disclaimer")
        text.insert(tk.END, "Desarrollado por Lucas Congil Hadla.\n", "footer")
        text.config(state=tk.DISABLED)

    # unused idx key kept for compatibility
    _idx = {"groups": 0, "knockout": 0}


def main():
    root = tk.Tk()
    root.withdraw()
    from prode_mundial.splash import SplashScreen
    splash = SplashScreen(root)

    sim_data = {}

    def _run_simulation():
        try:
            import prode_mundial.bracket as _pmb
            import prode_mundial.top_scorer as _pmt
            import prode_mundial.output as _pmo
            import prode_mundial.real_results as _pmr
            import prode_mundial.data as _pmd
            import prode_mundial.player_ratings as _pmpr
            _rr_path = os.path.join(OUTPUT_DIR, "real_results.json")
            _real_results = _pmr.load_real_results(_rr_path) if os.path.exists(_rr_path) else None
            _apr = {}
            _atr = {}
            try:
                _pmpr.PLAYER_RATINGS_DB.seed_if_empty()
                for _t in _pmd.TEAMS:
                    _a = _pmpr.PLAYER_RATINGS_DB.get_team_avg_ratings(_t)
                    if _a:
                        _apr[_t] = _a
                    _r = _pmpr.PLAYER_RATINGS_DB.get_team_avg_team_rating(_t)
                    if _r != 0.0:
                        _atr[_t] = _r
            except ImportError:
                pass
            gp, gr, kp = _pmb.run_full_simulation(quiet=True, real_results=_real_results,
                                                   avg_player_ratings=_apr, avg_team_ratings=_atr)
            scorers, _ = _pmt.compute_top_scorers(gp, kp, top_n=20)
            goleadores_list = [{"player": p, "team": t, "goals": g} for p, t, g in scorers]
            _pmo.export_all(gp, gr, kp)
            grps = load_json("fase_grupos.json") or gp or []
            kno = load_json("eliminatorias.json") or kp or []
            sim_data["pre_data"] = {
                "groups": grps,
                "knockout": kno,
                "tables": gr,
                "goleadores": goleadores_list,
            }
            sim_data["done"] = True
        except Exception as e:
            sim_data["error"] = e
            sim_data["done"] = True

    import threading
    t = threading.Thread(target=_run_simulation, daemon=True)
    t.start()

    _FAKE_MSGS = [
        (10, "Iniciando simulacion..."),
        (20, "Leyendo Mundiales..."),
        (35, "Cargando jugadores..."),
        (50, "Analizando fase de grupos..."),
        (65, "Simulando mundial 1500 veces..."),
        (75, "Leyendo historia de Mundiales..."),
        (85, "Generando predicciones..."),
        (95, "Preparando interfaz grafica..."),
        (100, "Listo!"),
    ]

    _fake_pct = 0

    def _tick():
        nonlocal _fake_pct
        if _fake_pct < 100:
            _fake_pct += 1
            msg = next(m for m in _FAKE_MSGS if _fake_pct <= m[0])[1]
            splash.set_progress(_fake_pct, msg)
            root.after(100, _tick)
        elif sim_data.get("done"):
            _finish()
        else:
            root.after(100, _tick)

    def _finish():
        splash.close()
        if "error" in sim_data:
            messagebox.showerror("Error", f"Error al iniciar GUI:\n{sim_data['error']}")
            root.destroy()
            return
        pre_data = sim_data["pre_data"]
        ico = os.path.join(OUTPUT_DIR, "wc26_icon.ico")
        if os.path.exists(ico):
            try:
                root.iconbitmap(ico)
            except Exception:
                pass
        root.deiconify()
        ProdeGUI(root, pre_data=pre_data)

    root.after(200, _tick)
    root.mainloop()


if __name__ == "__main__":
    main()
