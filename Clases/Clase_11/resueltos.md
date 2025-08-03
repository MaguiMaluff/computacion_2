
---

### Ejercicio 1: Creación de Procesos con Argumentos (`gestor.py`)

```python
import argparse
import time
import random
import os
import subprocess
from multiprocessing import Process, current_process

def hijo(verbose):
    pid = os.getpid()
    if verbose:
        print(f"[Hijo {pid}] Durmiendo...")
    time.sleep(random.randint(1,5))
    if verbose:
        print(f"[Hijo {pid}] Termina.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num', type=int, required=True, help="Cantidad de procesos hijos")
    parser.add_argument('--verbose', action='store_true', help="Activar mensajes detallados")
    args = parser.parse_args()

    print(f"[Padre {os.getpid()}] Creando {args.num} procesos hijos")
    procesos = []
    for _ in range(args.num):
        p = Process(target=hijo, args=(args.verbose,))
        p.start()
        procesos.append(p)

    # Mostrar jerarquía de procesos
    print("[Padre] Jerarquía de procesos (pstree):")
    subprocess.run(['pstree', '-p', str(os.getpid())])

    for p in procesos:
        p.join()
    print("[Padre] Todos los hijos finalizaron.")

if __name__ == '__main__':
    main()
```

---

## Ejercicio 2: Proceso Zombi

```python
import os
import time

def main():
    pid = os.fork()
    if pid == 0:
        # Proceso hijo termina inmediatamente
        print(f"[Hijo {os.getpid()}] Finaliza.")
        os._exit(0)
    else:
        print(f"[Padre {os.getpid()}] Hijo {pid} creado, no recolecta estado aún.")
        # No hace wait, duerme 10 segundos para mantener al hijo como zombi
        time.sleep(10)
        # Ahora recolecta el estado
        os.waitpid(pid, 0)
        print("[Padre] Estado del hijo recolectado.")

if __name__ == '__main__':
    main()
```

Desde Bash, durante los 10 segundos, ejecuta:

```bash
ps -ef | grep Z
cat /proc/[pid_hijo]/status | grep State
```

Donde `[pid_hijo]` es el PID del proceso hijo.

---

## Ejercicio 3: Proceso Huérfano

```python
import os
import time

def main():
    pid = os.fork()
    if pid == 0:
        # Hijo: espera 15 segundos
        print(f"[Hijo {os.getpid()}] Ejecutándose, padre: {os.getppid()}")
        time.sleep(15)
        print(f"[Hijo {os.getpid()}] Finalizando, padre actual: {os.getppid()}")
    else:
        # Padre termina inmediatamente
        print(f"[Padre {os.getpid()}] Termina.")
        os._exit(0)

if __name__ == '__main__':
    main()
```

Desde Bash, verificar que `PPID` del hijo cambia a 1 (`init` o `systemd`):

```bash
ps -o pid,ppid,cmd -p [pid_hijo]
```

---

## Ejercicio 4: Reemplazo con `exec()`

```python
import os

def main():
    pid = os.fork()
    if pid == 0:
        print(f"[Hijo {os.getpid()}] Reemplazando imagen con 'ls -l'")
        os.execvp("ls", ["ls", "-l"])
    else:
        os.waitpid(pid, 0)
        print("[Padre] Hijo terminó.")

if __name__ == '__main__':
    main()
```

Verificar con `ps` que el hijo es `ls`.

---

## Ejercicio 5: Pipes anónimos entre padre e hijo

```python
import os

def main():
    r, w = os.pipe()

    pid = os.fork()
    if pid == 0:
        # Proceso hijo escribe mensaje
        os.close(r)  # Cierra lectura
        mensaje = "Hola desde el hijo".encode()
        os.write(w, mensaje)
        os.close(w)
        os._exit(0)
    else:
        # Padre lee mensaje
        os.close(w)  # Cierra escritura
        mensaje = os.read(r, 1024)
        print("[Padre] Mensaje recibido:", mensaje.decode())
        os.close(r)
        os.waitpid(pid, 0)

if __name__ == '__main__':
    main()
```

---

## Ejercicio 6: FIFO (named pipe)

**Crear FIFO (en Bash):**

```bash
mkfifo /tmp/mi_fifo
```

**emisor.py**

```python
import time

def main():
    fifo = '/tmp/mi_fifo'
    with open(fifo, 'w') as f:
        for i in range(10):
            f.write(f"Mensaje {i}\n")
            f.flush()
            time.sleep(1)

if __name__ == '__main__':
    main()
```

**receptor.py**

```python
def main():
    fifo = '/tmp/mi_fifo'
    with open(fifo, 'r') as f:
        for line in f:
            print(f"[Receptor] {line.strip()}")

if __name__ == '__main__':
    main()
```

Ejecutar en dos terminales:

```bash
python3 receptor.py
python3 emisor.py
```

---

## Ejercicio 7: Procesos Concurrentes con Lock

