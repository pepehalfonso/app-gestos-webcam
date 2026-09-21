# GestureControl — Controla tu PC con gestos de la mano

App de escritorio en **Python** que usa tu **webcam + IA (MediaPipe)** para reconocer
**gestos de manos** y ejecutar **acciones** que tú mismo configuras
(subir volumen, play/pausa, clicks, abrir links, mover el mouse, etc.).

> ¿Sin Python? Descarga el **.exe para Windows** en
> [**Releases**](https://github.com/pepehalfonso/app-gestos-webcam/releases):

> descarga `Setup_GestureControl_v1.0.0.exe`, ejecútalo y sigue el asistente
> (sin Python ni instalaciones extra).
![Python](https://img.shields.io/badge/Python-3.11-blue)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-green)
![OpenCV](https://img.shields.io/badge/OpenCV-video-red)
![Windows](https://img.shields.io/badge/Windows-10%2F11-lightblue)

## Características

- **15 gestos base**: 11 estáticos + 4 dinámicos (swipes)
- **Gestos personalizados**: entrena tus propias poses en la página Mis gestos
- **Modo mouse aéreo**: el índice mueve el cursor, pinza = click izq, OK = click der
- **Links por gesto**: botón Pegar link, al hacer el gesto se abre en tu navegador
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

### Links por gesto

En la página **Gestos**, cada tarjeta tiene el botón **Pegar link**:
pégalo, pulsa Probar y Guarda. Al hacer ese gesto, el link se abre
en tu navegador predeterminado. También puedes escribir el link directo
en el desplegable (se convierte solo a `abrir_url:...`).

### Modo mouse aéreo

En **En vivo**, activa **Modo mouse aéreo**: tu dedo índice mueve el cursor,
**pinza** = click izquierdo y **OK** = click derecho.
Mientras está activo, esos dos gestos quedan reservados para clicks.

### Mis gestos (entrenables)

En la página **Mis gestos** puedes crear gestos propios:

1. Inicia la detección y pulsa **Nuevo gesto**.
2. Mantén tu pose quieta 3 segundos (se capturan 40 muestras).
3. Ve a **Gestos** y asígnale una acción como a cualquier otro.
4. Ajusta la **sensibilidad** si coincide de más o de menos.

Tus gestos se guardan en `custom_gestos.json` y aparecen con `*` en Gestos.

### Otras acciones personalizadas

- `comando:notepad` → ejecuta ese programa/comando de Windows

## Configuración (`config.json`)

```json
{
  "camara": 1,
  "cooldown_seg": 1.5,
  "frames_estables": 5,
  "sonido": true,
  "mouse_aereo": false,
  "sens_custom": 0.22,
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
- `mouse_aereo`: cursor con el índice, pinza/OK como clicks
- `sens_custom`: umbral de coincidencia de tus gestos (menor = más estricto)

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
gestos_custom.py     Gestos personalizados entrenables (vectores + coincidencia)
atajos.py            Atajos globales de teclado (Windows, sin dependencias)
action_manager.py    Ejecución de acciones (pyautogui / sistema / links)
GestureControl.iss   Script del instalador (Inno Setup)
config.json          Tu mapeo gesto → acción
custom_gestos.json   Tus gestos entrenados (se crea al entrenar)
test_camara.py       Diagnóstico de webcam
requirements.txt     Dependencias
```

## Atajos globales

Funcionan aunque la ventana no esté al frente (se activan al INICIAR):

- `Ctrl+Alt+G`: iniciar / detener la detección
- `Ctrl+Alt+M`: modo mouse aéreo on/off

Se cambian en la página **Ajustes** (formato: modificador + tecla).

## Compilar e instalador (opcional)

```powershell
pip install pyinstaller
pyinstaller --onedir --windowed --name GestureControl `
  --add-data "config.json;." `
  --add-data "hand_landmarker.task;." `
  --collect-data mediapipe `
  --collect-binaries mediapipe `
  app.py
```

El ejecutable queda en `dist/GestureControl/`. OJO: no excluyas
`matplotlib` (MediaPipe lo importa al arrancar).

Para el instalador con asistente (ver `GestureControl.iss`):

```powershell
winget install -e --id JRSoftware.InnoSetup --silent
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GestureControl.iss
```

Sale `dist/Setup_GestureControl_v1.0.0.exe` con icono opcional
y arranque con Windows.

## Licencia

MIT — úsalo y compártelo libremente.
