"""Gestos personalizados entrenables.

Cada gesto se guarda como un vector de distancias normalizadas
(invarian­te a posicion, tamano y espejo) en custom_gestos.json.
Comparar = distancia euclidiana media; si esta bajo el umbral, coincide.
"""
import json
import math
import os
import sys

DIM = 13
UMBRAL_DEFAULT = 0.22

_ARCHIVO = "custom_gestos.json"


def ruta_custom():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), _ARCHIVO)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _ARCHIVO)


def _d(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def escala_palma(lm):
    s = _d(lm[0].x, lm[0].y, lm[9].x, lm[9].y)
    return s if s > 1e-6 else 1.0


def extraer_vector(lm):
    """Vector de 13 distancias normalizadas por el tamano de la palma."""
    s = escala_palma(lm)
    wx, wy = lm[0].x, lm[0].y
    vec = [_d(lm[i].x, lm[i].y, wx, wy) / s for i in (4, 8, 12, 16, 20)]
    for a, b in ((4, 8), (8, 12), (12, 16), (16, 20), (4, 12), (8, 16), (4, 20), (12, 20)):
        vec.append(_d(lm[a].x, lm[a].y, lm[b].x, lm[b].y) / s)
    return vec


def distancia(a, b):
    n = min(len(a), len(b)) or 1
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / n)


def promediar(vectores):
    n = len(vectores)
    dim = max(len(v) for v in vectores)
    return [sum(v[i] if i < len(v) else 0.0 for v in vectores) / n for i in range(dim)]


def cargar(ruta=None):
    ruta = ruta or ruta_custom()
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("gestos", [])
    except (FileNotFoundError, ValueError):
        return []
    except Exception:
        return []


def guardar(plantillas, ruta=None):
    ruta = ruta or ruta_custom()
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"gestos": plantillas}, f, indent=2, ensure_ascii=False)
    return ruta


def mejor_coincidencia(vec, plantillas, umbral_default=UMBRAL_DEFAULT):
    """Devuelve (plantilla|None, distancia_min). Coincide si dist <= umbral."""
    best, best_d = None, None
    for p in plantillas:
        v = p.get("vector")
        if not v:
            continue
        d = distancia(vec, v)
        if best_d is None or d < best_d:
            best, best_d = p, d
    if best is None:
        return None, None
    umbral = float(best.get("umbral", umbral_default))
    if best_d <= umbral:
        return best, best_d
    return None, best_d


def siguiente_id(plantillas):
    nums = []
    for p in plantillas:
        pid = str(p.get("id", ""))
        if pid.startswith("custom_"):
            try:
                nums.append(int(pid.split("_", 1)[1]))
            except ValueError:
                pass
    return "custom_%d" % (max(nums) + 1 if nums else 1)
