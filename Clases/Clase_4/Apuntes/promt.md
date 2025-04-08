# Guía de Estudio sobre Pipes en Programación Concurrente

¡Hola! Entiendo que estás cursando Computación II y necesitas aprender sobre pipes en programación concurrente. Vamos a seguir la estructura que has propuesto, comenzando con la teoría fundamental antes de avanzar a implementaciones prácticas.

## 1. Fundamentos Teóricos de Pipes

### ¿Qué son los Pipes?

Los pipes son uno de los mecanismos más antiguos y fundamentales para la comunicación entre procesos (IPC - Inter-Process Communication). En esencia, un pipe es un canal de comunicación unidireccional que permite que un proceso escriba datos en un extremo y otro proceso lea esos datos desde el otro extremo.

Los pipes funcionan como una cola FIFO (First In, First Out), lo que significa que los datos se leen en el mismo orden en que fueron escritos. Conceptualmente, podemos visualizar un pipe como una tubería por la que fluyen datos en una sola dirección.

### Tipos de Pipes

Existen principalmente dos tipos de pipes:

1. **Pipes sin nombre (Anonymous Pipes)**: 
   - Solo pueden ser utilizados entre procesos relacionados (padre-hijo)
   - Existen únicamente mientras los procesos que los utilizan estén en ejecución
   - No tienen representación en el sistema de archivos

2. **Pipes con nombre (Named Pipes o FIFOs)**:
   - Permiten comunicación entre procesos no relacionados
   - Tienen representación en el sistema de archivos (como un archivo especial)
   - Pueden persistir incluso después de que los procesos terminen

### Importancia en Sistemas Operativos

Los pipes son fundamentales en sistemas operativos UNIX/Linux por varias razones:

- Permiten implementar el concepto de composición de comandos (usando `|` en la terminal)
- Facilitan la arquitectura de filtros, donde cada proceso realiza una tarea específica
- Proporcionan un método simple y eficiente para la comunicación entre procesos
- Son la base de muchos patrones de diseño en programación de sistemas

### Limitaciones de los Pipes

- Son unidireccionales (para comunicación bidireccional se necesitan dos pipes)
- Transmiten datos sin estructura (bytes en bruto)
- No funcionan para comunicación entre máquinas diferentes (solo local)
- Tienen capacidad limitada (buffer finito)

---

**ALTO PARA PUESTA EN COMÚN**

Antes de continuar, asegúrate de comprender estos conceptos fundamentales sobre los pipes. Es momento de compartir tu avance con el profesor y compañeros.

**Preguntas de comprensión:**
1. ¿Cuál es la principal diferencia entre pipes con nombre y sin nombre?
2. ¿Por qué decimos que los pipes implementan una estructura FIFO y qué implica esto?
3. ¿En qué situaciones los pipes no serían la mejor opción para comunicación entre procesos?

---

## 2. Implementación Interna y Ciclo de Vida

### Implementación a Nivel de Sistema Operativo

En sistemas UNIX/Linux, un pipe se implementa internamente como:

1. **Un buffer de tamaño fijo en memoria del kernel** (típicamente entre 4KB-64KB)
2. **Dos descriptores de archivo**: uno para lectura y otro para escritura
3. **Metadatos asociados** que el kernel utiliza para gestionar el pipe

Cuando se crea un pipe usando la llamada al sistema `pipe()`, el kernel:
- Asigna espacio para el buffer en memoria
- Crea dos descriptores de archivo: uno con permisos de solo lectura y otro con permisos de solo escritura
- Devuelve ambos descriptores al proceso que lo solicitó

### Ciclo de Vida de un Pipe

1. **Creación**: 
   - Para pipes sin nombre: mediante llamada al sistema `pipe()`
   - Para pipes con nombre: mediante `mkfifo()` o el comando `mkfifo`

2. **Uso**:
   - Escritura: los datos se escriben en el descriptor de escritura
   - Lectura: los datos se leen desde el descriptor de lectura
   - Si el buffer está lleno, las escrituras se bloquean
   - Si el buffer está vacío, las lecturas se bloquean

3. **Destrucción**:
   - Pipes sin nombre: se destruyen cuando se cierran todos los descriptores
   - Pipes con nombre: persisten como archivos especiales hasta que se eliminan explícitamente

### Comportamiento de E/S en Pipes

