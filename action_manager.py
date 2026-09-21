"""Ejecuta acciones del sistema a partir de un ID de accion.
Todas las acciones estan en ACCIONES para que la UI las liste.
Soporta tambien acciones personalizadas:
  "abrir_url:https://..." -> abre navegador
  "comando:notepad"       -> ejecuta programa/comando Windows
"""
import subprocess
import webbrowser
from urllib.parse import urlparse

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    _PYAUTO = True
except Exception:
    _PYAUTO = False


def _press(*keys):
    if not _PYAUTO:
        print(f"[accion] pyautogui no disponible, teclas: {keys}")
        return
    # teclas multimedia o normales
    if len(keys) == 1:
        pyautogui.press(keys[0])
    else:
        pyautogui.hotkey(*keys)


def _click(boton="left", doble=False):
    if not _PYAUTO:
        print(f"[accion] click {boton}")
        return
    if doble:
        pyautogui.doubleClick(button=boton)
    else:
        pyautogui.click(button=boton)


def tamano_pantalla():
    """Devuelve (ancho, alto) o None si pyautogui no esta disponible."""
    if not _PYAUTO:
        return None
    try:
        s = pyautogui.size()
        return (s.width, s.height)
    except Exception:
        return None


def mover_cursor(x, y):
    """Mueve el cursor a coordenadas de pantalla. Devuelve True si pudo."""
    if not _PYAUTO:
        return False
    try:
        pyautogui.moveTo(int(x), int(y), duration=0)
        return True
    except Exception:
        return False


ACCIONES = {
    "nada": "No hacer nada",
    "volumen_up": "Subir volumen",
    "volumen_down": "Bajar volumen",
    "mute": "Silenciar / activar sonido",
    "play_pause": "Play / Pausa multimedia",
    "siguiente_pista": "Pista siguiente",
    "anterior_pista": "Pista anterior",
    "flecha_izq": "Flecha izquierda",
    "flecha_der": "Flecha derecha",
    "flecha_arriba": "Flecha arriba",
    "flecha_abajo": "Flecha abajo",
    "espacio": "Espacio",
    "enter": "Enter",
    "escape": "Escape (Esc)",
    "alt_tab": "Alt + Tab (cambiar ventana)",
    "escritorio": "Win + D (mostrar escritorio)",
    "cerrar_ventana": "Alt + F4 (cerrar ventana)",
    "screenshot": "Captura de pantalla",
    "click_izq": "Click izquierdo",
    "click_der": "Click derecho",
    "doble_click": "Doble click",
    "abrir_navegador": "Abrir navegador",
    "abrir_youtube": "Abrir YouTube",
    "abrir_explorador": "Abrir explorador de archivos",
    "bloquear_pc": "Bloquear PC (Win+L)",
}


def lista_acciones():
    return sorted(ACCIONES.keys())


def normalizar_url(texto):
    """Limpia y valida un link. Devuelve la URL con esquema o None si no es valida."""
    if not texto:
        return None
    t = texto.strip().strip("<>")
    if t.lower().startswith("abrir_url:"):
        t = t.split(":", 1)[1].strip()
    if " " in t or not t:
        return None
    if "://" not in t:
        t = "https://" + t
    try:
        p = urlparse(t)
    except Exception:
        return None
    if p.scheme not in ("http", "https"):
        return None
    if "." not in (p.netloc or ""):
        return None
    return t


def es_link(accion_id):
    return isinstance(accion_id, str) and accion_id.startswith("abrir_url:")


def accion_a_link(accion_id):
    """Si la accion es un link, devuelve la URL. Si no, None."""
    if es_link(accion_id):
        return accion_id.split(":", 1)[1]
    return None


def normalizar_accion(valor):
    """Convierte lo que escribe el usuario en un ID de accion valido.

    - Si es una accion conocida, la devuelve tal cual.
    - Si parece un link (http://, https://, www. o dominio), lo convierte a abrir_url:...
    - Si no, lo devuelve recortado (sera tratado como desconocido al ejecutar).
    """
    if valor is None:
        return "nada"
    v = valor.strip()
    if not v:
        return "nada"
    if v in ACCIONES or v.startswith(("abrir_url:", "comando:")):
        return v
    url = normalizar_url(v)
    if url:
        return "abrir_url:" + url
    return v


def nombre_amigable(accion_id):
    """Texto corto para mostrar en la interfaz (links muestran el dominio)."""
    if accion_id in ACCIONES:
        return ACCIONES[accion_id]
    if es_link(accion_id):
        url = accion_a_link(accion_id)
        try:
            host = urlparse(url).netloc or url
            return "Abrir link: " + host
        except Exception:
            return "Abrir link"
    if isinstance(accion_id, str) and accion_id.startswith("comando:"):
        return "Ejecutar: " + accion_id.split(":", 1)[1]
    return accion_id


def descripcion(accion_id):
    return nombre_amigable(accion_id)


def ejecutar(accion_id):
    """Ejecuta la accion. Devuelve True si se ejecuto algo."""
    try:
        if accion_id in (None, "", "nada"):
            return False

        # acciones personalizadas
        if accion_id.startswith("abrir_url:"):
            url = normalizar_url(accion_id)
            if not url:
                print(f"[accion] link invalido: {accion_id}")
                return False
            webbrowser.open(url, new=2)
            print(f"[accion] link abierto: {url}")
            return True
        if accion_id.startswith("comando:"):
            cmd = accion_id.split(":", 1)[1]
            subprocess.Popen(cmd, shell=True)
            return True

        if accion_id == "volumen_up":
            _press("volumeup")
        elif accion_id == "volumen_down":
            _press("volumedown")
        elif accion_id == "mute":
            _press("volumemute")
        elif accion_id == "play_pause":
            _press("playpause")
        elif accion_id == "siguiente_pista":
            _press("nexttrack")
        elif accion_id == "anterior_pista":
            _press("prevtrack")
        elif accion_id == "flecha_izq":
            _press("left")
        elif accion_id == "flecha_der":
            _press("right")
        elif accion_id == "flecha_arriba":
            _press("up")
        elif accion_id == "flecha_abajo":
            _press("down")
        elif accion_id == "espacio":
            _press("space")
        elif accion_id == "enter":
            _press("enter")
        elif accion_id == "escape":
            _press("esc")
        elif accion_id == "alt_tab":
            _press("alt", "tab")
        elif accion_id == "escritorio":
            _press("win", "d")
        elif accion_id == "cerrar_ventana":
            _press("alt", "f4")
        elif accion_id == "bloquear_pc":
            _press("win", "l")
        elif accion_id == "screenshot":
            if _PYAUTO:
                import os, datetime
                carpeta = os.path.join(os.path.expanduser("~"), "Pictures", "GestureControl")
                os.makedirs(carpeta, exist_ok=True)
                nombre = datetime.datetime.now().strftime("cap_%Y%m%d_%H%M%S.png")
                pyautogui.screenshot(os.path.join(carpeta, nombre))
        elif accion_id == "click_izq":
            _click("left")
        elif accion_id == "click_der":
            _click("right")
        elif accion_id == "doble_click":
            _click("left", doble=True)
        elif accion_id == "abrir_navegador":
            webbrowser.open("https://www.google.com")
        elif accion_id == "abrir_youtube":
            webbrowser.open("https://www.youtube.com")
        elif accion_id == "abrir_explorador":
            subprocess.Popen("explorer", shell=True)
        else:
            print(f"[accion] desconocida: {accion_id}")
            return False
        print(f"[accion] ejecutada: {accion_id}")
        return True
    except Exception as e:
        print(f"[accion] error ejecutando {accion_id}: {e}")
        return False
