# -----------------------------
# Ejercicio 1: Manejo básico con SIGTERM
# -----------------------------

import signal
import os
import time
import atexit


def despedida():
    print("\n[atexit] Terminando el proceso de forma ordenada...")


def manejador_sigterm(signum, frame):
    print(f"[signal] Señal SIGTERM recibida. Código: {signum}")
    exit(0)


atexit.register(despedida)
signal.signal(signal.SIGTERM, manejador_sigterm)

print("Proceso ejecutándose. PID:", os.getpid())

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrumpido manualmente.")

# -----------------------------
# Ejercicio 2: Diferenciar señales según su origen
# -----------------------------

import os
import signal
import time
import multiprocessing
import random


def handler(signum, frame):
    print(f"[Padre] Señal recibida: {signum} desde PID {frame.f_globals.get('__name__', '?')}")


def hijo(signal_to_send):
    time.sleep(random.uniform(0.5, 2))
    os.kill(os.getppid(), signal_to_send)


if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGTERM, handler)

    señales = [signal.SIGUSR1, signal.SIGUSR2, signal.SIGTERM]
    procesos = [multiprocessing.Process(target=hijo, args=(s,)) for s in señales]

    for p in procesos:
        p.start()

    for _ in range(3):
        signal.pause()  # espera hasta que una señal sea recibida

# -----------------------------
# Ejercicio 3: Ignorar señales temporalmente
# -----------------------------

import signal
import time


def ignorar_sigint(signum, frame):
    print("SIGINT ignorada.")


print("Ignorando SIGINT por 5 segundos. Intenta presionar Ctrl+C...")
signal.signal(signal.SIGINT, ignorar_sigint)
time.sleep(5)

print("Restaurando comportamiento por defecto de SIGINT.")
signal.signal(signal.SIGINT, signal.default_int_handler)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("SIGINT capturada. Finalizando.")

# -----------------------------
# Ejercicio 4: Control multihilo con señales externas
# -----------------------------

import signal
import threading
import time

estado = {"pausado": False}
lock = threading.Lock()


def manejador_usr1(signum, frame):
    with lock:
        estado["pausado"] = True
        print("[Señal] Pausando cuenta")


def manejador_usr2(signum, frame):
    with lock:
        estado["pausado"] = False
        print("[Señal] Reanudando cuenta")


def cuenta():
    for i in range(30, 0, -1):
        with lock:
            if estado["pausado"]:
                print("[Cuenta] Pausado")
                while estado["pausado"]:
                    time.sleep(0.5)
        print(f"[Cuenta] {i}")
        time.sleep(1)


if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, manejador_usr1)
    signal.signal(signal.SIGUSR2, manejador_usr2)

    t = threading.Thread(target=cuenta)
    t.start()
    t.join()

# -----------------------------
# Ejercicio 5: Simulación de cola de trabajos con señales
# -----------------------------

import signal
import os
import time
import multiprocessing
import queue

trabajos = multiprocessing.Queue()


def productor(pid_consumidor):
    for i in range(5):
        mensaje = f"Trabajo {i} @ {time.time()}"
        print(f"[Productor] Generando: {mensaje}")
        trabajos.put(mensaje)
        os.kill(pid_consumidor, signal.SIGUSR1)
        time.sleep(0.5)


def manejador_trabajo(signum, frame):
    try:
        while not trabajos.empty():
            trabajo = trabajos.get_nowait()
            print(f"[Consumidor] Procesando: {trabajo}")
            time.sleep(1)
    except queue.Empty:
        pass


if __name__ == '__main__':
    pid = os.getpid()
    signal.signal(signal.SIGUSR1, manejador_trabajo)

    p = multiprocessing.Process(target=productor, args=(pid,))
    p.start()

    print("[Consumidor] Esperando trabajos...")
    while p.is_alive() or not trabajos.empty():
        signal.pause()
    print("[Consumidor] Fin.")
