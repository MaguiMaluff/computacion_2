### Ejercicio 1: Identificación de procesos padre e hijo
Crea un programa que genere un proceso hijo utilizando `fork()` y que ambos (padre e hijo) impriman sus respectivos PID y PPID. El objetivo es observar la relación jerárquica entre ellos.

```python
import os

def main():
    # Crear un proceso hijo
    pid = os.fork()
    
    # Proceso hijo (pid == 0)
    if pid == 0:
        print("PROCESO HIJO:")
        print(f"PID: {os.getpid()}")      # ID del proceso actual
        print(f"PPID: {os.getppid()}")    # ID del proceso padre

    # Proceso padre (pid > 0)
    else:
        print("PROCESO PADRE:")
        print(f"PID: {os.getpid()}")      # ID del proceso actual
        print(f"PID del hijo: {pid}")     # ID del proceso hijo
        print(f"PPID: {os.getppid()}")    # ID del proceso padre (shell)

```
---

### Ejercicio 2: Doble bifurcación
Escribe un programa donde un proceso padre cree dos hijos diferentes (no en cascada), y cada hijo imprima su identificador. El padre deberá esperar a que ambos terminen.

```python
import os

for i in range(2):
    pid = os.fork()
    if pid == 0:
        print(f"[HIJO {i}] PID: {os.getpid()}  Padre: {os.getppid()}")
        os._exit(0)

for _ in range(2):
    os.wait()
```

---

### Ejercicio 3: Reemplazo de un proceso hijo con `exec()`
Haz que un proceso hijo reemplace su contexto de ejecución con un programa del sistema, por ejemplo, el comando `ls -l`, utilizando `exec()`.

---

### Ejercicio 4: Secuencia controlada de procesos
Diseña un programa donde se creen dos hijos de manera secuencial: se lanza el primero, se espera a que finalice, y luego se lanza el segundo. Cada hijo debe realizar una tarea mínima.

---

### Ejercicio 5: Proceso zombi temporal
Crea un programa que genere un proceso hijo que termine inmediatamente, pero el padre no debe recoger su estado de salida durante algunos segundos. Observa su estado como zombi con herramientas del sistema.

---

### Ejercicio 6: Proceso huérfano adoptado por `init`
Genera un proceso hijo que siga ejecutándose luego de que el padre haya terminado. Verifica que su nuevo PPID corresponda al proceso `init` o `systemd`.

---

### Ejercicio 7: Multiproceso paralelo
Construye un programa que cree tres hijos en paralelo (no secuenciales). Cada hijo ejecutará una tarea breve y luego finalizará. El padre debe esperar por todos ellos.

---

### Ejercicio 8: Simulación de servidor multiproceso
Imita el comportamiento de un servidor concurrente que atiende múltiples clientes creando un proceso hijo por cada uno. Cada proceso debe simular la atención a un cliente con un `sleep()`.

---

### Ejercicio 9: Detección de procesos zombis en el sistema
Escribe un script que recorra `/proc` y detecte procesos en estado zombi, listando su PID, PPID y nombre del ejecutable. Este ejercicio debe realizarse sin utilizar `ps`.

---

### Ejercicio 10: Inyección de comandos en procesos huérfanos (Análisis de riesgo)
Simula un escenario donde un proceso huérfano ejecuta un comando externo sin control del padre. Analiza qué implicaciones tendría esto en términos de seguridad o evasión de auditorías.