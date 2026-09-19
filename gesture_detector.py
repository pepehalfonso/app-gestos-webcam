"""Detector de gestos con MediaPipe + OpenCV. v2 mas estricta.
Compatible con mediapipe 0.10.x (solutions.hands) y 1.x (tasks).
Mejoras vs v1:
- Dedo arriba/abajo con margen + distancia a muneca (robusto a rotacion)
- Pulgar extendido con doble chequeo (lateral + distancia a palma)
- Patrones estrictos (tres_dedos exige indice+medio+anular, no cualquier 3)
- OK vs pinza separados por umbrales no solapados + resto de dedos
- Pulgar arriba/abajo exige verticalidad clara, si no -> None (no adivina)
- Suavizado por mayoria (4 de ultimos 6) para evitar parpadeo
- Swipes mas estrictos (0.20) + anti-rebote 1s + solo si movimiento lineal
"""
import math
import os
import sys
import time
import urllib.request
from collections import deque, Counter
import cv2
import mediapipe as mp


GESTOS = [
    "mano_abierta",
    "puno",
    "uno",
    "dos_paz",
    "tres_dedos",
    "cuatro_dedos",
    "pulgar_arriba",
    "pulgar_abajo",
    "ok",
    "rock",
    "pinza",
    "swipe_izquierda",
    "swipe_derecha",
    "swipe_arriba",
    "swipe_abajo",
]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")


def _resolver_modelo():
    """Dentro del .exe el modelo va en _MEIPASS; si no esta, junto al .exe."""
    if getattr(sys, "frozen", False):
        cand_bundle = os.path.join(getattr(sys, "_MEIPASS", ""), "hand_landmarker.task")
        if cand_bundle and os.path.exists(cand_bundle):
            return cand_bundle
        cand_exe = os.path.join(os.path.dirname(sys.executable), "hand_landmarker.task")
        return cand_exe
    return MODEL_PATH

MARGEN_Y = 0.018  # margen para decidir arriba/abajo, evita borde


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _tiene_solutions():
    try:
        return hasattr(mp, "solutions") and hasattr(mp.solutions, "hands")
    except Exception:
        return False


def _dibujar_mano_cv2(frame, lm, conexiones):
    h, w, _ = frame.shape
    pts = [(int(p.x * w), int(p.y * h)) for p in lm]
    for c in conexiones:
        try:
            s, e = c.start, c.end
        except Exception:
            s, e = c[0], c[1]
        cv2.line(frame, pts[s], pts[e], (0, 255, 0), 2)
    for (x, y) in pts:
        cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)