- **Atomicidad**: Las escrituras de hasta un cierto tamaño (PIPE_BUF, generalmente 4KB) son atómicas
- **Bloqueo**: 
  - Lectura en pipe vacío: se bloquea hasta que haya datos o todos los escritores cierren su extremo
  - Escritura en pipe lleno: se bloquea hasta que haya espacio disponible
- **EOF (End of File)**: Se señaliza cuando todos los descriptores de escritura se cierran

### Señales y Manejo de Excepciones

- Si un proceso intenta escribir en un pipe sin lectores, recibe la señal SIGPIPE
- Si todos los escritores cierran su extremo, los lectores reciben EOF (read devuelve 0)
- Si todos los lectores cierran su extremo, los escritores reciben SIGPIPE al intentar escribir

---

**ALTO PARA PUESTA EN COMÚN**

Es momento de asegurarte que comprendes los aspectos técnicos de la implementación de pipes. Comparte tu progreso con el profesor.

**Preguntas de comprensión:**
1. ¿Qué sucede cuando un proceso intenta escribir en un pipe que no tiene lectores activos?
2. ¿Por qué es importante cerrar los descriptores de archivo de un pipe que no se utilizan?
3. ¿Qué significa que una escritura en un pipe sea "atómica" y por qué es importante?

---

## 3. Implementación de Pipes en Python

Python ofrece varias formas de trabajar con pipes, desde la biblioteca estándar hasta módulos más especializados.

### Usando el Módulo `os`

El módulo `os` proporciona acceso directo a la llamada al sistema `pipe()`:

```python
import os

# Crear un pipe
read_fd, write_fd = os.pipe()

# Los descriptores son números enteros que representan descriptores de archivo
print(f"Descriptor de lectura: {read_fd}, Descriptor de escritura: {write_fd}")

# Para trabajar con ellos como archivos Python
reader = os.fdopen(read_fd, 'rb')
writer = os.fdopen(write_fd, 'wb')

# Ahora podemos usar reader.read() y writer.write()
```

### Usando el Módulo `subprocess`

El módulo `subprocess` facilita la creación de pipes entre procesos:

```python
import subprocess

# Crear un proceso y conectar a sus stdin/stdout mediante pipes
proceso = subprocess.Popen(['comando', 'arg1'], 
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE)

# Escribir en stdin del proceso
proceso.stdin.write(b"datos de entrada\n")
proceso.stdin.flush()  # Importante para forzar la escritura

# Leer de stdout del proceso
salida = proceso.stdout.readline()
print(salida.decode('utf-8'))

# Cerrar los pipes y esperar a que termine el proceso
proceso.stdin.close()
proceso.wait()
```

### Usando el Módulo `multiprocessing`

El módulo `multiprocessing` ofrece una abstracción de alto nivel:

```python
from multiprocessing import Process, Pipe

def proceso_hijo(conn):
    # El hijo cierra el extremo de recepción
    conn.send(['hola', 'desde', 'hijo'])
    conn.close()

# Crear un pipe
parent_conn, child_conn = Pipe()

# Crear un proceso hijo
p = Process(target=proceso_hijo, args=(child_conn,))
p.start()

# Leer desde el proceso padre
print(parent_conn.recv())  # Imprime: ['hola', 'desde', 'hijo']

# Cerrar el extremo del padre y esperar al hijo
parent_conn.close()
p.join()
```

### Pipes con Nombre (Named Pipes / FIFOs)

```python
import os
import time

fifo_path = "/tmp/mi_fifo"

# Crear un FIFO si no existe
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# En un proceso/thread para escritura
with open(fifo_path, 'w') as fifo:
    fifo.write("Mensaje a través del FIFO\n")

# En otro proceso/thread para lectura
with open(fifo_path, 'r') as fifo:
    data = fifo.read()
    print(f"Leído del FIFO: {data}")
```

### Consideraciones Importantes

- **Codificación**: Los pipes transmiten bytes, no texto. Necesitas codificar/decodificar si trabajas con cadenas.
- **Buffering**: El buffering puede causar bloqueos inesperados; usa `flush()` después de escribir.
- **Cierre de descriptores**: Siempre cierra los extremos no utilizados para evitar fugas de recursos.
- **Deadlocks**: Ten cuidado con situaciones donde procesos se bloquean esperando mutuamente.

---

**ALTO PARA PUESTA EN COMÚN**

