# GestureControl — Controla tu PC con gestos de la mano

App de escritorio en **Python** que usa tu **webcam + IA (MediaPipe)** para reconocer
**15 gestos de manos** y ejecutar **acciones** que tú mismo configuras
(subir volumen, play/pausa, clicks, atajos, abrir apps, etc.).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-green)
![OpenCV](https://img.shields.io/badge/OpenCV-video-red)
![Windows](https://img.shields.io/badge/Windows-10%2F11-lightblue)

## Características

- **15 gestos**: 11 estáticos + 4 dinámicos (swipes)
- **25 acciones**: teclas, multimedia, mouse, sistema y personalizadas
- **Interfaz gráfica**: elige qué hace cada gesto, actívalo/desactívalo, prueba acciones
- **Vista previa integrada** con FPS, gesto actual y registro de eventos
- **Detección robusta**: márgenes anti-temblor, patrones estrictos, suavizado por mayoría,
  swipes con anti-rebote
- **Auto-detección de cámara** (prueba índices 0-4)
- **Configuración en `config.json`** (se guarda sola)

## Requisitos

- Windows 10/11 con webcam
- Python 3.10 o 3.11

## Instalación

```powershell
git clone https://github.com/pepehalfonso/app-gestos-webcam.git
cd app-gestos-webcam
pip install -r requirements.txt
```

> La primera vez que se detecta una mano, la app descarga el modelo
> `hand_landmarker.task` (~8 MB) automáticamente junto al programa.

## Uso

```powershell
python app.py
```

1. Pulsa **Detectar** para hallar tu webcam (o elige el índice a mano).
2. Activa solo los gestos que vas a usar (menos = menos confusión).
3. Elige la acción de cada gesto y pulsa **Probar**.
4. Pulsa **Guardar** y luego **INICIAR**. Mantén cada gesto ~0.7 s a 40-70 cm
   con buena luz frontal.

Para diagnosticar la cámara por separado:

```powershell
python test_camara.py
```

## Gestos disponibles

| Gesto | Descripción |
|---|---|
| `mano_abierta` | 5 dedos extendidos |
| `puno` | Mano totalmente cerrada |
| `uno` | Solo índice arriba |
| `dos_paz` | Índice + medio en V |
| `tres_dedos` | Índice + medio + anular |
| `cuatro_dedos` | 4 dedos, pulgar guardado |
| `pulgar_arriba` | Pulgar vertical arriba |
| `pulgar_abajo` | Pulgar vertical abajo |
| `ok` | Círculo pulgar-índice, resto arriba |
| `rock` | Índice + meñique arriba |
| `pinza` | Pellizco pulgar-índice, resto abajo |
| `swipe_izquierda` | Barrido a tu izquierda |
| `swipe_derecha` | Barrido a tu derecha |
| `swipe_arriba` | Barrido hacia arriba |
| `swipe_abajo` | Barrido hacia abajo |

## Acciones disponibles

Volumen (`volumen_up`, `volumen_down`, `mute`), multimedia
(`play_pause`, `siguiente_pista`, `anterior_pista`), flechas
(`flecha_izq`, `flecha_der`, `flecha_arriba`, `flecha_abajo`),
teclas (`espacio`, `enter`, `escape`), ventanas
(`alt_tab`, `escritorio`, `cerrar_ventana`, `bloquear_pc`),
mouse (`click_izq`, `click_der`, `doble_click`), sistema
(`screenshot`, `abrir_navegador`, `abrir_youtube`, `abrir_explorador`)
y `nada` (sin efecto).

### Acciones personalizadas

En el desplegable o directo en `config.json`:

- `abrir_url:https://www.youtube.com` → abre esa página
- `comando:notepad` → ejecuta ese programa/comando de Windows

## Configuración (`config.json`)

```json
{
  "camara": 1,
  "cooldown_seg": 1.5,
  "frames_estables": 5,
  "sonido": true,
  "mappings": [
    {"gesto": "mano_abierta", "accion": "play_pause", "activo": true},
    {"gesto": "puno", "accion": "mute", "activo": true}
  ]
}
```

- `camara`: índice de webcam (0-4)
- `cooldown_seg`: segundos mínimos entre dos acciones
- `frames_estables`: frames seguidos para confirmar un gesto (más = más preciso, menos = más rápido)
- `sonido`: beep al detectar (Windows)

## Si la cámara no abre

1. Corre `python test_camara.py` para ver qué índice funciona.
2. Windows → Configuración → Privacidad y seguridad → Cámara →
   permite el acceso a las apps de escritorio.
3. Cierra Zoom/Teams/Chrome si están usando la cámara.

## Consejos de detección

- Buena luz frontal, mano a 40-70 cm, fondo liso.
- Mantén el gesto quieto ~0.7 s (la barra de confirmación debe llenarse).
- Desactiva los gestos y swipes que no uses.
- Si un gesto se confunde, sube `frames_estables` a 6-7.

## Estructura del proyecto

```text
app.py               Interfaz + bucle de video
gesture_detector.py  Detección MediaPipe (compatible 0.10.x y 1.x) + clasificador
action_manager.py    Ejecución de acciones (pyautogui / sistema)
config.json          Tu mapeo gesto → acción
test_camara.py       Diagnóstico de webcam
requirements.txt     Dependencias
```

## Compilar a .exe (opcional)

```powershell
pip install pyinstaller
pyinstaller --onedir --windowed --name GestureControl `
  --add-data "config.json;." `
  --add-data "hand_landmarker.task;." `
  --collect-data mediapipe `
  app.py
```

El ejecutable queda en `dist/GestureControl/`. El `config.json` se guarda
junto al `.exe` y el modelo se incluye en el paquete.

## Licencia

MIT — úsalo y compártelo libremente.
