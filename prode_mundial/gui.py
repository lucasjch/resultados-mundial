# -*- coding: utf-8 -*-
"""GUI tkinter para visualizar el prode del Mundial 2026."""

import json
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

_TEAM_FLAGS = {}
_COLORS = {
    "bg": "#1a1a2e", "fg": "#e0e0e0", "accent": "#e94560",
    "card_bg": "#16213e", "card_border": "#0f3460",
    "star": "#f5c518", "btn": "#2E5090", "btn_hover": "#4A7BC5",
    "green": "#2ecc71", "red": "#e74c3c", "yellow": "#f1c40f",
}

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


def stars_html(pct):
    filled = int(pct / 20)
    s = "\u2605" * filled + "\u2606" * (5 - filled)
    return s


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
                       background="#ffffcc", relief=tk.SOLID,
                       borderwidth=1, font=("Consolas", 9))
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
        root.geometry("900x680")
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
        self._idx = {"groups": 0, "knockout": 0, "goleadores": 0}
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

    def _build_ui(self):
        header = tk.Frame(self.root, bg=_COLORS["bg"], height=80)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        header.pack_propagate(False)

        banner_path = os.path.join(OUTPUT_DIR, "wc26_logo.png")
        if os.path.exists(banner_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(banner_path)
                resample = 1
                img = img.resize((200, 60), resample)
                self._banner_img = ImageTk.PhotoImage(img)
                lbl_banner = tk.Label(header, image=self._banner_img, bg=_COLORS["bg"])
                lbl_banner.pack(side=tk.LEFT, padx=10)
            except Exception:
                pass

        lbl_title = tk.Label(header, text="Mundial 2026",
                             font=("Arial", 28, "bold"),
                             bg=_COLORS["bg"], fg=_COLORS["accent"])
        lbl_title.pack(side=tk.LEFT, padx=20)

        lbl_sub = tk.Label(header, text="Predicciones PRODE",
                           font=("Arial", 12), bg=_COLORS["bg"], fg=_COLORS["fg"])
        lbl_sub.pack(side=tk.LEFT, padx=5, pady=(15, 0))

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=_COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=_COLORS["card_bg"],
                        foreground=_COLORS["fg"], padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", _COLORS["btn"])])

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
                          bg=_COLORS["card_bg"], fg=_COLORS["fg"],
                          anchor=tk.W, padx=10)
        status.pack(fill=tk.X)

    def _nav_frame(self, parent, tab_name):
        f = tk.Frame(parent, bg=_COLORS["bg"])
        f.pack(fill=tk.X, pady=5)
        btn_prev = tk.Button(f, text=" \u25C0 ", font=("Arial", 14, "bold"),
                             bg=_COLORS["btn"], fg="white", relief=tk.RAISED,
                             activebackground=_COLORS["btn_hover"],
                             command=lambda: self._nav(tab_name, -1))
        btn_prev.pack(side=tk.LEFT, padx=5)
        btn_prev.bind("<Enter>", lambda e: btn_prev.configure(relief=tk.SUNKEN))
        btn_prev.bind("<Leave>", lambda e: btn_prev.configure(relief=tk.RAISED))

        lbl = tk.Label(f, text="", font=("Arial", 10), bg=_COLORS["bg"],
                       fg=_COLORS["fg"])
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        setattr(self, f"_lbl_{tab_name}", lbl)

        btn_next = tk.Button(f, text=" \u25B6 ", font=("Arial", 14, "bold"),
                             bg=_COLORS["btn"], fg="white", relief=tk.RAISED,
                             activebackground=_COLORS["btn_hover"],
                             command=lambda: self._nav(tab_name, 1))
        btn_next.pack(side=tk.RIGHT, padx=5)
        btn_next.bind("<Enter>", lambda e: btn_next.configure(relief=tk.SUNKEN))
        btn_next.bind("<Leave>", lambda e: btn_next.configure(relief=tk.RAISED))
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

        card = tk.Frame(parent, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=2, relief=tk.RIDGE)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        vs_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        vs_frame.pack(expand=True)

        font_vs = ("Arial", 22, "bold")
        lbl_a = tk.Label(vs_frame, text=_safe(team_a), font=font_vs,
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"])
        lbl_a.pack(side=tk.LEFT, padx=15)

        lbl_score = tk.Label(vs_frame, text=f"{score_a} - {score_b}",
                             font=("Arial", 28, "bold"),
                             bg=_COLORS["card_bg"], fg=_COLORS["accent"])
        lbl_score.pack(side=tk.LEFT, padx=20)

        lbl_b = tk.Label(vs_frame, text=_safe(team_b), font=font_vs,
                         bg=_COLORS["card_bg"], fg=_COLORS["fg"])
        lbl_b.pack(side=tk.LEFT, padx=15)

        prob_frame = tk.Frame(card, bg=_COLORS["card_bg"])
        prob_frame.pack(pady=5)
        tk.Label(prob_frame, text=f"  {team_a}: {prob_a:.0f}%  |  Empate: {prob_d:.0f}%  |  {team_b}: {prob_b:.0f}%  ",
                 font=("Consolas", 11), bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack()

        stars = stars_html(conf)
        star_lbl = tk.Label(card, text=stars, font=("Arial", 18),
                            bg=_COLORS["card_bg"], fg=_COLORS["star"])
        star_lbl.pack(pady=2)
        ToolTip(star_lbl, f"Confianza: {conf:.0f}%\nBasada en 1500 simulaciones Poisson")

        tk.Label(card, text=f"Sede: {venue}   Partido {idx+1}/{total}",
                 font=("Arial", 9), bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack()

        return card

    def _build_groups_tab(self):
        parent = self._tab_groups
        self._group_filter = None
        self._filtered_group_indices = list(range(len(self.data["groups"])))

        filter_frame = tk.Frame(parent, bg=_COLORS["bg"])
        filter_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        tk.Label(filter_frame, text="Grupo:", font=("Arial", 10, "bold"),
                 bg=_COLORS["bg"], fg=_COLORS["fg"]).pack(side=tk.LEFT, padx=(0, 5))
        groups_list = ["Todos"] + [chr(65 + i) for i in range(12)]
        self._group_combo = ttk.Combobox(filter_frame, values=groups_list,
                                          state="readonly", width=10, font=("Arial", 10))
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
                     bg=_COLORS["bg"], fg=_COLORS["fg"], font=("Arial", 14)).pack(expand=True)
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
                     bg=_COLORS["bg"], fg=_COLORS["fg"], font=("Arial", 14)).pack(expand=True)
            return
        idx = self._idx["knockout"]
        m = matches[idx]
        total = len(matches)
        card = self._match_card(self._card_frame_ko, m, idx, total)
        ronda = m.get("round", "KO")
        tk.Label(card, text=f"Ronda: {ronda}",
                 font=("Arial", 10, "bold"), bg=_COLORS["card_bg"], fg=_COLORS["yellow"]).pack()

    def _build_stats_tab(self):
        parent = self._tab_stats
        tables = self.data.get("tables", {})
        if not tables:
            tk.Label(parent, text="No hay tabla de posiciones.",
                     bg=_COLORS["bg"], fg=_COLORS["fg"], font=("Arial", 14)).pack(expand=True)
            return

        canvas = tk.Canvas(parent, bg=_COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_COLORS["bg"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for g in sorted(tables.keys()):
            grp_frame = tk.LabelFrame(scroll_frame, text=f"Grupo {g}",
                                      bg=_COLORS["card_bg"], fg=_COLORS["accent"],
                                      font=("Arial", 12, "bold"),
                                      padx=10, pady=5)
            grp_frame.pack(fill=tk.X, padx=10, pady=5)

            teams = tables[g]
            header_txt = f"{'Equipo':25s} {'Pts':5s} {'GD':5s} {'GF':5s} {'GA':5s}"
            tk.Label(grp_frame, text=header_txt, font=("Consolas", 10, "bold"),
                     bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(anchor=tk.W)

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
                prefix = "\u2605" if rank <= 2 else " "
                line = f"{prefix} {team_name:24s} {pts:3d}   {gd:+3d}  {gf:3d}  {ga:3d}"
                clr = _COLORS["green"] if rank <= 2 else _COLORS["fg"]
                tk.Label(grp_frame, text=line, font=("Consolas", 10),
                         bg=_COLORS["card_bg"], fg=clr).pack(anchor=tk.W)

    def _build_goleadores_tab(self):
        parent = self._tab_goleadores
        header = tk.Frame(parent, bg=_COLORS["bg"])
        header.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(header, text="Tabla de Goleadores",
                 font=("Arial", 14, "bold"), bg=_COLORS["bg"],
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
                     font=("Arial", 14)).pack(expand=True)
            return

        hdr = tk.Frame(scroll_frame, bg=_COLORS["card_bg"])
        hdr.pack(fill=tk.X, padx=10, pady=(5, 0))
        for txt, w in [("#", 4), ("Jugador", 30), ("Equipo", 22), ("Goles", 8)]:
            tk.Label(hdr, text=txt, font=("Consolas", 10, "bold"),
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
            row.pack(fill=tk.X, padx=10)
            tk.Label(row, text=str(rank), font=("Consolas", 10),
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=4, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=_safe(player), font=("Consolas", 10),
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=30, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=_safe(team), font=("Consolas", 10),
                     bg=row["bg"], fg=_COLORS["fg"],
                     width=22, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(goles), font=("Consolas", 10, "bold"),
                     bg=row["bg"], fg=_COLORS["star"],
                     width=8, anchor=tk.W).pack(side=tk.LEFT)

    def _compute_bonus_data(self):
        ko = self.data.get("knockout", [])
        groups = self.data.get("groups", [])
        scorers = self.data.get("goleadores", [])
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

        if scorers:
            ts = scorers[0]
            bonus["top_scorer"] = ts.get("player", "?")
            bonus["top_scorer_team"] = ts.get("team", "")
            bonus["top_scorer_goals"] = ts.get("raw_goals", ts.get("goals", 0))

        all_matches = groups + ko
        goals_scored = {}
        goals_conceded = {}
        max_total = 0
        best_match = {}
        for m in all_matches:
            a = m.get("team_a", "?")
            b = m.get("team_b", "?")
            sa = m.get("score_a", 0)
            sb = m.get("score_b", 0)
            goals_scored[a] = goals_scored.get(a, 0) + sa
            goals_scored[b] = goals_scored.get(b, 0) + sb
            goals_conceded[a] = goals_conceded.get(a, 0) + sb
            goals_conceded[b] = goals_conceded.get(b, 0) + sa
            total = sa + sb
            if total > max_total:
                max_total = total
                best_match = {"teams": f"{a} vs {b}", "score": f"{sa}-{sb}", "goals": total}

        if goals_scored:
            bonus["most_goals_team"] = max(goals_scored, key=goals_scored.get)
            bonus["most_goals_total"] = goals_scored[bonus["most_goals_team"]]
        if goals_conceded:
            bonus["best_defense"] = min(goals_conceded, key=goals_conceded.get)
            bonus["best_defense_ga"] = goals_conceded[bonus["best_defense"]]
        if best_match:
            bonus["best_match"] = best_match

        return bonus

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

        tk.Label(scroll_frame, text="Pronosticos Bonus",
                 font=("Arial", 18, "bold"), bg=_COLORS["bg"],
                 fg=_COLORS["accent"]).pack(pady=(15, 10))

        items = [
            ("\U0001F3C6  Campeon", bonus.get("champion", "?"),
             f"Confianza: {bonus.get('champion_conf', 0):.0f}%",
             _COLORS["star"]),
            ("\U0001F948  Subcampeon", bonus.get("runner_up", "?"),
             f"Final: {bonus.get('final_score', '')}",
             _COLORS["fg"]),
            ("\U0001F949  Tercer Puesto", bonus.get("third_place", "?"),
             f"3er puesto: {bonus.get('third_score', '')}",
             _COLORS["fg"]),
        ]
        for label, value, detail, color in items:
            self._bonus_card(scroll_frame, label, str(value), detail, color)

        ts = bonus.get("top_scorer", "")
        if ts:
            ts_team = bonus.get("top_scorer_team", "")
            ts_goals = bonus.get("top_scorer_goals", 0)
            self._bonus_card(scroll_frame, "\u26BD  Goleador",
                             f"{ts} ({ts_team})",
                             f"Goles: {ts_goals}",
                             _COLORS["yellow"])

        mt = bonus.get("most_goals_team", "")
        if mt:
            self._bonus_card(scroll_frame, "\U0001F525  Equipo con mas goles",
                             mt,
                             f"Total: {bonus.get('most_goals_total', 0)} goles",
                             _COLORS["green"])

        bd = bonus.get("best_defense", "")
        if bd:
            self._bonus_card(scroll_frame, "\U0001F6E1  Mejor defensa",
                             bd,
                             f"Solo {bonus.get('best_defense_ga', 0)} goles recibidos",
                             _COLORS["green"])

        bm = bonus.get("best_match", {})
        if bm:
            self._bonus_card(scroll_frame, "\U0001F4A5  Partido con mas goles",
                             f"{bm.get('teams', '')}",
                             f"{bm.get('score', '')} ({bm.get('goals', 0)} goles)",
                             _COLORS["accent"])

    def _bonus_card(self, parent, title, value, detail, color):
        card = tk.Frame(parent, bg=_COLORS["card_bg"],
                        highlightbackground=_COLORS["card_border"],
                        highlightthickness=2, relief=tk.RIDGE)
        card.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(card, text=title, font=("Arial", 12, "bold"),
                 bg=_COLORS["card_bg"], fg=color).pack(anchor=tk.W, padx=15, pady=(8, 0))
        tk.Label(card, text=value, font=("Arial", 16, "bold"),
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(anchor=tk.W, padx=15, pady=2)
        tk.Label(card, text=detail, font=("Arial", 10),
                 bg=_COLORS["card_bg"], fg=_COLORS["fg"]).pack(anchor=tk.W, padx=15, pady=(0, 8))


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
