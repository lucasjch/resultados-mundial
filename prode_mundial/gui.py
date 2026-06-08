# -*- coding: utf-8 -*-
"""GUI tkinter para visualizar el prode del Mundial 2026."""

import json
import math
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

_TEAM_FLAGS = {
    "Mexico":"MX","South Korea":"KR","South Africa":"ZA","Czechia":"CZ",
    "Canada":"CA","Switzerland":"CH","Qatar":"QA","Bosnia & Herzegovina":"BA",
    "Brazil":"BR","Morocco":"MA","Scotland":"GB","Haiti":"HT","USA":"US",
    "Paraguay":"PY","Australia":"AU","Turkey":"TR","Germany":"DE",
    "Ecuador":"EC","Ivory Coast":"CI","Curacao":"CW","Netherlands":"NL",
    "Japan":"JP","Sweden":"SE","Tunisia":"TN","Belgium":"BE","Egypt":"EG",
    "Iran":"IR","New Zealand":"NZ","Spain":"ES","Uruguay":"UY",
    "Saudi Arabia":"SA","Cape Verde":"CV","France":"FR","Norway":"NO",
    "Senegal":"SN","Iraq":"IQ","Argentina":"AR","Algeria":"DZ",
    "Austria":"AT","Jordan":"JO","Portugal":"PT","Colombia":"CO",
    "Uzbekistan":"UZ","DR Congo":"CD","England":"GB","Croatia":"HR",
    "Ghana":"GH","Panama":"PA",
}

_COLORS = {
    "bg": "#0a0a1a", "fg": "#d0d0e0", "accent": "#ff3366",
    "card_bg": "#12122a", "card_border": "#2a2a5a",
    "star": "#ffd700", "btn": "#1a1a4a", "btn_hover": "#2a2a6a",
    "green": "#00e676", "red": "#ff1744", "yellow": "#ffea00",
    "subtitle": "#8888bb",
}

_FONT_H = ("Corbel", 24, "bold")
_FONT_SH = ("Corbel", 14)
_FONT_M = ("Corbel", 11)
_FONT_S = ("Corbel", 9)
_FONT_SCORE = ("Corbel", 32, "bold")
_FONT_TEAM = ("Corbel", 20, "bold")
_FONT_TAB = ("Consolas", 10)
_FONT_TAB_H = ("Consolas", 10, "bold")

