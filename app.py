"""GestureControl v3 - interfaz increible.
Sidebar + paginas (En vivo / Gestos / Actividad / Ajustes)
Vista previa integrada, stats de sesion, sparkline FPS, log con colores.
Uso: python app.py
"""
import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from collections import Counter

import cv2

from gesture_detector import GestureDetector, GESTOS
from action_manager import ejecutar, lista_acciones, ACCIONES

try:
    from PIL import Image, ImageTk
    _PIL = True
except Exception:
    _PIL = False

try:
    import winsound
    _SOUND = True
except Exception:
    _SOUND = False

BASE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    # .exe: recursos en _MEIPASS, config escribible junto al .exe
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    USER_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = BASE
    USER_DIR = BASE
CONFIG_PATH = os.path.join(USER_DIR, "config.json")
CONFIG_DEFAULT = os.path.join(BUNDLE_DIR, "config.json")

# ---------- paleta ----------
BG = "#0e1119"
SIDEBAR = "#151b28"
CARD = "#1a2132"
CARD2 = "#222b42"
LINE = "#2c3650"
FG = "#eef1f7"
MUTED = "#8e99b0"
ACCENT = "#00d0ff"
ACCENT2 = "#7c5cff"
GREEN = "#2fe08c"
RED = "#ff5d6c"
YELLOW = "#ffc857"

NOMBRES = {
    "mano_abierta": "Mano abierta", "puno": "Puno cerrado",
    "uno": "Un dedo", "dos_paz": "Paz",
    "tres_dedos": "Tres dedos", "cuatro_dedos": "Cuatro dedos",
    "pulgar_arriba": "Pulgar arriba", "pulgar_abajo": "Pulgar abajo",
    "ok": "OK", "rock": "Rock", "pinza": "Pinza",
    "swipe_izquierda": "Swipe izq.", "swipe_derecha": "Swipe der.",
    "swipe_arriba": "Swipe arriba", "swipe_abajo": "Swipe abajo",
}
DETALLE = {
    "mano_abierta": "5 dedos extendidos", "puno": "Mano totalmente cerrada",
    "uno": "Solo indice arriba", "dos_paz": "Indice + medio en V",
    "tres_dedos": "Indice + medio + anular", "cuatro_dedos": "4 dedos, pulgar guardado",
    "pulgar_arriba": "Pulgar vertical arriba", "pulgar_abajo": "Pulgar vertical abajo",
    "ok": "Circulo pulgar-indice", "rock": "Indice + menique",
    "pinza": "Pellizco pulgar-indice",
    "swipe_izquierda": "Barrido a tu izquierda", "swipe_derecha": "Barrido a tu derecha",
    "swipe_arriba": "Barrido hacia arriba", "swipe_abajo": "Barrido hacia abajo",
}
ICONO = {
    "mano_abierta": "5", "puno": "0", "uno": "1", "dos_paz": "2",
    "tres_dedos": "3", "cuatro_dedos": "4", "pulgar_arriba": "^",
    "pulgar_abajo": "v", "ok": "OK", "rock": "R", "pinza": "Pz",
    "swipe_izquierda": "<-", "swipe_derecha": "->",
    "swipe_arriba": "^|", "swipe_abajo": "v|",
}

DEFAULT_MAP = [
    ("mano_abierta", "play_pause", True), ("puno", "mute", True),
    ("uno", "volumen_up", True), ("dos_paz", "screenshot", True),
    ("tres_dedos", "escritorio", True), ("cuatro_dedos", "alt_tab", False),
    ("pulgar_arriba", "volumen_up", False), ("pulgar_abajo", "volumen_down", False),
    ("ok", "click_izq", True), ("rock", "abrir_youtube", True),
    ("pinza", "click_der", False), ("swipe_izquierda", "flecha_izq", False),
    ("swipe_derecha", "flecha_der", False), ("swipe_arriba", "flecha_arriba", False),
    ("swipe_abajo", "flecha_abajo", False),
]


def cargar_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def abrir_camara(preferido):
    cands = [preferido] + [i for i in [0, 1, 2, 3, 4] if i != preferido]
    backs = []
    try:
        backs.append(cv2.CAP_DSHOW)
    except Exception:
        pass
    backs.append(cv2.CAP_ANY)
    for idx in cands:
        for b in backs:
            try:
                cap = cv2.VideoCapture(idx, b)
                if not cap.isOpened():
                    cap.release()
                    continue
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ok, f = cap.read()
                if ok and f is not None:
                    return cap, idx
                cap.release()
            except Exception:
                continue
    return None, -1


