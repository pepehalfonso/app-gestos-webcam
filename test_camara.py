"""Prueba rapida de webcam. Busca en indices 0-4 y muestra video.
Uso: python test_camara.py
Pulsa Q para salir. Te dira que indice poner en la app.
"""
import cv2

def probar(indice, backend):
    cap = cv2.VideoCapture(indice, backend)
    if not cap.isOpened():
        print(f"  [{indice} backend={backend}] no abre")
        cap.release()
        return False
    ok, frame = cap.read()
    if not ok or frame is None:
        print(f"  [{indice} backend={backend}] abre pero no lee frames (camara ocupada o virtual)")
        cap.release()
        return False
    print(f"  [{indice} backend={backend}] OK frame {frame.shape} -> mostrando 3 seg, pulsa Q para pasar")
    import time
    t0 = time.time()
    while time.time() - t0 < 30:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        cv2.putText(frame, f"Camara {indice} OK - Q para siguiente", (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f"Test camara {indice}", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            break
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    print("Buscando camaras 0-4...")
    encontrados = []
    for i in [0, 1, 2, 3, 4]:
        # En Windows DSHOW suele ser mas estable
        for b, nombre in [(cv2.CAP_DSHOW, "DSHOW"), (cv2.CAP_ANY, "ANY")]:
            print(f"Probando indice {i} {nombre}...")
            try:
                cap = cv2.VideoCapture(i, b)
                opened = cap.isOpened()
                ok = False
                if opened:
                    ok, _ = cap.read()
                cap.release()
                print(f"  -> opened={opened} read={ok}")
                if opened and ok:
                    encontrados.append((i, nombre))
                    break
            except Exception as e:
                print(f"  -> error {e}")
    print(f"\nCamaras funcionales: {encontrados}")
    if not encontrados:
        print("No se encontro ninguna. Revisa permisos de Windows: Configuracion > Privacidad > Camara.")
    else:
        for (i, n) in encontrados:
            b = cv2.CAP_DSHOW if n == "DSHOW" else cv2.CAP_ANY
            probar(i, b)
        print(f"\nPon en la app Camara = {encontrados[0][0]} (el primero que viste funcionar).")