Asegúrate de comprender las diferentes formas de implementar pipes en Python. Comparte tu progreso con el profesor.

**Preguntas de comprensión:**
1. ¿Cuáles son las principales diferencias entre usar `os.pipe()` y `multiprocessing.Pipe()`?
2. ¿Por qué es importante llamar a `flush()` después de escribir en un pipe?
3. ¿Qué sucede si no cierras un descriptor de archivo de pipe que ya no necesitas?

---

## 4. Ejemplo Práctico: Comunicación Unidireccional Entre Procesos

Vamos a implementar un ejemplo completo de comunicación unidireccional entre un proceso padre e hijo usando pipes.

```python
#!/usr/bin/env python3
"""
Ejemplo de comunicación unidireccional entre procesos usando pipes en Python.
El proceso padre envía una serie de números al proceso hijo,
quien calcula su cuadrado y lo imprime.
"""

import os
import sys
import time
from typing import List


def proceso_hijo(read_fd: int):
    """
    Función que ejecuta el proceso hijo.
    Lee números del pipe, calcula su cuadrado y lo imprime.
    
    Args:
        read_fd: Descriptor de archivo para lectura del pipe
    """
    # Cerramos extremo de escritura que heredamos del padre pero no usamos
    # Esto es crucial para el correcto funcionamiento
    os.close(write_fd)
    
    # Convertimos el descriptor a un objeto de archivo Python
    pipe_read = os.fdopen(read_fd, 'r')
    
    print(f"[HIJO] PID {os.getpid()}: Esperando datos del padre...")
    
    # Leemos del pipe línea por línea hasta recibir "FIN"
    while True:
        line = pipe_read.readline().strip()
        
        # Verificamos si es señal de fin
        if line == "FIN" or not line:
            break
            
        # Convertimos a número y calculamos su cuadrado
        try:
            num = int(line)
            result = num * num
            print(f"[HIJO] Recibido: {num}, Cuadrado: {result}")
        except ValueError:
            print(f"[HIJO] Error: No pude convertir '{line}' a número")
        
        # Pequeña pausa para simular procesamiento
        time.sleep(0.5)
    
    print(f"[HIJO] Terminando proceso hijo (PID {os.getpid()})")
    pipe_read.close()
    sys.exit(0)


def proceso_padre(write_fd: int, numeros: List[int]):
    """
    Función que ejecuta el proceso padre.
    Envía números al proceso hijo a través del pipe.
    
    Args:
        write_fd: Descriptor de archivo para escritura del pipe
        numeros: Lista de números a enviar al hijo
    """
    # Cerramos extremo de lectura que no usamos
    os.close(read_fd)
    
    # Convertimos el descriptor a un objeto de archivo Python
    pipe_write = os.fdopen(write_fd, 'w')
    
    print(f"[PADRE] PID {os.getpid()}: Enviando datos al hijo...")
    
    # Enviamos cada número como una línea de texto
    for num in numeros:
        print(f"[PADRE] Enviando: {num}")
        pipe_write.write(f"{num}\n")
        pipe_write.flush()  # Importante: forzar la escritura inmediata
        time.sleep(1)  # Pausa entre envíos
    
    # Enviamos señal de finalización
    print("[PADRE] Enviando señal de finalización")
    pipe_write.write("FIN\n")
    pipe_write.flush()
    pipe_write.close()


if __name__ == "__main__":
    # Creamos el pipe
    read_fd, write_fd = os.pipe()
    
    # Lista de números a procesar
    numeros = [1, 5, 10, 15, 20]
    
    # Creamos un proceso hijo
    pid = os.fork()
    
    if pid == 0:
        # Estamos en el proceso hijo
        proceso_hijo(read_fd)
    else:
        # Estamos en el proceso padre
        print(f"[PADRE] Creado proceso hijo con PID {pid}")
        proceso_padre(write_fd, numeros)
        
        # Esperamos a que el hijo termine
        os.waitpid(pid, 0)
        print("[PADRE] El proceso hijo ha terminado")

```

### Explicación del Código

1. **Creación del pipe**: Usamos `os.pipe()` para crear un pipe sin nombre, obteniendo dos descriptores de archivo.

2. **Fork del proceso**: Con `os.fork()` creamos un proceso hijo que hereda una copia de todos los descriptores de archivo del padre.

