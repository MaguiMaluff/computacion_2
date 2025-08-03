

### Ejercicio 6 · Cronómetro compartido con detección de incoherencias

```python
from multiprocessing import Process, Value, Lock
import time

def actualizador(tiempo_compartido, lock, id_proc):
    while True:
        with lock:
            tiempo_compartido.value = time.time()
        print(f"Proceso {id_proc} actualizó el tiempo.")
        time.sleep(1)

def lector(tiempo_compartido, lock):
    ultimo = 0.0
    while True:
        time.sleep(0.5)
        with lock:
            actual = tiempo_compartido.value
        if ultimo != 0 and abs(actual - ultimo) > 1:
            print(f"¡Incoherencia detectada! Salto de {actual - ultimo:.2f}s")
        else:
            print(f"Lector: tiempo correcto {actual:.2f}")
        ultimo = actual

if __name__ == '__main__':
    tiempo = Value('d', 0.0)
    lock = Lock()

    p1 = Process(target=actualizador, args=(tiempo, lock, 1))
    p2 = Process(target=actualizador, args=(tiempo, lock, 2))
    p3 = Process(target=actualizador, args=(tiempo, lock, 3))
    lector_p = Process(target=lector, args=(tiempo, lock))

    p1.start(); p2.start(); p3.start()
    lector_p.start()

    try:
        p1.join(); p2.join(); p3.join()
        lector_p.join()
    except KeyboardInterrupt:
        print("Terminando...")
```

---

### Ejercicio 7 · Load balancer simple con Queue

```python
from multiprocessing import Process, Queue, current_process
import time
import random

def worker(q, resultados):
    while True:
        url = q.get()
        if url is None:
            break
        inicio = time.time()
        # Simulación descarga con sleep
        time.sleep(random.uniform(0.5, 1.5))
        fin = time.time()
        duracion = fin - inicio
        resultados.put((current_process().pid, url, duracion))

def maestro(urls, k):
    q = Queue()
    resultados = Queue()
    workers = [Process(target=worker, args=(q, resultados)) for _ in range(k)]

    for w in workers:
        w.start()

    for url in urls:
        q.put(url)

    # Señales de finalización
    for _ in workers:
        q.put(None)

    for w in workers:
        w.join()

    # Recoger resultados
    lista_resultados = []
    while not resultados.empty():
        lista_resultados.append(resultados.get())

    # Ordenar por duración y mostrar
    lista_resultados.sort(key=lambda x: x[2])
    for pid, url, dur in lista_resultados:
        print(f"PID {pid} descargó {url} en {dur:.2f} segundos")

if __name__ == '__main__':
    urls = [f"http://example.com/file{i}" for i in range(10)]
    maestro(urls, 3)
```

---

### Ejercicio 8 · Cálculo de números primos con sincronización a archivo

```python
from multiprocessing import Process, Lock
import math

def es_primo(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) +1):
        if n % i == 0:
            return False
    return True

def primos_en_rango(inicio, fin, lock):
    with open('primos.txt', 'a') as f:
        for num in range(inicio, fin):
            if es_primo(num):
                with lock:
                    f.write(f"{num}\n")

if __name__ == '__main__':
    lock = Lock()
    rango_total = 10_000
    n_procesos = 8
    rango_por_proceso = rango_total // n_procesos

    procesos = []
    for i in range(n_procesos):
        inicio = i * rango_por_proceso
        fin = inicio + rango_por_proceso
        p = Process(target=primos_en_rango, args=(inicio, fin, lock))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    print("Cálculo de primos terminado.")
```

---

### Ejercicio 9 · Simulación banco con back-off exponencial

```python
from multiprocessing import Process, Value, Lock
import time
import random

def cajero(balance, lock, id_cajero, iteraciones=100):
    backoff = 0.01
    for _ in range(iteraciones):
        while True:
            locked = lock.acquire(False)
            if locked:
                # Operación crítica
                operacion = random.choice(['deposito', 'retiro'])
                monto = random.randint(1, 100)
                if operacion == 'retiro' and balance.value < monto:
                    print(f"Cajero {id_cajero}: Fondos insuficientes para retirar {monto}.")
                else:
                    if operacion == 'deposito':
                        balance.value += monto
                        print(f"Cajero {id_cajero}: Depositó {monto}. Nuevo balance: {balance.value}")
                    else:
                        balance.value -= monto
                        print(f"Cajero {id_cajero}: Retiró {monto}. Nuevo balance: {balance.value}")
                lock.release()
                backoff = 0.01  # reset backoff
                break
            else:
                # Back-off exponencial
                time.sleep(backoff)
                backoff = min(backoff * 2, 1.0)

if __name__ == '__main__':
    balance = Value('i', 1000)
    lock = Lock()
    procesos = [Process(target=cajero, args=(balance, lock, i)) for i in range(4)]

    for p in procesos:
        p.start()

    for p in procesos:
        p.join()

    print(f"Balance final: {balance.value}")
```

---

### Ejercicio 10 · Benchmark IPC: Pipe vs Queue vs Manager().list

```python
from multiprocessing import Process, Pipe, Queue, Manager
import time

N = 1_000_000

def enviar_pipe(conn):
    for i in range(N):
        conn.send(i)
    conn.close()

def recibir_pipe(conn):
    while True:
        try:
            _ = conn.recv()
        except EOFError:
            break

def enviar_queue(q):
    for i in range(N):
        q.put(i)

def recibir_queue(q):
    for _ in range(N):
        _ = q.get()

def enviar_manager_list(lst):
    for i in range(N):
        lst.append(i)

def benchmark_pipe():
    p_conn, c_conn = Pipe()
    p1 = Process(target=enviar_pipe, args=(p_conn,))
    p2 = Process(target=recibir_pipe, args=(c_conn,))

    start = time.perf_counter()
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    end = time.perf_counter()
    return end - start

def benchmark_queue():
    q = Queue()
    p1 = Process(target=enviar_queue, args=(q,))
    p2 = Process(target=recibir_queue, args=(q,))

    start = time.perf_counter()
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    end = time.perf_counter()
    return end - start

def benchmark_manager_list():
    mgr = Manager()
    lst = mgr.list()
    p = Process(target=enviar_manager_list, args=(lst,))

    start = time.perf_counter()
    p.start()
    p.join()
    end = time.perf_counter()
    return end - start

if __name__ == '__main__':
    print("Benchmark Pipe:", benchmark_pipe(), "segundos")
    print("Benchmark Queue:", benchmark_queue(), "segundos")
    print("Benchmark Manager List:", benchmark_manager_list(), "segundos")
```

---