def buscar_camaras():
    out = []
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_ANY)
        op = cap.isOpened()
        ok = False
        if op:
            ok, _ = cap.read()
        cap.release()
        if op and ok:
            out.append(i)
    return out


# ---------- widgets ----------
class Toggle(tk.Canvas):
    def __init__(self, parent, var, command=None, w=44, h=24):
        super().__init__(parent, width=w, height=h, bg=CARD2, highlightthickness=0, cursor="hand2")
        self.var, self.cmd, self.w, self.h = var, command, w, h
        self.bind("<Button-1>", self.flip)
        var.trace_add("write", lambda *_a: self.draw())
        self.draw()

    def flip(self, _e=None):
        self.var.set(not self.var.get())
        if self.cmd:
            self.cmd()

    def draw(self):
        self.delete("all")
        on = bool(self.var.get())
        bg = "#0e5a6e" if on else "#3a4358"
        fg = ACCENT if on else "#6b7690"
        self.create_rounded = None
        self.create_rectangle(1, 1, self.w - 1, self.h - 1, fill=bg, outline=fg, width=1)
        x = self.w - 11 if on else 11
        self.create_oval(x - 8, 4, x + 8, self.h - 4, fill=fg, outline="")


class Sparkline(tk.Canvas):
    def __init__(self, parent, w=150, h=36):
        super().__init__(parent, width=w, height=h, bg="#0f1420", highlightthickness=0)
        self.w, self.h, self.data = w, h, []

    def push(self, v):
        self.data.append(max(0, min(v, 60)))
        if len(self.data) > 60:
            self.data.pop(0)
        self.delete("all")
        if len(self.data) < 2:
            return
        pts = []
        for i, val in enumerate(self.data):
            x = i / 59 * (self.w - 4) + 2
            y = self.h - 3 - (val / 60) * (self.h - 8)
            pts += [x, y]
        self.create_line(*pts, fill=ACCENT, width=2, smooth=True)