3. **Proceso hijo**:
   - Cierra el descriptor de escritura que no utilizará
   - Convierte el descriptor de lectura en un objeto de archivo Python
   - Lee líneas del pipe y procesa cada número recibido
   - Termina cuando recibe la señal "FIN"

4. **Proceso padre**:
   - Cierra el descriptor de lectura que no utilizará
   - Envía números al hijo a través del pipe
   - Envía señal de finalización y espera a que el hijo termine

5. **Manejo adecuado de recursos**:
   - Cerramos los extremos no utilizados
   - Utilizamos `flush()` para forzar escrituras inmediatas
   - Limpiamos los recursos al finalizar

Este ejemplo demuestra varios conceptos importantes:
- Comunicación unidireccional padre-hijo
- Protocolo simple de comunicación (números en líneas y señal "FIN")
- Cierre correcto de descriptores no utilizados
- Sincronización básica entre procesos

---

**ALTO PARA PUESTA EN COMÚN**

Es momento de asegurarte que comprendes el ejemplo práctico. Intenta ejecutarlo y observa su comportamiento. Comparte tu experiencia y resultados con el profesor.

**Preguntas de comprensión:**
1. ¿Por qué es importante cerrar los extremos del pipe que no se utilizan en cada proceso?
2. ¿Qué sucedería si eliminaras la llamada a `flush()` después de cada escritura?
3. ¿Cómo podrías modificar este código para enviar datos más complejos que números enteros?

---

## 5. Patrones Avanzados con Pipes

Ahora vamos a explorar dos patrones más avanzados: la implementación de un pipeline (similar a los pipes de shell) y la comunicación bidireccional entre procesos.

### Patrón Pipeline

El patrón pipeline permite conectar varios procesos en serie, donde la salida de uno es la entrada del siguiente.

```python
#!/usr/bin/env python3
"""
Implementación de un pipeline de tres etapas usando pipes:
1. Generador: Produce números del 1 al 10
2. Filtro: Filtra solo los números pares
3. Procesador: Calcula el cuadrado de los números filtrados
"""

import os
import sys
import time


def etapa_generador(write_fd):
    """Genera números del 1 al 10 y los envía a la siguiente etapa."""
    # Cerramos descriptores que no usamos
    os.close(pipe1_read)
    os.close(pipe2_read)
    os.close(pipe2_write)
    
    # Convertimos descriptor a archivo
    pipe_write = os.fdopen(write_fd, 'w')
    
    print(f"[GENERADOR] PID {os.getpid()}: Generando números...")
    
    # Generamos números del 1 al 10
    for i in range(1, 11):
        print(f"[GENERADOR] Produciendo: {i}")
        pipe_write.write(f"{i}\n")
        pipe_write.flush()
        time.sleep(0.5)
    
    # Señal de finalización
    pipe_write.write("FIN\n")
    pipe_write.flush()
    pipe_write.close()
    print("[GENERADOR] Terminado")
    sys.exit(0)


def etapa_filtro(read_fd, write_fd):
    """Lee números, filtra solo los pares y los envía a la siguiente etapa."""
    # Cerramos descriptores que no usamos
    os.close(pipe1_write)
    os.close(pipe2_read)
    
    # Convertimos descriptores a archivos
    pipe_read = os.fdopen(read_fd, 'r')
    pipe_write = os.fdopen(write_fd, 'w')
    
    print(f"[FILTRO] PID {os.getpid()}: Filtrando números pares...")
    
    # Leemos cada línea
    while True:
        line = pipe_read.readline().strip()
        
        # Verificamos si es fin
        if line == "FIN" or not line:
            break
            
        # Filtramos los pares
        try:
            num = int(line)
            if num % 2 == 0:  # Es par
                print(f"[FILTRO] Pasando número par: {num}")
                pipe_write.write(f"{num}\n")
                pipe_write.flush()
            else:
                print(f"[FILTRO] Descartando número impar: {num}")
        except ValueError:
            print(f"[FILTRO] Error: No pude convertir '{line}' a número")
    
    # Señal de finalización
    pipe_write.write("FIN\n")
    pipe_write.flush()
    pipe_read.close()
    pipe_write.close()
    print("[FILTRO] Terminado")
    sys.exit(0)


def etapa_procesador(read_fd):
    """Lee números filtrados y calcula su cuadrado."""
    # Cerramos descriptores que no usamos
    os.close(pipe1_read)
    os.close(pipe1_write)
    os.close(pipe2_write)
    
    # Convertimos descriptor a archivo
    pipe_read = os.fdopen(read_fd, 'r')
    
    print(f"[PROCESADOR] PID {os.getpid()}: Calculando cuadrados...")
    
    # Leemos cada línea
    while True:
        line = pipe_read.readline().strip()
        
        # Verificamos si es fin
        if line == "FIN" or not line:
            break
            
        # Calculamos el cuadrado
        try:
            num = int(line)
            result = num * num
            print(f"[PROCESADOR] Número: {num}, Cuadrado: {result}")
        except ValueError:
            print(f"[PROCESADOR] Error: No pude convertir '{line}' a número")
    
    pipe_read.close()
    print("[PROCESADOR] Terminado")
    sys.exit(0)


if __name__ == "__main__":
    # Creamos dos pipes para conectar las tres etapas
    pipe1_read, pipe1_write = os.pipe()  # Conexión Generador -> Filtro
    pipe2_read, pipe2_write = os.pipe()  # Conexión Filtro -> Procesador
    
    # Creamos el proceso para la etapa 3 (Procesador)
    pid_procesador = os.fork()
    
    if pid_procesador == 0:
        # Estamos en el proceso Procesador
        etapa_procesador(pipe2_read)
    else:
        # Continuamos en el proceso padre para crear la etapa 2
        print(f"[PRINCIPAL] Creado proceso Procesador con PID {pid_procesador}")
        
        pid_filtro = os.fork()
        
        if pid_filtro == 0:
            # Estamos en el proceso Filtro
            etapa_filtro(pipe1_read, pipe2_write)
        else:
            # Continuamos en el proceso padre para crear la etapa 1
            print(f"[PRINCIPAL] Creado proceso Filtro con PID {pid_filtro}")
            
            pid_generador = os.fork()
            
            if pid_generador == 0:
                # Estamos en el proceso Generador
                etapa_generador(pipe1_write)
            else:
                # Estamos en el proceso principal
                print(f"[PRINCIPAL] Creado proceso Generador con PID {pid_generador}")
                
                # Cerramos todos los descriptores en el proceso principal
                # ya que no los usamos
                os.close(pipe1_read)
                os.close(pipe1_write)
                os.close(pipe2_read)
                os.close(pipe2_write)
                
                # Esperamos a que terminen todos los procesos hijos
                print("[PRINCIPAL] Esperando a que terminen los procesos...")
                os.waitpid(pid_generador, 0)
                os.waitpid(pid_filtro, 0)
                os.waitpid(pid_procesador, 0)
                print("[PRINCIPAL] Todos los procesos han terminado")

```

