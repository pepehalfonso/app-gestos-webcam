"""Atajos globales de teclado en Windows, sin dependencias externas.

Usa RegisterHotKey + una ventana solo-de-mensajes en un hilo propio.
Los callbacks se ejecutan en el hilo de atajos: si tocan la UI,
el llamador debe redirigirlos con root.after (Tkinter no es thread-safe).

Ejemplo:
    hk = HotkeyManager()
    hk.register("ctrl+alt+g", lambda: print("toggle"))
    ...
    hk.stop()
"""
import ctypes
import threading
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_HOTKEY = 0x0312
WM_DESTROY = 0x0002
HWND_MESSAGE = -3

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

_MODS = {"alt": MOD_ALT, "ctrl": MOD_CONTROL, "control": MOD_CONTROL,
         "shift": MOD_SHIFT, "mayus": MOD_SHIFT, "win": MOD_WIN,
         "windows": MOD_WIN, "meta": MOD_WIN}

_F_KEYS = {"f%d" % i: 0x6F + i for i in range(1, 13)}
_ESPECIALES = {"espacio": 0x20, "space": 0x20, "tab": 0x09, "enter": 0x0D,
               "escape": 0x1B, "esc": 0x1B, "insert": 0x2D, "supr": 0x2E,
               "delete": 0x2E, "inicio": 0x24, "home": 0x24, "fin": 0x23,
               "end": 0x23, "re_pag": 0x21, "av_pag": 0x22}
_F_KEYS.update(_ESPECIALES)


def mostrar_combo(mod, vk):
    partes = []
    if mod & MOD_CONTROL:
        partes.append("Ctrl")
    if mod & MOD_ALT:
        partes.append("Alt")
    if mod & MOD_SHIFT:
        partes.append("Shift")
    if mod & MOD_WIN:
        partes.append("Win")
    if 0x41 <= vk <= 0x5A:
        partes.append(chr(vk))
    elif 0x30 <= vk <= 0x39:
        partes.append(chr(vk))
    elif 0x70 <= vk <= 0x7B:
        partes.append("F%d" % (vk - 0x6F))
    else:
        for nombre, codigo in _F_KEYS.items():
            if codigo == vk:
                partes.append(nombre.capitalize())
                break
        else:
            partes.append("VK%02X" % vk)
    return "+".join(partes)


def parse_combo(texto):
    """'ctrl+alt+g' -> (mod, vk). Lanza ValueError si no es valido."""
    if not texto or not texto.strip():
        raise ValueError("atajo vacio")
    partes = [p.strip().lower() for p in texto.replace(" ", "").split("+") if p.strip()]
    if len(partes) < 2:
        raise ValueError("usa al menos modificador + tecla (ej: ctrl+alt+g)")
    *mods, tecla = partes
    mod = 0
    for m in mods:
        if m not in _MODS:
            raise ValueError("modificador desconocido: %s (usa ctrl/alt/shift/win)" % m)
        mod |= _MODS[m]
    if mod == 0:
        raise ValueError("falta modificador (ctrl/alt/shift/win)")
    if len(tecla) == 1 and (tecla.isalnum()):
        vk = ord(tecla.upper())
    elif tecla in _F_KEYS:
        vk = _F_KEYS[tecla]
    else:
        raise ValueError("tecla no soportada: %s (usa a-z, 0-9 o f1-f12)" % tecla)
    return mod, vk


_WNDPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
                              wintypes.WPARAM, wintypes.LPARAM)


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", _POINT)]


class _WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", _WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE), ("hIcon", ctypes.c_void_p),
                ("hCursor", ctypes.c_void_p), ("hbrBackground", ctypes.c_void_p),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR)]