_RE_ASCII = re.compile(r'[^\x20-\x7e]')
def _safe(text):
    return _RE_ASCII.sub('?', str(text))

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)


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
    return "\u2605" * filled + "\u2606" * (5 - filled)


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
    def __init__(self, root):
        self.root = root
        root.title("Prode Mundial 2026")
        root.configure(bg=_COLORS["bg"])
        root.geometry("960x720")
        root.resizable(True, True)

        groups = load_json("fase_grupos.json") or []
        knockout = load_json("eliminatorias.json") or []
        self.data = {
            "groups": groups,
            "knockout": knockout,
            "tables": load_json("tabla_posiciones.json") or {},
            "prode": load_json("prode_completo.json") or [],
            "goleadores": self._load_goleadores(groups, knockout),
        }
        self._idx = {"groups": 0, "knockout": 0}
        self._build_ui()

    def _load_goleadores(self, gp, kp):
        if gp or kp:
            try:
                sys.path.insert(0, BASE_DIR)
                from top_scorer import compute_top_scorers
                return compute_top_scorers(gp, kp, top_n=20)
            except Exception:
                pass
        return []

    def _styled_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=_FONT_M,
                        bg=_COLORS["btn"], fg=_COLORS["fg"],
                        relief=tk.RAISED, bd=0, padx=12, pady=4,
                        cursor="hand2", activebackground=_COLORS["btn_hover"],
                        command=cmd)
        btn.bind("<Enter>", lambda e: btn.configure(bg=_COLORS["btn_hover"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=_COLORS["btn"]))
        return btn

    def _build_ui(self):
        header = tk.Frame(self.root, bg=_COLORS["bg"], height=70)
        header.pack(fill=tk.X, padx=15, pady=(10, 0))
        header.pack_propagate(False)

        banner_path = os.path.join(OUTPUT_DIR, "wc26_logo.png")
        if os.path.exists(banner_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(banner_path)
                resample = 1
                img = img.resize((180, 55), resample)
                self._banner_img = ImageTk.PhotoImage(img)
                lbl_banner = tk.Label(header, image=self._banner_img, bg=_COLORS["bg"])
                lbl_banner.pack(side=tk.LEFT, padx=5)
            except Exception:
                pass

        tk.Label(header, text="Mundial 2026",
                 font=_FONT_H, bg=_COLORS["bg"],
                 fg=_COLORS["accent"]).pack(side=tk.LEFT, padx=15)

        tk.Label(header, text="Predicciones PRODE",
                 font=_FONT_SH, bg=_COLORS["bg"],
                 fg=_COLORS["subtitle"]).pack(side=tk.LEFT, padx=5, pady=(12, 0))

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=_COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=_COLORS["card_bg"],
                        foreground=_COLORS["fg"],
                        padding=[18, 6],
                        font=("Corbel", 11))
        style.map("TNotebook.Tab",
                  background=[("selected", _COLORS["btn"])],
                  foreground=[("selected", "#ffffff")])

        self._tab_groups = ttk.Frame(nb)
        self._tab_ko = ttk.Frame(nb)
        self._tab_stats = ttk.Frame(nb)
        self._tab_goleadores = ttk.Frame(nb)
        self._tab_bonus = ttk.Frame(nb)

        nb.add(self._tab_groups, text=" Fase de Grupos ")
        nb.add(self._tab_ko, text=" Eliminatorias ")
        nb.add(self._tab_stats, text=" Estadisticas ")
        nb.add(self._tab_goleadores, text=" Goleadores ")
        nb.add(self._tab_bonus, text=" Bonus ")

        self._build_groups_tab()
        self._build_ko_tab()
        self._build_stats_tab()
        self._build_goleadores_tab()
        self._build_bonus_tab()

        status = tk.Label(self.root, text="Datos cargados desde output/",
                          bg=_COLORS["card_bg"], fg=_COLORS["subtitle"],
                          anchor=tk.W, padx=15)
        status.pack(fill=tk.X)

    def _nav_frame(self, parent, tab_name):
        f = tk.Frame(parent, bg=_COLORS["bg"])
        f.pack(fill=tk.X, pady=5)
        btn_prev = self._styled_btn(f, " \u25C0 ", lambda: self._nav(tab_name, -1))
        btn_prev.pack(side=tk.LEFT, padx=5)
        lbl = tk.Label(f, text="", font=_FONT_M, bg=_COLORS["bg"],
                       fg=_COLORS["fg"])
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)
        setattr(self, f"_lbl_{tab_name}", lbl)
        btn_next = self._styled_btn(f, " \u25B6 ", lambda: self._nav(tab_name, 1))
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
        venue = match.get("venue", "")
        conf = match.get("confidence", 0)
        probs = match.get("probabilities", {})
        prob_a = probs.get("a_win", 0)
        prob_b = probs.get("b_win", 0)
        prob_d = probs.get("draw", 0)

        shadow = tk.Frame(parent, bg=_COLORS["bg"], padx=2, pady=2)
        shadow.pack(fill=tk.BOTH, expand=True, padx=18, pady=8)
        card = tk.Frame(shadow, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=1, relief=tk.FLAT)
        card.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        vs_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        vs_frame.pack(expand=True, pady=(20, 5))

        lbl_a = tk.Label(vs_frame, text=flag_name(team_a), font=_FONT_TEAM,
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"])
        lbl_a.pack(side=tk.LEFT, padx=15)

        score_frame = tk.Frame(vs_frame, bg=_COLORS["score_bg"] if "score_bg" in _COLORS else _COLORS["card_bg"],
                                highlightbackground=_COLORS["card_border"],
                                highlightthickness=1, padx=20, pady=5)
        score_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(score_frame, text=f"{score_a} - {score_b}",
                 font=_FONT_SCORE, bg=score_frame["bg"],
                 fg=_COLORS["accent"]).pack()

        lbl_b = tk.Label(vs_frame, text=flag_name(team_b), font=_FONT_TEAM,
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"])
        lbl_b.pack(side=tk.LEFT, padx=15)

        prob_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        prob_frame.pack(pady=5)
        tk.Label(prob_frame,
                 text=f"  {flag_name(team_a)}: {prob_a:.0f}%  |  Empate: {prob_d:.0f}%  |  {flag_name(team_b)}: {prob_b:.0f}%  ",
                 font=_FONT_M, bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).pack()

        stars = stars_html(conf)
        star_lbl = tk.Label(card, text=stars, font=("Corbel", 20),
                            bg=_COLORS["card_bg"], fg=_COLORS["star"])
        star_lbl.pack(pady=2)
        ToolTip(star_lbl, f"Confianza: {conf:.0f}%\nBasada en 1500 simulaciones Poisson")

        round_label = match.get("round", "")
        grp_label = f"  {round_label}  |  " if round_label else ""
        tk.Label(card, text=f"{grp_label}Sede: {venue}   Partido {idx+1}/{total}",
                 font=_FONT_S, bg=_COLORS["card_bg"],
                 fg=_COLORS["subtitle"]).pack(pady=(0, 10))

        return card

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

        self._nav_frame(parent, "groups")
        self._card_frame_groups = tk.Frame(parent, bg=_COLORS["bg"])
        self._card_frame_groups.pack(fill=tk.BOTH, expand=True)
        self._show_group_match()

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
        self._idx["groups"] = 0
        self._show_group_match()

    def _show_group_match(self):
        for w in self._card_frame_groups.winfo_children():
            w.destroy()
        matches = self.data["groups"]
        if not matches:
            tk.Label(self._card_frame_groups, text="No hay datos. Ejecute main.py primero.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return
        filtered = self._filtered_group_indices
        idx = self._idx["groups"]
        if idx >= len(filtered):
            idx = 0
            self._idx["groups"] = 0
        m = matches[filtered[idx]]
        total = len(filtered)
        grp = m.get("round", "")
        lbl = getattr(self, "_lbl_groups", None)
        if lbl:
            lbl.config(text=f"{grp}  -  Partido {idx+1}/{total}")
        self._match_card(self._card_frame_groups, m, idx, total)

    def _build_ko_tab(self):
        parent = self._tab_ko
        self._nav_frame(parent, "knockout")
        self._card_frame_ko = tk.Frame(parent, bg=_COLORS["bg"])
        self._card_frame_ko.pack(fill=tk.BOTH, expand=True)
        self._show_ko_match()

    def _show_ko_match(self):
        for w in self._card_frame_ko.winfo_children():
            w.destroy()
        matches = self.data["knockout"]
        if not matches:
            tk.Label(self._card_frame_ko, text="No hay datos. Ejecute main.py primero.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"],
                     font=_FONT_SH).pack(expand=True)
            return
        idx = self._idx["knockout"]
        m = matches[idx]
        total = len(matches)
        card = self._match_card(self._card_frame_ko, m, idx, total)
        ronda = m.get("round", "KO")
        tk.Label(card, text=f"Ronda: {ronda}",
                 font=_FONT_M, bg=_COLORS["card_bg"],
                 fg=_COLORS["yellow"]).pack()

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

            hdr_line = f"{'':4s} {'Pts':4s} {'GD':4s} {'GF':4s} {'GA':4s}"
            tk.Label(grp_frame, text=hdr_line, font=_FONT_TAB_H,
                     bg=_COLORS["card_bg"],
                     fg=_COLORS["subtitle"]).pack(anchor=tk.W)

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
                fn = flag_name(team_name)
                prefix = "\u2605" if rank <= 2 else " "
                line = f"{prefix} {fn:24s} {pts:3d} {gd:+3d} {gf:3d} {ga:3d}"
                clr = _COLORS["green"] if rank <= 2 else _COLORS["fg"]
                tk.Label(grp_frame, text=line, font=_FONT_TAB,
                         bg=_COLORS["card_bg"], fg=clr,
                         anchor=tk.W).pack(fill=tk.X)

        third = self._compute_third_placed(tables)
        if third:
            sep = tk.Frame(scroll_frame, bg=_COLORS["card_border"], height=1)
            sep.pack(fill=tk.X, padx=15, pady=(15, 5))
            tk.Label(scroll_frame, text="Mejores Terceros (8 clasifican a 32vos)",
                     font=("Corbel", 14, "bold"), bg=_COLORS["bg"],
                     fg=_COLORS["accent"]).pack(pady=(5, 5))

            hdr3 = tk.Frame(scroll_frame, bg=_COLORS["bg"])
            hdr3.pack(fill=tk.X, padx=20)
            for txt, w in [("", 3), ("Equipo", 28), ("Grp", 4), ("Pts", 5), ("GD", 5), ("GF", 5)]:
                tk.Label(hdr3, text=txt, font=_FONT_TAB_H,
                         bg=_COLORS["bg"], fg=_COLORS["subtitle"],
                         width=w, anchor=tk.W).pack(side=tk.LEFT)

            for rank3, (grp, tm, pts3, gd3, gf3) in enumerate(third, 1):
                qualifies = rank3 <= 4
                row_bg = _COLORS["card_bg"] if rank3 % 2 == 0 else _COLORS["bg"]
                row3 = tk.Frame(scroll_frame, bg=row_bg)
                row3.pack(fill=tk.X, padx=20)
                icon = "\u2605" if qualifies else " "
                clr3 = _COLORS["green"] if qualifies else _COLORS["fg"]
                tk.Label(row3, text=icon, font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=3).pack(side=tk.LEFT)
                tk.Label(row3, text=flag_name(tm), font=_FONT_TAB, bg=row_bg,
                         fg=clr3, width=28, anchor=tk.W).pack(side=tk.LEFT)
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
        tk.Label(header, text="Tabla de Goleadores",
                 font=("Corbel", 18, "bold"), bg=_COLORS["bg"],
                 fg=_COLORS["accent"]).pack(side=tk.LEFT)

        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
            tk.Label(row, text=flag_name(team), font=_FONT_TAB,
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=24, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(goles), font=_FONT_TAB_H,
                     bg=row["bg"], fg=_COLORS["star"],
                     width=8, anchor=tk.W).pack(side=tk.LEFT)

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
            bonus["most_goals_team"] = max(gs, key=gs.get)
            bonus["most_goals_total"] = gs[bonus["most_goals_team"]]
        if gc:
            bonus["best_defense"] = min(gc, key=gc.get)
            bonus["best_defense_ga"] = gc[bonus["best_defense"]]
        if best_match:
            bonus["best_match"] = best_match

        return bonus

    def _bonus_card(self, parent, title, value, detail, color):
        card = tk.Frame(parent, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=1, relief=tk.FLAT)
        card.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(card, text=title, font=("Corbel", 13, "bold"),
                 bg=_COLORS["card_bg"], fg=color).pack(anchor=tk.W, padx=15, pady=(8, 0))
        tk.Label(card, text=value, font=("Corbel", 17, "bold"),
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(anchor=tk.W, padx=15, pady=2)
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

        bonus = self._compute_bonus_data()

        tk.Label(scroll_frame, text="Predicciones Bonus",
                 font=("Corbel", 22, "bold"), bg=_COLORS["bg"],
                 fg=_COLORS["accent"]).pack(pady=(20, 5))

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
            "  \u25cf  3 pts  - Resultado exacto\n"
            "  \u25cf  1 pt   - Resultado acertado (ganador o empate)\n"
            "  \u25cf  0 pts  - No acertaste\n\n"
            "Predicciones Bonus:\n"
            "  \u25cf  Campeon: ? pts\n"
            "  \u25cf  Goleador: ? pts\n"
            "  \u25cf  Cada clasificado de grupo: 1 pt\n"
            "  \u25cf  Cada semifinalista correcto: 1 pt"
        )
        tk.Label(rules_card, text=rules_text, font=_FONT_M,
                 bg=_COLORS["card_bg"],
                 fg=_COLORS["fg"], justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 8))

        # Champion, runner-up, third place
        items = [
            ("\U0001F3C6  Campeon", bonus.get("champion", "?"),
             f"Confianza: {bonus.get('champion_conf', 0):.0f}%",
             _COLORS["star"]),
            ("\U0001F948  Subcampeon", bonus.get("runner_up", "?"),
             f"Final: {bonus.get('final_score', '')}",
             _COLORS["subtitle"]),
            ("\U0001F949  Tercer Puesto", bonus.get("third_place", "?"),
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
            self._bonus_card(scroll_frame, "\u26BD  Goleador",
                             f"{ts} ({flag_name(ts_team)})",
                             f"Goles: {ts_goals}",
                             _COLORS["yellow"])

        # 4 Semifinalists
        sfs = bonus.get("semifinalists", [])
        if sfs:
            sf_text = "  |  ".join(flag_name(t) for t in sfs)
            self._bonus_card(scroll_frame, "\U0001F3C6  4 Semifinalistas",
                             sf_text,
                             "1 pt por cada acierto",
                             _COLORS["green"])

        # Classified per group
        classified = bonus.get("classified", {})
        if classified:
            lines = []
            for g in sorted(classified.keys()):
                t1, t2 = classified[g]
                lines.append(f"  {g}: {flag_name(t1)}, {flag_name(t2)}")
            cls_text = "\n".join(lines)
            inner = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                             highlightbackground=_COLORS["card_border"],
                             highlightthickness=1, relief=tk.FLAT)
            inner.pack(fill=tk.X, padx=20, pady=6)
            tk.Label(inner, text="Clasificados por Grupo",
                     font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                     fg=_COLORS["green"]).pack(anchor=tk.W, padx=15, pady=(8, 2))
            tk.Label(inner, text=cls_text, font=_FONT_M,
                     bg=_COLORS["card_bg"],
                     fg=_COLORS["fg"], justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 8))

        # x2 recommendations
        try:
            sys.path.insert(0, BASE_DIR)
            from optimizer import analyze_x2
            x2_data = analyze_x2(group_predictions=self.data["groups"])
            if x2_data:
                x2_inner = tk.Frame(scroll_frame, bg=_COLORS["card_bg"],
                                    highlightbackground=_COLORS["card_border"],
                                    highlightthickness=1, relief=tk.FLAT)
                x2_inner.pack(fill=tk.X, padx=20, pady=6)
                tk.Label(x2_inner, text="Multiplicador x2 - Top 3 Recomendados",
                         font=("Corbel", 13, "bold"), bg=_COLORS["card_bg"],
                         fg=_COLORS["accent"]).pack(anchor=tk.W, padx=15, pady=(8, 2))
                tk.Label(x2_inner,
                         text="Poner x2 hasta en 3 partidos. Si acertas, duplica los puntos (3\u21926, 1\u21924).",
                         font=_FONT_S, bg=_COLORS["card_bg"],
                         fg=_COLORS["subtitle"]).pack(anchor=tk.W, padx=15, pady=(0, 2))
                for i, r in enumerate(x2_data[:3], 1):
                    fa = flag_name(r["team_a"])
                    fb = flag_name(r["team_b"])
                    line = (f"  {i}. {fa} vs {fb}  |  "
                            f"Pronostico: {r['predicted']}  |  "
                            f"P(acierto): {r['p_result_pct']:.0f}%  |  "
                            f"EV gain: +{r['ev_gain']:.3f}")
                    tk.Label(x2_inner, text=line, font=_FONT_M,
                             bg=_COLORS["card_bg"],
                             fg=_COLORS["fg"], justify=tk.LEFT,
                             anchor=tk.W).pack(fill=tk.X, padx=15, pady=1)
        except Exception:
            pass

        # Extra stats
        mt = bonus.get("most_goals_team", "")
        if mt:
            self._bonus_card(scroll_frame, "\U0001F525  Equipo con mas goles",
                             flag_name(mt),
                             f"Total: {bonus.get('most_goals_total', 0)} goles",
                             _COLORS["green"])
        bd = bonus.get("best_defense", "")
        if bd:
            self._bonus_card(scroll_frame, "\U0001F6E1  Mejor defensa",
                             flag_name(bd),
                             f"Solo {bonus.get('best_defense_ga', 0)} goles recibidos",
                             _COLORS["green"])
        bm = bonus.get("best_match", {})
        if bm:
            self._bonus_card(scroll_frame, "\U0001F4A5  Partido con mas goles",
                             f"{bm.get('teams', '')}",
                             f"{bm.get('score', '')} ({bm.get('goals', 0)} goles)",
                             _COLORS["accent"])

    # unused idx key kept for compatibility
    _idx = {"groups": 0, "knockout": 0}


def main():
    root = tk.Tk()
    ico = os.path.join(OUTPUT_DIR, "wc26_icon.ico")
    if os.path.exists(ico):
        try:
            root.iconbitmap(ico)
        except Exception:
            pass
    try:
        app = ProdeGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Error al iniciar GUI:\n{e}")
        raise


if __name__ == "__main__":
    main()