class GestureDetector:
    def __init__(self, detection_conf=0.6, track_conf=0.5):
        self.hist = deque(maxlen=15)
        self._smooth = deque(maxlen=6)
        self._last_swipe_t = 0
        self._frames_tras_swipe = 999
        self.backend = "none"
        self._t0 = time.time()

        if _tiene_solutions():
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5,
                )
                self.mp_draw = mp.solutions.drawing_utils
                self.backend = "solutions"
                print("[gestos] backend: solutions.hands (0.10.x)")
                return
            except Exception as e:
                print(f"[gestos] solutions fallo, pruebo tasks: {e}")

        try:
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core import base_options
        except ImportError:
            from mediapipe.tasks.python import vision  # noqa
            from mediapipe.tasks.python.core import base_options

        model_path = _resolver_modelo()
        if not os.path.exists(model_path):
            print("[gestos] descargando modelo hand_landmarker.task (~8MB)...")
            try:
                os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
                urllib.request.urlretrieve(MODEL_URL, model_path)
                print("[gestos] modelo descargado.")
            except Exception as e:
                raise RuntimeError(f"No se pudo descargar el modelo: {e}")

        from mediapipe.tasks.python import vision as _vision
        from mediapipe.tasks.python.core import base_options as _bo
        opts = _vision.HandLandmarkerOptions(
            base_options=_bo.BaseOptions(model_asset_path=model_path),
            running_mode=_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=detection_conf,
            min_hand_presence_confidence=detection_conf,
            min_tracking_confidence=track_conf,
        )
        self._vision = _vision
        self.landmarker = _vision.HandLandmarker.create_from_options(opts)
        try:
            self._conex = list(_vision.HandLandmarksConnections.HAND_CONNECTIONS)
        except Exception:
            self._conex = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]
        self.backend = "tasks"
        print("[gestos] backend: tasks HandLandmarker (1.x)")

    # ---------- nivel bajo ----------
    def _dedo_estado(self, tip, pip, mcp, wrist):
        """True=arriba claro, False=abajo claro, None=dudoso."""
        dy = pip.y - tip.y  # >0 significa punta arriba de nudillo
        d_tip = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
        d_pip = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
        # claramente arriba: punta alta + mas lejos de muneca
        if dy > MARGEN_Y and d_tip > d_pip * 1.02:
            return True
        # claramente abajo: punta baja o mucho mas cerca de muneca (enrollado)
        if dy < -MARGEN_Y * 0.5 or d_tip < d_pip * 0.95:
            # exigir que sea claramente abajo, no borde
            if dy < 0.005 or d_tip < d_pip:
                return False
        return None

    def _pulgar_extendido(self, lm, handedness):
        # chequeo 1: lateralidad segun mano
        if handedness == "Right":
            lateral = lm[3].x - lm[4].x  # >0 si pulgar a la izquierda (extendido)
        else:
            lateral = lm[4].x - lm[3].x
        # chequeo 2: punta lejos de la palma (punto 9 = centro palma)
        d_tip_palma = _dist(lm[4], lm[9])
        d_ip_palma = _dist(lm[3], lm[9])
        ext_por_dist = d_tip_palma > d_ip_palma * 1.15 and d_tip_palma > 0.08
        ext_por_lat = lateral > 0.02
        return ext_por_dist and ext_por_lat

    def _dedos_arriba(self, lm, handedness):
        w = lm[0]
        i = self._dedo_estado(lm[8], lm[6], lm[5], w)
        m = self._dedo_estado(lm[12], lm[10], lm[9], w)
        r = self._dedo_estado(lm[16], lm[14], lm[13], w)
        p = self._dedo_estado(lm[20], lm[18], lm[17], w)
        t_ext = self._pulgar_extendido(lm, handedness)
        return i, m, r, p, t_ext

    # ---------- clasificador estricto ----------
    def _estatico_raw(self, lm, handedness):
        i_up, m_up, r_up, p_up, t_ext = self._dedos_arriba(lm, handedness)
        d_4_8 = _dist(lm[4], lm[8])
        d_8_12 = _dist(lm[8], lm[12])
        d_8_20 = _dist(lm[8], lm[20])

        # --- gestos distintivos primero ---
        # OK: pulgar-indice pegados + los otros 3 ARRIBA claros
        if d_4_8 < 0.045 and m_up is True and r_up is True and p_up is True:
            if _dist(lm[4], lm[12]) > 0.07:  # circulo no colapsado
                return "ok"
        # PINZA: pegados pero los otros 3 ABAJO claros (no solapa con OK)
        # + indice no totalmente enrollado (dist a muneca) para no confundir con puno
        if 0.015 < d_4_8 < 0.06 and m_up is False and r_up is False and p_up is False:
            d_tip8_wrist = math.hypot(lm[8].x - lm[0].x, lm[8].y - lm[0].y)
            dy_8_6 = lm[8].y - lm[6].y  # en pinza no muy enrollado (<0.12), en puno ~0.25
            if d_tip8_wrist > 0.24 and dy_8_6 < 0.12 and abs(lm[4].y - lm[8].y) < 0.09:
                return "pinza"
        # ROCK: indice y menique arriba, medio+anular abajo, bien separados
        if i_up is True and p_up is True and m_up is False and r_up is False:
            if d_8_20 > 0.07 and d_4_8 > 0.06:
                return "rock"
        # PULGAR: solo si resto abajo claro + verticalidad clara
        if i_up is False and m_up is False and r_up is False and p_up is False and t_ext:
            dy = lm[3].y - lm[4].y  # >0 pulgar apunta arriba
            dx = abs(lm[4].x - lm[3].x)
            nudillos_y = (lm[6].y + lm[10].y + lm[14].y + lm[18].y) / 4.0
            if dy > 0.06 and abs(dy) > dx * 1.2 and lm[4].y < nudillos_y - 0.05:
                return "pulgar_arriba"
            if dy < -0.06 and abs(dy) > dx * 1.2 and lm[4].y > nudillos_y + 0.05:
                return "pulgar_abajo"
            return None  # pulgar extendido pero sin direccion clara -> no adivinar

        # --- resto: exigir estados claros, si hay dudoso -> None ---
        if None in (i_up, m_up, r_up, p_up):
            return None
        count = sum([i_up, m_up, r_up, p_up])

        if count == 4 and t_ext and d_8_12 > 0.03:
            return "mano_abierta"
        if count == 0 and not t_ext and d_4_8 > 0.045:
            return "puno"
        if i_up and not m_up and not r_up and not p_up and not t_ext and d_4_8 > 0.07:
            return "uno"
        if i_up and m_up and not r_up and not p_up and not t_ext:
            if d_8_12 > 0.035 and d_4_8 > 0.06:  # V separada
                return "dos_paz"
            return None
        # tres: EXACTO indice+medio+anular, menique abajo (antes aceptaba cualquier 3)
        if i_up and m_up and r_up and not p_up and not t_ext:
            return "tres_dedos"
        if count == 4 and not t_ext:
            return "cuatro_dedos"
        return None

    def _suavizado(self, raw):
        self._smooth.append(raw)
        if len(self._smooth) < 4:
            return None
        c = Counter([g for g in self._smooth if g is not None])
        if not c:
            return None
        top, n = c.most_common(1)[0]
        # exigir 3 de ultimos 6 para aceptar
        if n >= 3 and self._smooth[-1] == top:
            return top
        return None

    def _swipe(self):
        self._frames_tras_swipe += 1
        if self._frames_tras_swipe < 10:
            return None
        if len(self.hist) < 10:
            return None
        ahora = time.time()
        if ahora - self._last_swipe_t < 1.0:
            return None
        # desplazamiento en ultimos 6 frames (movimiento reciente, no deriva lenta)
        x0, y0 = self.hist[-6]
        x1, y1 = self.hist[-1]
        dx = x1 - x0
        dy = y1 - y0
        if abs(dx) < 0.20 and abs(dy) < 0.16:
            return None
        # linealidad: puntos intermedios deben ir en misma direccion
        xs = [p[0] for p in list(self.hist)[-6:]]
        ys = [p[1] for p in list(self.hist)[-6:]]
        if abs(dx) > abs(dy) * 1.6:
            # monotono en x?
            pasos = sum(1 for a, b in zip(xs, xs[1:]) if (b - a) * dx > 0)
            if pasos < 3:
                return None
            return "swipe_derecha" if dx > 0 else "swipe_izquierda"
        if abs(dy) > abs(dx) * 1.6:
            pasos = sum(1 for a, b in zip(ys, ys[1:]) if (b - a) * dy > 0)
            if pasos < 3:
                return None
            return "swipe_abajo" if dy > 0 else "swipe_arriba"
        return None

    def _procesar(self, lm, handedness, frame):
        self.hist.append((lm[0].x, lm[0].y))
        raw = self._estatico_raw(lm, handedness)
        s = self._swipe()
        if s:
            self._last_swipe_t = time.time()
            self._frames_tras_swipe = 0
            self.hist.clear()
            self._smooth.clear()
            return s
        self._frames_tras_swipe += 1
        return self._suavizado(raw)

    def detect(self, frame_bgr):
        """Procesa un frame. Devuelve (frame_anotado, gesto_o_None)."""
        gesto = None
        try:
            if self.backend == "solutions":
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                res = self.hands.process(rgb)
                if res.multi_hand_landmarks:
                    hand_lm = res.multi_hand_landmarks[0]
                    label = "Right"
                    if res.multi_handedness:
                        label = res.multi_handedness[0].classification[0].label
                    lm = hand_lm.landmark
                    gesto = self._procesar(lm, label, frame_bgr)
                    self.mp_draw.draw_landmarks(
                        frame_bgr, hand_lm, self.mp_hands.HAND_CONNECTIONS
                    )
                else:
                    self.hist.clear()
                    self._smooth.append(None)
            else:
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ts = int((time.time() - self._t0) * 1000)
                res = self.landmarker.detect_for_video(mp_img, ts)
                if res.hand_landmarks:
                    lm = res.hand_landmarks[0]
                    label = "Right"
                    try:
                        if res.handedness and res.handedness[0]:
                            label = res.handedness[0][0].category_name or "Right"
                    except Exception:
                        pass
                    gesto = self._procesar(lm, label, frame_bgr)
                    _dibujar_mano_cv2(frame_bgr, lm, self._conex)
                else:
                    self.hist.clear()
                    self._smooth.append(None)
        except Exception as e:
            print(f"[gestos] error detect: {e}")
        return frame_bgr, gesto