def _prototipos():
    u = user32
    u.RegisterClassW.argtypes = [ctypes.POINTER(_WNDCLASSW)]
    u.RegisterClassW.restype = ctypes.c_ushort
    u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                  wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    u.CreateWindowExW.restype = ctypes.c_void_p
    u.RegisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                 ctypes.c_uint, ctypes.c_uint]
    u.RegisterHotKey.restype = ctypes.c_int
    u.UnregisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int]
    u.UnregisterHotKey.restype = ctypes.c_int
    u.DefWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                 ctypes.c_void_p, ctypes.c_void_p]
    u.DefWindowProcW.restype = ctypes.c_void_p
    u.GetMessageW.argtypes = [ctypes.POINTER(_MSG), ctypes.c_void_p,
                              ctypes.c_uint, ctypes.c_uint]
    u.GetMessageW.restype = ctypes.c_int
    u.TranslateMessage.argtypes = [ctypes.POINTER(_MSG)]
    u.TranslateMessage.restype = ctypes.c_int
    u.DispatchMessageW.argtypes = [ctypes.POINTER(_MSG)]
    u.DispatchMessageW.restype = ctypes.c_void_p
    u.DestroyWindow.argtypes = [ctypes.c_void_p]
    u.DestroyWindow.restype = ctypes.c_int
    u.UnregisterClassW.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p]
    u.UnregisterClassW.restype = ctypes.c_int
    u.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                               ctypes.c_void_p, ctypes.c_void_p]
    u.PostMessageW.restype = ctypes.c_int
    u.PostQuitMessage.argtypes = [ctypes.c_int]
    u.PostQuitMessage.restype = None
    u.PostThreadMessageW.argtypes = [wintypes.DWORD, ctypes.c_uint,
                                     ctypes.c_void_p, ctypes.c_void_p]
    u.PostThreadMessageW.restype = ctypes.c_int
    u.PeekMessageW.argtypes = [ctypes.POINTER(_MSG), ctypes.c_void_p,
                               ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
    u.PeekMessageW.restype = ctypes.c_int
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD


_prototipos()


class HotkeyManager:
    def __init__(self):
        import queue
        self._cbs = {}
        self._ops = queue.Queue()
        self._next_id = 1
        self._hilo = None
        self._tid = None
        self._corriendo = False
        self._lock = threading.Lock()
        self._listo = threading.Event()

    def _bucle(self):
        import queue as _queue
        user32.PeekMessageW(ctypes.byref(_MSG()), None, 0, 0, 0)  # crea la cola
        self._tid = kernel32.GetCurrentThreadId()
        self._corriendo = True
        self._listo.set()
        msg = _MSG()
        while self._corriendo:
            # 1) operaciones pendientes (registrar/limpiar)
            try:
                while True:
                    op = self._ops.get_nowait()
                    self._ejecutar_op(op)
            except _queue.Empty:
                pass
            if not self._corriendo:
                break
            # 2) mensajes (WM_HOTKEY llega aqui al usar hWnd NULL)
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0:  # WM_QUIT
                break
            if ret < 0:
                continue
            if msg.message == WM_HOTKEY:
                with self._lock:
                    cb = self._cbs.get(int(msg.wParam))
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass
            # lo demas se ignora (no hay ventanas propias)
        # al salir: desregistra todo
        with self._lock:
            for hid in list(self._cbs):
                try:
                    user32.UnregisterHotKey(None, hid)
                except Exception:
                    pass
            self._cbs.clear()

    def _ejecutar_op(self, op):
        kind = op[0]
        if kind == "reg":
            _, hid, mod, vk, listo, caja = op
            ok = bool(user32.RegisterHotKey(None, hid, mod, vk))
            err = kernel32.GetLastError() if not ok else 0
            caja.append((ok, err))
            listo.set()
        elif kind == "unreg":
            _, hid = op
            try:
                user32.UnregisterHotKey(None, hid)
            except Exception:
                pass
            with self._lock:
                self._cbs.pop(hid, None)
        elif kind == "stop":
            self._corriendo = False
            user32.PostQuitMessage(0)

    def _despertar(self):
        try:
            if self._tid:
                user32.PostThreadMessageW(self._tid, 0, None, None)
        except Exception:
            pass

    def start(self):
        if self._hilo and self._hilo.is_alive():
            return
        self._listo.clear()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()
        self._listo.wait(timeout=3)

    def register(self, combo, callback):
        """Registra 'ctrl+alt+g'. Devuelve el id o lanza RuntimeError/ValueError."""
        mod, vk = parse_combo(combo)
        self.start()
        if not self._hilo or not self._hilo.is_alive():
            raise RuntimeError("no se pudo iniciar el hilo de atajos")
        with self._lock:
            hid = self._next_id
            self._next_id += 1
            self._cbs[hid] = callback
        listo = threading.Event()
        caja = []
        self._ops.put(("reg", hid, mod, vk, listo, caja))
        self._despertar()
        if not listo.wait(timeout=5):
            with self._lock:
                self._cbs.pop(hid, None)
            raise RuntimeError("el hilo de atajos no respondio")
        ok, err = caja[0]
        if not ok:
            with self._lock:
                self._cbs.pop(hid, None)
            raise RuntimeError("Windows rechazo el atajo %r (codigo %d): "
                               "quiza lo usa otro programa" % (combo, err))
        return hid

    def unregister(self, hid):
        self._ops.put(("unreg", hid))
        self._despertar()

    def stop(self):
        self._ops.put(("stop",))
        self._despertar()
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=3)
        self._hilo = None
        self._tid = None