### Comunicación Bidireccional

Para implementar comunicación bidireccional, necesitamos dos pipes, uno para cada dirección.

```python
#!/usr/bin/env python3
"""
Ejemplo de comunicación bidireccional entre procesos usando pipes.
El proceso padre envía números al hijo, quien responde con sus cuadrados.
"""

import os
import sys
import time


def proceso_hijo(pipe_read_fd, pipe_write_fd):
    """
    Función para el proceso hijo que recibe números,
    calcula sus cuadrados y responde al padre.
    """
    # Convertimos los descriptores a archivos Python
    pipe_read = os.fdopen(pipe_read_fd, 'r')
    pipe_write = os.fdopen(pipe_write_fd, 'w')
    
    print(f"[HIJO] PID {os.getpid()}: Listo para recibir números")
    
    # Procesamos números hasta recibir "FIN"
    while True:
        # Leemos un número del padre
        line = pipe_read.readline().strip()
        
        if line == "FIN" or not line:
            break
            
        try:
            num = int(line)
            print(f"[HIJO] He recibido el número: {num}")
            
            # Calculamos el cuadrado
            result = num * num
            
            # Respondemos al padre
            print(f"[HIJO] Enviando el cuadrado: {result}")
            pipe_write.write(f"{result}\n")
            pipe_write.flush()
            
        except ValueError:
            print(f"[HIJO] Error: No pude convertir '{line}' a número")
            pipe_write.write("ERROR\n")
            pipe_write.flush()
    
    # Cerramos los pipes y terminamos
    print("[HIJO] Terminando proceso")
    pipe_read.close()
    pipe_write.close()
    sys.exit(0)


def proceso_padre(pipe_write_fd, pipe_read_fd, numeros):
    """
    Función para el proceso padre que envía números al hijo
    y recibe los cuadrados calculados.
    """
    # Convertimos los descriptores a archivos Python
    pipe_write = os.fdopen(pipe_write_fd, 'w')
    pipe_read = os.fdopen(pipe_read_fd, 'r')
    
    print(f"[PADRE] PID {os.getpid()}: Enviando números al hijo")
    
    # Enviamos cada número y esperamos su respuesta
    for num in numeros:
        # Enviamos el número
        print(f"[PADRE] Enviando número: {num}")
        pipe_write.write(f"{num}\n")
        pipe_write.flush()
        
        # Esperamos la respuesta
        response = pipe_read.readline().strip()
        
        if response == "ERROR":
            print(f"[PADRE] El hijo reportó un error procesando {num}")
        else:
            try:
                result = int(response)
                print(f"[PADRE] Cuadrado de {num} = {result}")
            except ValueError:
                print(f"[PADRE] Respuesta inesperada: '{response}'")
        
        # Pequeña pausa entre operaciones
        time.sleep(1)
    
    # Enviamos señal de finalización
    print("[PADRE] Enviando señal de finalización")
    pipe_write.write("FIN\n")
    pipe_write.flush()
    
    # Cerramos los pipes
    pipe_write.close()
    pipe_read.close()


if __name__ == "__main__":
    # Creamos dos pipes para comunicación bidireccional
    # pipe1: padre -> hijo
    pipe1_read, pipe1_write = os.pipe()
    
    # pipe2: hijo -> padre
    pipe2_read, pipe2_write = os.pipe()
    
    # Lista de números a procesar
    numeros = [3, 7, 12, 8, 21]
    
    # Creamos el proceso hijo
    pid = os.fork()
    
    if pid == 0:
        # Proceso hijo
        # Cerramos extremos que no usamos
        os.close(pipe1_write)
        os.close(pipe2_read)
        
        # Ejecutamos la función del hijo
        proceso_hijo(pipe1_read, pipe2_write)
    else:
        # Proceso padre
        print(f"[PADRE] Creado proceso hijo con PID {pid}")
        
        # Cerramos extremos que no usamos
        os.close(pipe1_read)
        os.close(pipe2_write)
        
        # Ejecutamos la función del padre
        proceso_padre(pipe1_write, pipe2_read, numeros)
        
        # Esperamos a que el hijo termine
        os.waitpid(pid, 0)
        print("[PADRE] El proceso hijo ha terminado")

```