```python
from multiprocessing import Process, Lock
from datetime import datetime
import time
import os

def escribir_log(lock, archivo):
    pid = os.getpid()
    with lock:
        with open(archivo, 'a') as f:
            f.write(f"Proceso {pid} en {datetime.now()}\n")
    time.sleep(0.5)

if __name__ == '__main__':
    lock = Lock()
    archivo = 'log.txt'
    procesos = [Process(target=escribir_log, args=(lock, archivo)) for _ in range(4)]

    for p in procesos:
        p.start()
    for p in procesos:
        p.join()

    print("Escrituras finalizadas.")
```

---

## Ejercicio 8: Condición de Carrera y Corrección

```python
from multiprocessing import Process, Value, Lock
import time

def incremento(compartido, n, lock=None):
    for _ in range(n):
        if lock:
            with lock:
                compartido.value += 1
        else:
            compartido.value += 1

if __name__ == '__main__':
    n = 100_000
    valor = Value('i', 0)
    lock = Lock()

    # Sin Lock (condición de carrera)
    p1 = Process(target=incremento, args=(valor, n, None))
    p2 = Process(target=incremento, args=(valor, n, None))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("Sin Lock:", valor.value)  # Probablemente incorrecto

    # Reiniciar valor
    valor.value = 0

    # Con Lock
    p3 = Process(target=incremento, args=(valor, n, lock))
    p4 = Process(target=incremento, args=(valor, n, lock))
    p3.start()
    p4.start()
    p3.join()
    p4.join()
    print("Con Lock:", valor.value)  # Debe ser 200000
```

---

## Ejercicio 9: Control de concurrencia con Semaphore

```python
from multiprocessing import Process, Semaphore
import time
import os
import random

def acceso_zona(sem, num):
    print(f"[Proceso {num}] intentando acceder...")
    with sem:
        print(f"[Proceso {num}] dentro de la zona crítica.")
        time.sleep(random.uniform(0.5, 2))
        print(f"[Proceso {num}] saliendo de la zona crítica.")

if __name__ == '__main__':
    sem = Semaphore(3)
    procesos = [Process(target=acceso_zona, args=(sem, i)) for i in range(10)]

    for p in procesos:
        p.start()
    for p in procesos:
        p.join()

    print("Todos los procesos terminaron.")
```

---

## Ejercicio 10: Sincronización con RLock

```python
from multiprocessing import Process, RLock
import time
import os

class CuentaBancaria:
    def __init__(self):
        self.saldo = 0
        self.lock = RLock()

    def depositar(self, monto):
        with self.lock:
            print(f"[{os.getpid()}] Depositando {monto}")
            self.saldo += monto
            self._mostrar_saldo()

    def retirar(self, monto):
        with self.lock:
            if self.saldo >= monto:
                print(f"[{os.getpid()}] Retirando {monto}")
                self.saldo -= monto
                self._mostrar_saldo()
            else:
                print(f"[{os.getpid()}] Saldo insuficiente")

    def operar(self, monto_deposito, monto_retiro):
        with self.lock:
            self.depositar(monto_deposito)
            self.retirar(monto_retiro)

    def _mostrar_saldo(self):
        print(f"[{os.getpid()}] Saldo actual: {self.saldo}")

def worker(cuenta):
    for _ in range(3):
        cuenta.operar(100, 50)
        time.sleep(1)

if __name__ == '__main__':
    cuenta = CuentaBancaria()
    procesos = [Process(target=worker, args=(cuenta,)) for _ in range(3)]

    for p in procesos:
        p.start()
    for p in procesos:
        p.join()
```


---

## Ejercicio 11: Manejo de Señales

```python
import signal
import time
import os

def manejador(signum, frame):
    print(f"[PID {os.getpid()}] Señal {signum} recibida.")

if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, manejador)
    print(f"PID: {os.getpid()}, esperando señales SIGUSR1...")
    while True:
        time.sleep(1)
```

Desde Bash, envía señal:

```bash
kill -SIGUSR1 [pid]
```

---

## Ejercicio 12: Ejecución Encadenada con `argparse` y Pipes

**generador.py**

```python
import argparse
import random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, required=True)
    args = parser.parse_args()

    for _ in range(args.n):
        print(random.randint(0, 100))

if __name__ == '__main__':
    main()
```

**filtro.py**

```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min', type=int, required=True)
    args = parser.parse_args()

    for linea in sys.stdin:
        try:
            num = int(linea.strip())
            if num > args.min:
                print(num)
        except ValueError:
            pass

if __name__ == '__main__':
    main()
```

Ejecutar:

```bash
python3 generador.py --n 100 | python3 filtro.py --min 50
```

---

## Ejercicio 13: Visualización de Jerarquía de Procesos

```python
from multiprocessing import Process
import os
import time

def hijo():
    print(f"Hijo PID: {os.getpid()}")
    time.sleep(5)

if __name__ == '__main__':
    p1 = Process(target=hijo)
    p2 = Process(target=hijo)
    p1.start()
    p2.start()

    print(f"Padre PID: {os.getpid()}")
    p1.join()
    p2.join()
```

