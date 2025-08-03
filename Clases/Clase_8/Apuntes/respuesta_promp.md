

# Guía Completa de Multiprocessing en Python para Estudiantes de Ingeniería

---

## a) Fundamentos de procesos y programación concurrente

* **Proceso:** instancia de programa en ejecución con memoria independiente.
* **Hilo:** unidad de ejecución dentro de un proceso que comparte memoria.
* Multiprocessing permite paralelismo real en Python, evitando el GIL.
* Ciclo de vida: creación → inicio (start) → ejecución → terminación → join.

**Ejemplo básico:**

```python
from multiprocessing import Process
import os

def worker():
    print(f"Hijo PID: {os.getpid()}")

if __name__ == "__main__":
    print(f"Padre PID: {os.getpid()}")
    p = Process(target=worker)
    p.start()
    p.join()
```

---

## b) Creación y gestión de procesos con `multiprocessing`

* Crear proceso con `Process(target=funcion)`.
* Métodos importantes:

  * `start()`: inicia proceso.
  * `join()`: espera que proceso termine.
  * `is_alive()`: chequea si sigue vivo.
* Acceder a PID con `p.pid`.
* Ejemplo:

```python
from multiprocessing import Process
import time

def tarea():
    print("Inicio tarea")
    time.sleep(2)
    print("Fin tarea")

if __name__ == "__main__":
    p = Process(target=tarea)
    p.start()
    print(f"Proceso iniciado con PID {p.pid}")
    p.join()
    print("Proceso finalizado")
```

---

## c) Comunicación entre procesos

* Procesos tienen memoria separada → necesitan mecanismos IPC.
* **Pipes:** canal de comunicación dúplex (bidireccional) entre 2 procesos.
* **Queues:** cola segura para múltiples productores y consumidores.

**Pipe ejemplo:**

```python
from multiprocessing import Process, Pipe

def hijo(conn):
    msg = conn.recv()
    print(f"Hijo recibió: {msg}")
    conn.send("Mensaje desde hijo")
    conn.close()

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()
    p = Process(target=hijo, args=(child_conn,))
    p.start()
    parent_conn.send("Hola desde padre")
    print(parent_conn.recv())
    p.join()
```

**Queue ejemplo:**

```python
from multiprocessing import Process, Queue

def productor(q):
    for i in range(5):
        q.put(i)
        print(f"Producto {i} enviado")

def consumidor(q):
    while not q.empty():
        item = q.get()
        print(f"Consumido {item}")

if __name__ == "__main__":
    q = Queue()
    p1 = Process(target=productor, args=(q,))
    p2 = Process(target=consumidor, args=(q,))
    p1.start()
    p1.join()
    p2.start()
    p2.join()
```

---

## d) Sincronización básica con Lock

* **Condición de carrera:** cuando procesos acceden/modifican datos simultáneamente y causan errores.
* `Lock()` evita que dos procesos entren a una sección crítica al mismo tiempo.

**Ejemplo Lock:**

```python
from multiprocessing import Process, Lock

def tarea(lock, i):
    lock.acquire()
    print(f"Proceso {i} entrando a sección crítica")
    lock.release()

if __name__ == "__main__":
    lock = Lock()
    procesos = [Process(target=tarea, args=(lock, i)) for i in range(3)]
    for p in procesos:
        p.start()
    for p in procesos:
        p.join()
```

---

## e) Pool de procesos

* Administra un grupo de procesos para tareas paralelas.
* Métodos importantes:

  * `map(func, iterable)`: aplica función a elementos.
  * `apply(func, args)`: ejecuta función una vez.
  * Versiones asíncronas (`map_async`, `apply_async`).

**Ejemplo Pool:**

```python
from multiprocessing import Pool
import time

def cuadrado(x):
    return x * x

if __name__ == "__main__":
    with Pool(4) as pool:
        resultados = pool.map(cuadrado, [1, 2, 3, 4])
        print(resultados)
```

---

## f) Memoria compartida básica

* `Value` y `Array` permiten compartir datos simples entre procesos.
* `Value` es para un solo valor, `Array` para colecciones.

**Ejemplo Value:**

```python
from multiprocessing import Process, Value

def tarea(n):
    n.value += 1

if __name__ == "__main__":
    num = Value('i', 0)
    procesos = [Process(target=tarea, args=(num,)) for _ in range(5)]
    for p in procesos:
        p.start()
    for p in procesos:
        p.join()
    print(f"Valor final: {num.value}")
```

---

# Consideraciones finales

* Multiprocessing logra paralelismo real, a diferencia de threads en Python.
* Siempre sincroniza acceso a datos compartidos.
* Usa `join()` para esperar procesos.
* Analiza el código y entiende cada paso antes de avanzar.
* En tu práctica, modifica el archivo `mp_worker.py` para demostrar que varios procesos corren simultáneamente.

---