### Prevención de Problemas Comunes

#### 1. Deadlocks

Los deadlocks (bloqueos mutuos) ocurren cuando dos o más procesos se quedan esperando indefinidamente recursos que tienen otros procesos. Con pipes, esto puede ocurrir por:

- Un proceso esperando leer de un pipe vacío cuando todos los escritores ya cerraron su extremo
- Procesos esperando mutuamente por datos que nunca llegan

**Soluciones**:
- Cerrar siempre los extremos del pipe que no se utilizan
- Usar timeouts en operaciones de lectura/escritura
- Implementar protocolos claros de comunicación con señales de fin
- Evitar esperas circulares entre procesos

#### 2. Buffer Overflow

Si un proceso escribe mucho más rápido de lo que otro lee, el buffer del pipe puede llenarse, lo que bloquea al escritor.

**Soluciones**:
- Equilibrar la velocidad de lectura/escritura
- Implementar comunicación con confirmaciones (acknowledge)
- Considerar usar pipes no bloqueantes para manejar este caso

#### 3. Pérdida de Datos

Si un proceso termina abruptamente sin cerrar correctamente los pipes, puede haber pérdida de datos.

**Soluciones**:
- Implementar manejo de señales
- Usar try/finally para garantizar cierre de pipes
- Implementar mecanismos de recuperación

---

**ALTO PARA PUESTA EN COMÚN**

Es momento de revisar estos patrones más avanzados. Intenta ejecutar los ejemplos y comprende su funcionamiento. Comparte tus observaciones con el profesor.

**Preguntas de comprensión:**
1. ¿Cómo se implementa la comunicación bidireccional usando pipes y por qué necesitamos dos pipes?
2. ¿Qué ventajas ofrece el patrón pipeline para el procesamiento de datos?
3. ¿Cómo podrías detectar y resolver un deadlock en un sistema que utiliza pipes?

---