Desde Bash:

```bash
pstree -p [pid_padre]
ps --forest -p [pid_padre]
```

---

## Ejercicio 14: Ejecución Diferida y Sincronización con `sleep`

**script\_python.py**

```python
import time

print(f"Proceso {os.getpid()} durmiendo 10 segundos")
time.sleep(10)
print("Fin de proceso")
```

**script\_bash.sh**

```bash
#!/bin/bash
python3 script_python.py &
PID=$!
echo "PID proceso: $PID"
sleep 3
ps -p $PID
kill -SIGTERM $PID
```

---

## Ejercicio 15: Análisis de Procesos Activos (Bash)

```bash
#!/bin/bash
declare -A estados
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    if [[ -r /proc/$pid/status ]]; then
        nombre=$(grep '^Name:' /proc/$pid/status | awk '{print $2}')
        ppid=$(grep '^PPid:' /proc/$pid/status | awk '{print $2}')
        estado=$(grep '^State:' /proc/$pid/status | awk '{print $2}')
        echo "PID: $pid | PPID: $ppid | Nombre: $nombre | Estado: $estado"
        ((estados[$estado]++))
    fi
done

echo "Resumen de estados:"
for estado in "${!estados[@]}"; do
    echo "$estado: ${estados[$estado]}"
done
```

---

## Ejercicio 16: Recolección Manual de Estado de Hijos

```python
import os
import time

def hijo(t):
    print(f"Hijo {os.getpid()} durmiendo {t} segundos")
    time.sleep(t)
    print(f"Hijo {os.getpid()} terminando")

if __name__ == '__main__':
    hijos = []
    for t in [3,1,5]:
        pid = os.fork()
        if pid == 0:
            hijo(t)
            os._exit(0)
        else:
            hijos.append(pid)

    orden = []
    while hijos:
        pid, status = os.wait()
        print(f"[Padre] Hijo {pid} terminó con estado {status}")
        orden.append(pid)
        hijos.remove(pid)

    print("Orden de terminación:", orden)
```

---

## Ejercicio 17: Simulación de Lector y Escritor con FIFO (Bash)

**Escritor:**

```bash
#!/bin/bash
FIFO=/tmp/mi_fifo

if [[ ! -p $FIFO ]]; then
    mkfifo $FIFO
fi

for i in {1..10}; do
    echo "Mensaje $i" > $FIFO
    sleep 1
done
```

**Lector:**

```bash
#!/bin/bash
FIFO=/tmp/mi_fifo

if [[ ! -p $FIFO ]]; then
    mkfifo $FIFO
fi

while true; do
    if read line < $FIFO; then
        echo "Leído: $line"
    fi
done
```

---

## Ejercicio 18: Observación de Pipes con `lsof`

```python
import os

def main():
    r, w = os.pipe()
    print(f"Lectura FD: {r}, Escritura FD: {w}")
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os._exit(0)
    else:
        os.close(w)
        input("Ejecuta 'lsof -p {0}' en otro terminal y presiona Enter".format(os.getpid()))
        os.waitpid(pid, 0)

if __name__ == '__main__':
    main()
```

---

## Ejercicio 19: Monitoreo de Escritura Concurrente sin Exclusión

Ejecuta varios procesos con este código (sin lock):

```python
import time
import os

def escribir():
    with open("concurrencia.txt", "a") as f:
        for i in range(10):
            f.write(f"Proceso {os.getpid()} línea {i}\n")
            time.sleep(0.1)

if __name__ == '__main__':
    escribir()
```

Luego con lock:

```python
from multiprocessing import Lock, Process
import time
import os

def escribir(lock):
    with lock:
        with open("concurrencia.txt", "a") as f:
            for i in range(10):
                f.write(f"Proceso {os.getpid()} línea {i}\n")
                time.sleep(0.1)

if __name__ == '__main__':
    lock = Lock()
    procesos = [Process(target=escribir, args=(lock,)) for _ in range(3)]
    for p in procesos:
        p.start()
    for p in procesos:
        p.join()
```

---

## Ejercicio 20: Interacción entre Procesos con Señales Personalizadas

**receptor.py**

```python
import signal
import time
import os

def handler_usr1(signum, frame):
    print(f"[{os.getpid()}] Recibió SIGUSR1")

def handler_usr2(signum, frame):
    print(f"[{os.getpid()}] Recibió SIGUSR2")

if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, handler_usr1)
    signal.signal(signal.SIGUSR2, handler_usr2)
    print(f"PID: {os.getpid()} esperando señales...")
    while True:
        time.sleep(1)
```

**emisor.py**

```python
import os
import signal
import time
import sys

if len(sys.argv) < 2:
    print("Uso: emisor.py [pid_receptor]")
    exit(1)

pid = int(sys.argv[1])

while True:
    os.kill(pid, signal.SIGUSR1)
    time.sleep(2)
    os.kill(pid, signal.SIGUSR2)
    time.sleep(2)
```

