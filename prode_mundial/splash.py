# -*- coding: utf-8 -*-
"""Pantalla de carga con imagen de fondo y barra de progreso verde 3D."""

import os
import sys
import tkinter as tk

from PIL import Image, ImageTk

_COLORS = {
    "bg":          "#0d1117",
    "fg":          "#e6edf3",
    "accent":      "#c9a84c",
    "card_bg":     "#161b22",
    "card_border": "#30363d",
    "subtitle":    "#8b949e",
    "green":       "#238636",
    "green_light": "#2ea043",
    "green_dark":  "#145522",
}


class _GreenProgressBar:
    """Barra de progreso verde con efecto 3D hecho en Canvas (composicion)."""

    def __init__(self, parent, width=400, height=26):
        self._canvas = tk.Canvas(parent, width=width, height=height,
                                 bg=_COLORS["bg"], highlightthickness=0)
        self._w = width
        self._h = height
        self._pct = 0

    def place(self, **kwargs):
        self._canvas.place(**kwargs)

    def set(self, pct):
        self._pct = max(0, min(100, pct))
        self._draw(self._pct)

    def _draw(self, pct):
        c = self._canvas
        c.delete("all")
        w, h = self._w, self._h
        c.create_rectangle(1, 1, w - 1, h - 1,
                           outline=_COLORS["card_border"], width=2)
        c.create_rectangle(3, 3, w - 3, h - 3,
                           fill=_COLORS["card_bg"], outline="")
        if pct > 0:
            fw = max(4, int((w - 8) * pct / 100))
            c.create_rectangle(4, 4, 4 + fw, h - 4,
                               fill=_COLORS["green"], outline="")
            c.create_rectangle(4, 4, 4 + fw, 8,
                               fill=_COLORS["green_light"], outline="")
            c.create_rectangle(4, h - 8, 4 + fw, h - 4,
                               fill=_COLORS["green_dark"], outline="")
        c.create_text(w // 2, h // 2, text=f"{pct:.0f}%",
                      fill=_COLORS["fg"], font=("Corbel", 10, "bold"))


class SplashScreen:
    """Pantalla de carga con imagen de fondo adaptativa y barra de progreso."""

    def __init__(self, root):
        self.root = root
        self._win = tk.Toplevel(root)
        self._img_orig = None
        self._bg_photo = None
        self._win_w = 720
        self._win_h = 520

        self._win.overrideredirect(True)
        self._win.configure(bg=_COLORS["bg"])
        self._center(self._win_w, self._win_h)
        self._win.resizable(True, True)
        self._win.minsize(500, 350)

        self._load_image()

        self._canvas = tk.Canvas(self._win, bg=_COLORS["bg"], highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Configure>", self._on_resize)

        self._render_bg()

        # Title
        self._title_id = self._canvas.create_text(
            self._win_w // 2, 45,
            text="\u26BD Mundial 2026",
            fill=_COLORS["accent"],
            font=("Corbel", 28, "bold"),
            tags="title")

        # Status label
        self._status_id = self._canvas.create_text(
            self._win_w // 2, self._win_h // 2 - 20,
            text="", fill=_COLORS["fg"],
            font=("Corbel", 13),
            tags="status")

        # Progress bar (centered, bottom area)
        self._bar_width = 400
        self._progress = _GreenProgressBar(self._win, width=self._bar_width)
        self._progress.place(relx=0.5, rely=0.80, anchor=tk.CENTER)

        # Footer
        self._footer_id = self._canvas.create_text(
            self._win_w // 2, self._win_h - 18,
            text="Prode Mundial 2026 \u2014 Lucas Congil Hadla",
            fill=_COLORS["subtitle"],
            font=("Corbel", 9),
            tags="footer")

        root.update_idletasks()

    def _load_image(self):
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
            path = os.path.join(base, "prode_mundial", "imput",
                                "wp15655996-fifa-world-cup-2026-hd-wallpapers.jpg")
        else:
            base = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base, "imput",
                                "wp15655996-fifa-world-cup-2026-hd-wallpapers.jpg")
        if os.path.exists(path):
            try:
                self._img_orig = Image.open(path).convert("RGB")
            except Exception:
                self._img_orig = None

    def _center(self, w, h):
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        self._win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _on_resize(self, event):
        self._win_w = event.width
        self._win_h = event.height
        self._render_bg()
        self._canvas.coords(self._title_id, self._win_w // 2, 45)
        self._canvas.coords(self._status_id,
                            self._win_w // 2, self._win_h // 2 - 20)
        self._canvas.coords(self._footer_id,
                            self._win_w // 2, self._win_h - 18)

    def _render_bg(self):
        self._canvas.delete("bg")
        if self._img_orig is None:
            return
        try:
            iw, ih = self._img_orig.size
            ww = max(self._win_w, 1)
            wh = max(self._win_h, 1)
            scale = max(ww / iw, wh / ih)
            nw = int(iw * scale)
            nh = int(ih * scale)
            resized = self._img_orig.resize((nw, nh), Image.LANCZOS)
            left = (nw - ww) // 2
            top = (nh - wh) // 2
            cropped = resized.crop((left, top, left + ww, top + wh))
            darkened = cropped.point(lambda p: int(p * 0.30))
            self._bg_photo = ImageTk.PhotoImage(darkened)
            self._canvas.create_image(0, 0, anchor=tk.NW,
                                      image=self._bg_photo, tags="bg")
            self._canvas.tag_lower("bg")
        except Exception:
            pass

    def set_progress(self, value, text=""):
        self._progress.set(value)
        self._canvas.itemconfig(self._status_id, text=text)
        self.root.update_idletasks()

    def close(self):
        self._win.destroy()
