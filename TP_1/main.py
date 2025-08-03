import multiprocessing as mp
import time
import random
from datetime import datetime
from analizador import proceso_analizador
from verificador import proceso_verificador

def generar_muestra(i):
    muestra = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "frecuencia": random.randint(60, 180),
        "presion": [random.randint(110, 180), random.randint(70, 110)],
        "oxigeno": random.randint(90, 100)
    }
    # Fuerza un valor fuera de rango cada 15 muestras
    if i == 15:
        muestra["frecuencia"] = 220  # fuera de rango
    if i == 30:
        muestra["oxigeno"] = 85      # fuera de rango
    if i == 45:
        muestra["presion"][0] = 210  # fuera de rango
    return muestra

if __name__ == "__main__":
    parent_a, child_a = mp.Pipe()
    parent_b, child_b = mp.Pipe()
    parent_c, child_c = mp.Pipe()

    queue_a = mp.Queue()
    queue_b = mp.Queue()
    queue_c = mp.Queue()

    verificador_proc = mp.Process(
        target=proceso_verificador,
        args=(queue_a, queue_b, queue_c)
    )

    analizador_a = mp.Process(target=proceso_analizador, args=('frecuencia', child_a, queue_a))
    analizador_b = mp.Process(target=proceso_analizador, args=('presion', child_b, queue_b))
    analizador_c = mp.Process(target=proceso_analizador, args=('oxigeno', child_c, queue_c))

    verificador_proc.start()
    analizador_a.start()
    analizador_b.start()
    analizador_c.start()

    for i in range(60):
        muestra = generar_muestra(i)
        parent_a.send(muestra)
        parent_b.send(muestra)
        parent_c.send(muestra)
        time.sleep(1)

    parent_a.send('FIN')
    parent_b.send('FIN')
    parent_c.send('FIN')
    analizador_a.join()
    analizador_b.join()
    analizador_c.join()
    verificador_proc.join()
    print("Fin")