# ✅ Ejercicio 1 — Lectura diferida
# lector.py
import os

FIFO_PATH = "/tmp/test_fifo"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

print("Esperando datos en el FIFO...")
with open(FIFO_PATH, "r") as fifo:
    for line in fifo:
        print(f"[LECTOR] Recibido: {line.strip()}")

# escritor.py
import os
import time

FIFO_PATH = "/tmp/test_fifo"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

time.sleep(2)

with open(FIFO_PATH, "w") as fifo:
    fifo.write("Hola desde el escritor\n")
    fifo.write("Otra línea más\n")
    fifo.flush()

print("[ESCRITOR] Mensajes enviados.")


# ✅ Ejercicio 2 — FIFO como buffer entre procesos
# productor.py
import os
import time

FIFO_PATH = "/tmp/fifo_buffer"
if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

with open(FIFO_PATH, "w") as fifo:
    for i in range(1, 101):
        fifo.write(f"{i}\n")
        fifo.flush()
        time.sleep(0.1)

# consumidor.py
import os
import time
from datetime import datetime

FIFO_PATH = "/tmp/fifo_buffer"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

last_number = 0

with open(FIFO_PATH, "r") as fifo:
    for line in fifo:
        number = int(line.strip())
        print(f"[{datetime.now()}] Recibido: {number}")
        if number != last_number + 1 and last_number != 0:
            print("⚠️ Número perdido entre", last_number, "y", number)
        last_number = number


# ✅ Ejercicio 3 — FIFO + archivos
# escritor.py
import os

FIFO_PATH = "/tmp/fifo_archivo"
if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

print("Escribe líneas (exit para salir):")
with open(FIFO_PATH, "w") as fifo:
    while True:
        line = input("> ")
        fifo.write(line + "\n")
        fifo.flush()
        if line.strip().lower() == "exit":
            break

# lector_guarda.py
import os

FIFO_PATH = "/tmp/fifo_archivo"
OUTPUT_FILE = "output.txt"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

with open(FIFO_PATH, "r") as fifo, open(OUTPUT_FILE, "w") as out:
    for line in fifo:
        if line.strip().lower() == "exit":
            break
        out.write(line)


# ✅ Ejercicio 4 — Múltiples productores
# productor1.py, productor2.py, productor3.py (idénticos excepto ID)
import os
import time

FIFO_PATH = "/tmp/fifo_multi"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

ID = 1  # Cambiar según productor

with open(FIFO_PATH, "w") as fifo:
    for _ in range(10):
        fifo.write(f"Soy productor {ID}\n")
        fifo.flush()
        time.sleep(1)

# lector.py
import os

FIFO_PATH = "/tmp/fifo_multi"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

with open(FIFO_PATH, "r") as fifo:
    for line in fifo:
        print(f"[LECTOR] {line.strip()}")


# ✅ Ejercicio 5 — FIFO con apertura condicional
# lector_nonblock.py
import os
import time
import errno
import fcntl

FIFO_PATH = "/tmp/fifo_nonblock"
if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

retries = 5
for i in range(retries):
    try:
        fd = os.open(FIFO_PATH, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd) as fifo:
            print("[LECTOR] FIFO abierto sin bloqueo")
            for line in fifo:
                print("[LECTOR] Recibido:", line.strip())
        break
    except OSError as e:
        if e.errno == errno.ENXIO:
            print(f"[INTENTO {i+1}] No hay escritor. Reintentando...")
            time.sleep(1)
        else:
            raise
else:
    print("[LECTOR] No se pudo abrir FIFO después de varios intentos.")


# ✅ Ejercicio 6 — Chat asincrónico con doble FIFO
# usuario_a.py / usuario_b.py (ajustar nombres FIFO)
import os
import threading
from datetime import datetime

SEND_FIFO = "/tmp/chat_a"
RECV_FIFO = "/tmp/chat_b"

for path in [SEND_FIFO, RECV_FIFO]:
    if not os.path.exists(path):
        os.mkfifo(path)

def leer():
    with open(RECV_FIFO, "r") as fifo:
        for line in fifo:
            print(f"[{datetime.now()}] Otro: {line.strip()}")

threading.Thread(target=leer, daemon=True).start()

with open(SEND_FIFO, "w") as fifo:
    while True:
        msg = input("Yo > ")
        fifo.write(msg + "\n")
        fifo.flush()
        if msg.strip().lower() == "/exit":
            break


# ✅ Ejercicio 7 — Monitor de temperatura simulado
# simulador.py
import os
import time
import random

FIFO_PATH = "/tmp/temperatura_fifo"
if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

with open(FIFO_PATH, "w") as fifo:
    while True:
        temp = round(random.uniform(20, 30), 2)
        fifo.write(f"{temp}\n")
        fifo.flush()
        time.sleep(1)

# monitor.py
import os
from datetime import datetime

FIFO_PATH = "/tmp/temperatura_fifo"

if not os.path.exists(FIFO_PATH):
    os.mkfifo(FIFO_PATH)

with open(FIFO_PATH, "r") as fifo:
    for line in fifo:
        temp = float(line.strip())
        timestamp = datetime.now()
        print(f"[{timestamp}] Temperatura: {temp}°C")
        if temp > 28:
            print("⚠️ ALERTA: Temperatura alta!")
        with open("log_temp.txt", "a") as log:
            log.write(f"{timestamp}: {temp}°C\n")