class App:
    def __init__(self, root):
        self.root = root
        root.title("GestureControl")
        root.geometry("1280x800")
        root.minsize(1100, 680)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.cfg = cargar_config()
        self.mapa = {m["gesto"]: m for m in self.cfg.get("mappings", [])}
        for g, a, on in DEFAULT_MAP:
            if g not in self.mapa:
                self.mapa[g] = {"gesto": g, "accion": a, "activo": on}

        # estado
        self.running = False
        self.thread = None
        self.cap = None
        self.page = "envivo"
        self.total_gestos = 0
        self.total_acciones = 0
        self.por_gesto = Counter()
        self.sesion_t0 = None
        self.fps_hist = []
        self._img = None
        self.var_cam = tk.IntVar(value=self.cfg.get("camara", 1))
        self.var_cooldown = tk.DoubleVar(value=self.cfg.get("cooldown_seg", 1.5))
        self.var_frames = tk.IntVar(value=self.cfg.get("frames_estables", 5))
        self.var_sonido = tk.BooleanVar(value=self.cfg.get("sonido", True))
        self.var_buscar = tk.StringVar()
        self.var_filtro = tk.StringVar(value="Todos")
        self.var_buscar.trace_add("write", lambda *_a: self._filtrar_gestos())

        self._estilo()
        self._layout()
        self.show_page("envivo")
        self.log("Bienvenido. Elige tus gestos y pulsa INICIAR.", "sys")
        self._tick_reloj()
        self._pulso()

    # ---------- estilo ----------
    def _estilo(self):
        s = ttk.Style(self.root)
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        s.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("TButton", font=("Segoe UI", 10, "bold"), padding=7)
        s.configure("Accent.TButton", background=ACCENT, foreground="#052530")
        s.map("Accent.TButton", background=[("active", "#4fdcff"), ("disabled", "#23414d")])
        s.configure("Ghost.TButton", background=CARD2, foreground=FG)
        s.configure("Danger.TButton", background="#3a2230", foreground="#ff9aab")
        s.configure("TCombobox", fieldbackground="#0d1220", background="#0d1220", foreground=FG,
                    arrowcolor=ACCENT)
        s.configure("Horizontal.TScale", background=CARD)
        s.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor="#0d1220")

    # ---------- layout base ----------
    def _layout(self):
        # sidebar
        side = tk.Frame(self.root, bg=SIDEBAR, width=210)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="GestureControl", bg=SIDEBAR, fg=FG,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(side, text="vision + manos + acciones", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 14))
        self.nav_btns = {}
        for key, txt, sub in [("envivo", "En vivo", "camara y deteccion"),
                              ("gestos", "Gestos", "15 gestos -> accion"),
                              ("actividad", "Actividad", "historial y stats"),
                              ("ajustes", "Ajustes", "camara y sistema")]:
            b = tk.Button(side, bg=SIDEBAR, fg=MUTED, anchor="w", relief="flat",
                          activebackground=CARD2, activeforeground=FG, cursor="hand2",
                          font=("Segoe UI", 11, "bold"),
                          text=f"  {txt}\n      {sub}",
                          justify="left", command=lambda k=key: self.show_page(k))
            b.pack(fill="x", padx=8, pady=2, ipady=6)
            self.nav_btns[key] = b
        tk.Frame(side, bg=LINE, height=1).pack(fill="x", padx=16, pady=12)
        self.side_status = tk.Label(side, text="● detenido", bg=SIDEBAR, fg=RED,
                                    font=("Segoe UI", 10, "bold"))
        self.side_status.pack(anchor="w", padx=16)
        tk.Label(side, text="v3 increible · MediaPipe + OpenCV",
                 bg=SIDEBAR, fg=MUTED, font=("Segoe UI", 8)).pack(side="bottom", pady=12)

        # area derecha
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        # topbar
        top = tk.Frame(main, bg=BG)
        top.pack(fill="x", padx=18, pady=(14, 6))
        self.lbl_title = tk.Label(top, text="En vivo", bg=BG, fg=FG, font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(side="left")
        self.lbl_subtitle = tk.Label(top, text="", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self.lbl_subtitle.pack(side="left", padx=10, pady=(8, 0))
        self.pill = tk.Label(top, text="DETENIDO", bg="#2a1e26", fg=RED,
                             font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.pill.pack(side="right", padx=6)
        self.lbl_fps_top = tk.Label(top, text="-- FPS", bg=BG, fg=MUTED, font=("Segoe UI", 10, "bold"))
        self.lbl_fps_top.pack(side="right", padx=6)
        self.lbl_backend = tk.Label(top, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.lbl_backend.pack(side="right", padx=6)

        # contenedor paginas
        self.holder = tk.Frame(main, bg=BG)
        self.holder.pack(fill="both", expand=True, padx=18, pady=8)
        self.pages = {}
        for k in ("envivo", "gestos", "actividad", "ajustes"):
            f = tk.Frame(self.holder, bg=BG)
            self.pages[k] = f
        self._build_envivo()
        self._build_gestos()
        self._build_actividad()
        self._build_ajustes()

    def show_page(self, key):
        self.page = key
        for k, f in self.pages.items():
            f.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        tit = {"envivo": ("En vivo", "Tu mano en tiempo real"),
               "gestos": ("Gestos", "Que hace cada gesto"),
               "actividad": ("Actividad", "Que paso en tu sesion"),
               "ajustes": ("Ajustes", "Camara, tiempos y sistema")}[key]
        self.lbl_title.config(text=tit[0])
        self.lbl_subtitle.config(text=tit[1])
        for k, b in self.nav_btns.items():
            b.config(bg=CARD2 if k == key else SIDEBAR,
                     fg=FG if k == key else MUTED)

    # ---------- pagina EN VIVO ----------
    def _build_envivo(self):
        p = self.pages["envivo"]
        p.columnconfigure(0, weight=8)
        p.columnconfigure(1, weight=4)

        # video card
        vc = tk.Frame(p, bg=CARD, padx=14, pady=12)
        vc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        p.rowconfigure(0, weight=1)
        tk.Label(vc, text="CAMARA EN VIVO", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_video = tk.Label(vc, bg="#080b12", fg=MUTED,
                                  text="Pulsa INICIAR para ver tu mano aqui",
                                  width=64, height=20)
        self.lbl_video.pack(fill="both", expand=True, pady=8)
        # barra de progreso de confirmacion + sparkline
        brow = tk.Frame(vc, bg=CARD)
        brow.pack(fill="x")
        tk.Label(brow, text="Confirmacion:", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self.bar_conf = ttk.Progressbar(brow, mode="determinate", maximum=100,
                                        style="Horizontal.TProgressbar", length=220)
        self.bar_conf.pack(side="left", padx=8)
        tk.Label(brow, text="FPS:", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(12, 4))
        self.spark = Sparkline(brow, w=150, h=30)
        self.spark.pack(side="left")

        # columna derecha
        rc = tk.Frame(p, bg=BG)
        rc.grid(row=0, column=1, sticky="nsew")
        # gesto actual
        gc = tk.Frame(rc, bg=CARD2, padx=14, pady=12)
        gc.pack(fill="x")
        tk.Label(gc, text="GESTO ACTUAL", bg=CARD2, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_gesto = tk.Label(gc, text="—", bg=CARD2, fg=ACCENT,
                                  font=("Segoe UI", 28, "bold"))
        self.lbl_gesto.pack(anchor="w")
        self.lbl_gesto_det = tk.Label(gc, text="esperando deteccion…", bg=CARD2, fg=MUTED,
                                      font=("Segoe UI", 10), wraplength=260, justify="left")
        self.lbl_gesto_det.pack(anchor="w")
        self.lbl_accion = tk.Label(gc, text="", bg="#0d2b36", fg=ACCENT,
                                   font=("Segoe UI", 10, "bold"), padx=8, pady=4)
        self.lbl_accion.pack(anchor="w", pady=(8, 0))

        # stats 2x2
        sc = tk.Frame(rc, bg=BG)
        sc.pack(fill="x", pady=8)
        self.stat_vars = {}
        for i, (k, t) in enumerate([("fps", "FPS"), ("gestos", "Gestos"),
                                    ("acciones", "Acciones"), ("tiempo", "Tiempo")]):
            c = tk.Frame(sc, bg=CARD, padx=10, pady=8)
            c.grid(row=i // 2, column=i % 2, sticky="nsew", padx=2, pady=2)
            sc.columnconfigure(i % 2, weight=1)
            tk.Label(c, text=t.upper(), bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            v = tk.Label(c, text="0", bg=CARD, fg=FG, font=("Segoe UI", 16, "bold"))
            v.pack(anchor="w")
            self.stat_vars[k] = v

        # botones
        self.btn_start = tk.Button(rc, text="INICIAR DETECCION", bg=ACCENT, fg="#052530",
                                   font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
                                   pady=10, command=self.iniciar)
        self.btn_start.pack(fill="x", pady=(2, 6))
        self.btn_stop = tk.Button(rc, text="Detener", bg=CARD, fg=FG,
                                  font=("Segoe UI", 10), relief="flat", cursor="hand2",
                                  pady=8, command=self.detener)
        self.btn_stop.pack(fill="x")
        # sonido
        srow = tk.Frame(rc, bg=BG)
        srow.pack(fill="x", pady=8)
        tk.Label(srow, text="Sonido al detectar:", bg=BG, fg=MUTED).pack(side="left")
        Toggle(srow, self.var_sonido).pack(side="right")

    # ---------- pagina GESTOS ----------
    def _build_gestos(self):
        p = self.pages["gestos"]
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        self.ent_search = tk.Entry(bar, textvariable=self.var_buscar, bg="#0d1220", fg=FG,
                                   insertbackground=FG, relief="flat", font=("Segoe UI", 11))
        self.ent_search.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.ent_search.insert(0, "")
        # placeholder simple
        ttk.Combobox(bar, textvariable=self.var_filtro, width=12, state="readonly",
                     values=["Todos", "Activos", "Inactivos"]).pack(side="left", padx=4)
        self.var_filtro.trace_add("write", lambda *_a: self._filtrar_gestos())
        tk.Button(bar, text="Guardar todo", bg=ACCENT, fg="#052530",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=lambda: self.guardar()).pack(side="left", padx=4)
        self.lbl_gcount = tk.Label(bar, text="", bg=BG, fg=MUTED)
        self.lbl_gcount.pack(side="left", padx=8)

        # scroll grid
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True)
        self.g_canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.g_canvas.yview)
        self.g_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.g_canvas.pack(side="left", fill="both", expand=True)
        self.g_inner = tk.Frame(self.g_canvas, bg=BG)
        self.g_canvas.create_window((0, 0), window=self.g_inner, anchor="nw")
        self.g_inner.bind("<Configure>", lambda _e: self.g_canvas.configure(scrollregion=self.g_canvas.bbox("all")))
        # mousewheel windows
        self.g_canvas.bind_all("<MouseWheel>", lambda e: self.g_canvas.yview_scroll(int(-e.delta / 120), "units"))

        self.g_cards = {}
        self.filas = {}
        acciones = lista_acciones()
        for g in GESTOS:
            card = tk.Frame(self.g_inner, bg=CARD, padx=12, pady=10)
            # grid 3 columnas
            idx = GESTOS.index(g)
            card.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=5, pady=5)
            self.g_inner.columnconfigure(idx % 3, weight=1)
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x")
            badge = tk.Label(top, text=ICONO.get(g, "?"), bg="#0d2b36", fg=ACCENT,
                             font=("Segoe UI", 12, "bold"), width=4, pady=4)
            badge.pack(side="left")
            m = self.mapa[g]
            var_on = tk.BooleanVar(value=bool(m.get("activo", True)))
            Toggle(top, var_on, command=self._conteo_gestos).pack(side="right")
            tk.Label(card, text=NOMBRES.get(g, g), bg=CARD, fg=FG,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 0))
            tk.Label(card, text=DETALLE.get(g, ""), bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9), wraplength=220, justify="left").pack(anchor="w")
            cb = ttk.Combobox(card, values=acciones, state="readonly", width=24)
            actual = m.get("accion", "nada")
            if actual not in acciones:
                cb["values"] = acciones + [actual]
            cb.set(actual)
            cb.pack(fill="x", pady=6)
            tk.Button(card, text="Probar accion", bg=CARD2, fg=FG, relief="flat",
                      cursor="hand2", command=lambda gg=g: self.probar_accion(gg)).pack(fill="x")
            # hover
            for w in (card,):
                w.bind("<Enter>", lambda e, c=card: c.config(bg=CARD2))
                w.bind("<Leave>", lambda e, c=card: c.config(bg=CARD))
            self.g_cards[g] = card
            self.filas[g] = (var_on, cb)
        self._conteo_gestos()
        self._filtrar_gestos()

    def _conteo_gestos(self):
        try:
            n = sum(1 for v, _c in self.filas.values() if v.get())
            self.lbl_gcount.config(text=f"{n}/{len(self.filas)} activos")
        except Exception:
            pass

    def _filtrar_gestos(self):
        q = self.var_buscar.get().lower().strip()
        f = self.var_filtro.get()
        for g, card in self.g_cards.items():
            var_on, cb = self.filas[g]
            txt = (NOMBRES.get(g, g) + " " + g + " " + cb.get()).lower()
            ok_q = (q in txt) if q else True
            ok_f = True
            if f == "Activos":
                ok_f = bool(var_on.get())
            elif f == "Inactivos":
                ok_f = not bool(var_on.get())
            if ok_q and ok_f:
                card.grid()
            else:
                card.grid_remove()

    # ---------- pagina ACTIVIDAD ----------
    def _build_actividad(self):
        p = self.pages["actividad"]
        row = tk.Frame(p, bg=BG)
        row.pack(fill="x", pady=(0, 8))
        self.lbl_atotal = tk.Label(row, text="0 gestos · 0 acciones", bg=CARD, fg=FG,
                                   font=("Segoe UI", 11, "bold"), padx=14, pady=8)
        self.lbl_atotal.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(row, text="Limpiar", bg=CARD2, fg=FG, relief="flat", cursor="hand2",
                  padx=14, command=self._limpiar_log).pack(side="left", padx=3)
        tk.Button(row, text="Exportar .txt", bg=CARD2, fg=FG, relief="flat", cursor="hand2",
                  padx=14, command=self._exportar_log).pack(side="left", padx=3)
        self.txt_log = tk.Text(p, bg="#0b0f18", fg="#cdd6e4", font=("Consolas", 10),
                               wrap="word", state="disabled", relief="flat", padx=10, pady=10)
        self.txt_log.pack(fill="both", expand=True)
        for tag, col in [("ok", GREEN), ("gesto", ACCENT), ("sys", MUTED), ("warn", YELLOW), ("err", RED)]:
            self.txt_log.tag_config(tag, foreground=col)

    def _limpiar_log(self):
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.config(state="disabled")

    def _exportar_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Texto", "*.txt")],
                                            initialfile="gesturecontrol_log.txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.txt_log.get("1.0", "end"))
            self.log("Registro exportado.", "sys")

    # ---------- pagina AJUSTES ----------
    def _build_ajustes(self):
        p = self.pages["ajustes"]
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        # camara
        c1 = tk.Frame(p, bg=CARD, padx=14, pady=12)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=6)
        tk.Label(c1, text="CAMARA", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        r = tk.Frame(c1, bg=CARD)
        r.pack(fill="x", pady=6)
        tk.Label(r, text="Indice:", bg=CARD, fg=FG).pack(side="left")
        ttk.Spinbox(r, from_=0, to=4, width=5, textvariable=self.var_cam).pack(side="left", padx=8)
        tk.Button(r, text="Detectar", bg=CARD2, fg=FG, relief="flat", cursor="hand2",
                  command=self.detectar_camaras).pack(side="left")
        self.lbl_cams = tk.Label(c1, text="Tip: si ves negro, prueba 0, 1 o 2.",
                                 bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=300,
                                 justify="left")
        self.lbl_cams.pack(anchor="w")
        # tiempos
        c2 = tk.Frame(p, bg=CARD, padx=14, pady=12)
        c2.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=6)
        tk.Label(c2, text="TIEMPOS", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(c2, text="Cooldown (evita repeticiones):", bg=CARD, fg=FG).pack(anchor="w", pady=(6, 0))
        ttk.Scale(c2, from_=0.5, to=4.0, variable=self.var_cooldown, orient="horizontal").pack(fill="x")
        tk.Label(c2, text="Frames estables (precision):", bg=CARD, fg=FG).pack(anchor="w", pady=(6, 0))
        ttk.Scale(c2, from_=2, to=10, variable=self.var_frames, orient="horizontal").pack(fill="x")
        self.lbl_vals = tk.Label(c2, text="", bg=CARD, fg=ACCENT, font=("Segoe UI", 10, "bold"))
        self.lbl_vals.pack(anchor="w", pady=4)
        self.var_cooldown.trace_add("write", lambda *_a: self._upd_vals())
        self.var_frames.trace_add("write", lambda *_a: self._upd_vals())
        self._upd_vals()
        # sistema
        c3 = tk.Frame(p, bg=CARD, padx=14, pady=12)
        c3.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=6)
        tk.Label(c3, text="SISTEMA", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        try:
            import mediapipe as _mp
            mpv = getattr(_mp, "__version__", "?")
        except Exception:
            mpv = "?"
        self.lbl_backend = tk.Label(c3, text=f"MediaPipe {mpv} · OpenCV {cv2.__version__}",
                                    bg=CARD, fg=FG)
        self.lbl_backend.pack(anchor="w", pady=4)
        self.lbl_model = tk.Label(c3, text="", bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.lbl_model.pack(anchor="w")
        mp_ = os.path.join(BASE, "hand_landmarker.task")
        self.lbl_model.config(text=f"Modelo: {'OK (' + mp_ + ')' if os.path.exists(mp_) else 'se descargara al iniciar'}")
        srow = tk.Frame(c3, bg=CARD)
        srow.pack(fill="x", pady=6)
        tk.Label(srow, text="Sonido al detectar", bg=CARD, fg=FG).pack(side="left")
        Toggle(srow, self.var_sonido).pack(side="right")
        # guardar
        c4 = tk.Frame(p, bg=CARD, padx=14, pady=12)
        c4.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=6)
        tk.Label(c4, text="CONFIGURACION", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Button(c4, text="GUARDAR TODO", bg=ACCENT, fg="#052530",
                  font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                  pady=8, command=lambda: self.guardar()).pack(fill="x", pady=6)
        tk.Button(c4, text="Restablecer valores", bg=CARD2, fg=FG, relief="flat",
                  cursor="hand2", command=self.restablecer).pack(fill="x")
        tk.Label(c4, text="config.json se guarda automaticamente al iniciar.",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 8), wraplength=300).pack(pady=6)

    def _upd_vals(self):
        try:
            self.lbl_vals.config(text=f"{float(self.var_cooldown.get()):.1f}s  ·  {int(float(self.var_frames.get()))} frames")
        except Exception:
            pass

    # ---------- logica ----------
    def log(self, msg, tag="sys"):
        hora = datetime.now().strftime("%H:%M:%S")
        try:
            self.txt_log.config(state="normal")
            self.txt_log.insert("end", f"[{hora}] {msg}\n", tag)
            self.txt_log.see("end")
            self.txt_log.config(state="disabled")
        except Exception:
            pass

    def detectar_camaras(self):
        self.log("Buscando camaras…", "sys")
        found = buscar_camaras()
        if not found:
            messagebox.showwarning("Camara", "Ninguna camara responde.\nPermisos de Windows y cierra Zoom/Teams.")
            self.lbl_cams.config(text="Ninguna encontrada.")
            self.log("Sin camaras.", "err")
        else:
            self.var_cam.set(found[0])
            self.lbl_cams.config(text=f"Encontradas: {found} · usando {found[0]}")
            self.log(f"Camaras: {found}", "ok")

    def probar_accion(self, gesto):
        _on, cb = self.filas[gesto]
        acc = cb.get().strip()
        self.log(f"Prueba {NOMBRES.get(gesto, gesto)} -> {acc}", "gesto")
        ejecutar(acc)

    def guardar(self):
        maps = []
        for g in GESTOS:
            var_on, cb = self.filas[g]
            maps.append({"gesto": g, "accion": cb.get().strip(), "activo": bool(var_on.get())})
        self.cfg.update({"mappings": maps, "cooldown_seg": float(self.var_cooldown.get()),
                         "frames_estables": int(float(self.var_frames.get())),
                         "camara": int(self.var_cam.get()), "sonido": bool(self.var_sonido.get())})
        guardar_config(self.cfg)
        self.mapa = {m["gesto"]: m for m in maps}
        self._conteo_gestos()
        self.log("Configuracion guardada.", "ok")
        messagebox.showinfo("Guardado", f"Guardado en\n{CONFIG_PATH}")

    def restablecer(self):
        if not messagebox.askyesno("Restablecer", "Volver a los valores por defecto?"):
            return
        for g, a, on in DEFAULT_MAP:
            var_on, cb = self.filas[g]
            var_on.set(on)
            cb.set(a)
        self.var_cooldown.set(1.5)
        self.var_frames.set(5)
        self._conteo_gestos()
        self._upd_vals()

    def iniciar(self):
        if self.running:
            return
        if not _PIL:
            messagebox.showwarning("Video", "Instala pillow: pip install pillow")
        self.guardar_silencioso()
        self.running = True
        self.sesion_t0 = time.time()
        self._ui_estado(True)
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self.log("Deteccion iniciada.", "ok")
        self.show_page("envivo")

    def guardar_silencioso(self):
        maps = []
        for g in GESTOS:
            var_on, cb = self.filas[g]
            maps.append({"gesto": g, "accion": cb.get().strip(), "activo": bool(var_on.get())})
        self.mapa = {m["gesto"]: m for m in maps}
        self.cfg.update({"mappings": maps, "cooldown_seg": float(self.var_cooldown.get()),
                         "frames_estables": int(float(self.var_frames.get())),
                         "camara": int(self.var_cam.get()), "sonido": bool(self.var_sonido.get())})
        guardar_config(self.cfg)

    def detener(self):
        self.running = False
        self._ui_estado(False)
        self.log("Deteccion detenida.", "sys")

    def _ui_estado(self, on):
        self.pill.config(text="EN VIVO" if on else "DETENIDO",
                         bg="#0d3327" if on else "#2a1e26",
                         fg=GREEN if on else RED)
        self.side_status.config(text="● en vivo" if on else "● detenido",
                                fg=GREEN if on else RED)
        self.btn_start.config(state="disabled" if on else "normal")
        self.btn_stop.config(state="normal" if on else "disabled")

    def cerrar(self):
        self.running = False
        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        self.root.destroy()

    def _tick_reloj(self):
        if self.sesion_t0 and self.running:
            s = int(time.time() - self.sesion_t0)
            self.stat_vars["tiempo"].config(text=f"{s // 60}:{s % 60:02d}")
            self.lbl_atotal.config(text=f"{self.total_gestos} gestos · {self.total_acciones} acciones")
        self.root.after(1000, self._tick_reloj)

    def _pulso(self):
        # latido del punto lateral cuando esta en vivo
        if self.running:
            c = self.side_status.cget("fg")
            self.side_status.config(fg=GREEN if c == "#1d7a4e" else "#1d7a4e")
        self.root.after(700, self._pulso)

    # ---------- video loop ----------
    def _loop(self):
        cd = float(self.var_cooldown.get())
        cam_id = int(self.var_cam.get())
        fest = int(float(self.var_frames.get()))
        try:
            det = GestureDetector()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("IA", f"No inicio el detector:\n{e}"))
            self.root.after(0, self.detener)
            return
        self.root.after(0, lambda b=getattr(det, "backend", "?"): self.lbl_backend.config(text=f"IA: {b}"))
        cap, usado = abrir_camara(cam_id)
        if cap is None:
            self.root.after(0, lambda: messagebox.showerror("Camara", "Sin camara (0-4). Revisa permisos."))
            self.root.after(0, self.detener)
            return
        self.cap = cap
        if usado != cam_id:
            self.root.after(0, lambda u=usado: self.var_cam.set(u))
        self.root.after(0, lambda: self.log(f"Camara {usado} lista.", "ok"))
        cand, racha, ult = None, 0, 0
        t0, nf = time.time(), 0
        while self.running:
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue
            frame = cv2.flip(frame, 1)
            frame, gesto = det.detect(frame)
            if gesto:
                cand, racha = (gesto, racha + 1) if gesto == cand else (gesto, 1)
            else:
                cand, racha = None, 0
            # progreso
            pv = int(min(racha / max(fest, 1), 1.0) * 100)
            self.root.after(0, lambda v=pv: self.bar_conf.config(value=v))
            if cand:
                c = cand
                self.root.after(0, lambda cc=c: self._pintar_cand(cc))
            if cand and racha >= fest:
                m = self.mapa.get(cand, {})
                ahora = time.time()
                if m.get("activo") and (ahora - ult) > cd:
                    acc = m.get("accion", "nada")
                    ejecutar(acc)
                    ult = ahora
                    self.total_gestos += 1
                    self.total_acciones += 1
                    self.por_gesto[cand] += 1
                    g, a = cand, acc
                    self.root.after(0, lambda gg=g, aa=a: self._pintar_hit(gg, aa))
                    self.root.after(0, lambda gg=g, aa=a: self.log(f"{NOMBRES.get(gg, gg)} -> {aa}", "gesto"))
                    if self.var_sonido.get() and _SOUND:
                        try:
                            winsound.Beep(880, 110)
                        except Exception:
                            pass
                    cand, racha = None, 0
            nf += 1
            if time.time() - t0 >= 1.0:
                fps = nf / max(time.time() - t0, 0.01)
                t0, nf = time.time(), 0
                self.root.after(0, lambda f=fps: self._pintar_fps(f))
            # etiqueta + marco
            cv2.putText(frame, cand or "", (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 208, 255), 2)
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 208, 255), 2)
            self._frame(frame)
        try:
            cap.release()
        except Exception:
            pass
        self.cap = None
        self.root.after(0, self.detener)

    def _pintar_cand(self, c):
        self.lbl_gesto.config(text=NOMBRES.get(c, c))
        self.lbl_gesto_det.config(text=DETALLE.get(c, ""))

    def _pintar_hit(self, g, a):
        self.lbl_gesto.config(text=NOMBRES.get(g, g))
        self.lbl_gesto_det.config(text=DETALLE.get(g, ""))
        self.lbl_accion.config(text=f"→ {ACCIONES.get(a, a)}")
        self.stat_vars["gestos"].config(text=str(self.total_gestos))
        self.stat_vars["acciones"].config(text=str(self.total_acciones))
        self.lbl_atotal.config(text=f"{self.total_gestos} gestos · {self.total_acciones} acciones")
        # pop visual
        self.lbl_gesto.config(font=("Segoe UI", 30, "bold"))
        self.root.after(180, lambda: self.lbl_gesto.config(font=("Segoe UI", 28, "bold")))

    def _pintar_fps(self, f):
        self.lbl_fps_top.config(text=f"{f:.0f} FPS")
        self.stat_vars["fps"].config(text=f"{f:.0f}")
        try:
            self.spark.push(f)
        except Exception:
            pass

    def _frame(self, frame):
        if not _PIL:
            return
        try:
            cw = self.lbl_video.winfo_width()
            if cw < 60:
                cw = 620
            h, w, _ = frame.shape
            sc = min(cw / w, 420 / h)
            small = cv2.resize(frame, (max(1, int(w * sc)), max(1, int(h * sc))))
            img = Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
            tkimg = ImageTk.PhotoImage(image=img)
            self._img = tkimg
            self.root.after(0, lambda: self.lbl_video.config(image=tkimg, text=""))
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
