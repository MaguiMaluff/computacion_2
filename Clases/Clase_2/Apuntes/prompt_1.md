# Procesos en Sistemas Operativos: Guía Completa

¡Bienvenido a esta sesión de aprendizaje sobre procesos en sistemas operativos! Vamos a seguir una estructura paso a paso, comenzando con los fundamentos y avanzando hacia implementaciones prácticas en Python.

## 1. Fundamentos de procesos

### Definición formal de proceso

Un **proceso** es una instancia de un programa en ejecución. Formalmente, podemos definirlo como una entidad activa que consiste en:

- Un **espacio de direcciones**: la memoria asignada al proceso
- Un **conjunto de atributos de control**: información que el sistema operativo utiliza para gestionar el proceso

Los atributos principales de un proceso incluyen:

- **PID (Process ID)**: Identificador único del proceso
- **Estado**: Running, Ready, Blocked, etc.
- **Contador de programa**: Indica la dirección de la próxima instrucción a ejecutar
- **Registros de CPU**: Valores actuales de los registros
- **Información de gestión de memoria**: Punteros a tablas de páginas, segmentos
- **Información contable**: Tiempo de CPU usado, límites de tiempo
- **Información de estado de E/S**: Dispositivos asignados, archivos abiertos

### Diferencias entre programa y proceso

| Programa | Proceso |
|----------|---------|
| Entidad pasiva | Entidad activa |
| Conjunto de instrucciones almacenadas en disco | Programa en ejecución |
| No cambia durante su existencia | Cambia constantemente su estado |
| No consume recursos de CPU o memoria hasta ser ejecutado | Consume recursos del sistema mientras está en ejecución |
| Puede existir como archivo sin ejecutarse | Solo existe durante su ejecución |

### Historia y evolución del concepto de procesos

- **Primera generación (1945-1955)**: Computadoras sin sistema operativo, un programa ocupaba toda la máquina
- **Segunda generación (1955-1965)**: Sistemas batch simples, un proceso a la vez
- **Tercera generación (1965-1980)**: Multiprogramación, varios procesos en memoria
- **Cuarta generación (1980-presente)**: Sistemas multiusuario, multiprocesador con procesos y threads

**🔍 ALTO PARA PUESTA EN COMÚN CON LA CLASE**

Preguntas de comprensión:
1. ¿Cuáles son las principales diferencias entre un programa y un proceso?
2. ¿Qué atributos son esenciales para la gestión de un proceso por parte del SO?
3. ¿Cómo ha evolucionado el concepto de proceso desde los primeros sistemas operativos?

Recuerda compartir tus respuestas con el profesor antes de continuar.

## 2. El modelo de procesos en UNIX/Linux

### Jerarquía de procesos y herencia

En UNIX/Linux, los procesos siguen un modelo jerárquico donde:

- Cada proceso (excepto el primero) es creado por otro proceso llamado "proceso padre"
- El proceso creado se denomina "proceso hijo"
- Se forma un árbol de procesos con una relación padre-hijo
- Los hijos heredan muchas características de sus padres:
  - Variables de entorno
  - Descriptores de archivos abiertos
  - Directorio de trabajo actual
  - Máscaras de permisos

### El proceso init/systemd

- **init (PID 1)**: Tradicionalmente el primer proceso creado por el kernel
- **systemd**: Reemplaza a init en muchas distribuciones Linux modernas
- Funciones principales:
  - Adoptar procesos huérfanos
  - Iniciar servicios del sistema
  - Gestionar el apagado ordenado del sistema

### Visualización de procesos mediante herramientas del sistema

Las principales herramientas para visualizar procesos son:

- **ps**: Muestra instantáneas de los procesos actuales
  ```bash
  ps aux               # Lista todos los procesos
  ps -ef | grep python # Filtra procesos python
  ```

- **top/htop**: Muestra procesos en tiempo real con uso de recursos
  ```bash
  top                  # Visualización básica
  htop                 # Versión mejorada (requiere instalación)
  ```

- **pstree**: Muestra procesos en formato de árbol jerárquico
  ```bash
  pstree               # Árbol de procesos completo
  pstree -p            # Incluye PIDs
  ```

**🔍 ALTO PARA PUESTA EN COMÚN CON LA CLASE**

Preguntas de comprensión:
1. ¿Qué características heredan los procesos hijos de sus padres en sistemas UNIX/Linux?
2. ¿Cuál es el rol del proceso init/systemd en el sistema operativo?
3. ¿Qué comando utilizarías para ver la jerarquía de procesos en formato de árbol?

Recuerda compartir tus respuestas con el profesor antes de continuar.

## 3. Manipulación de procesos con Python

### Uso del módulo os para fork() y exec()

Python proporciona acceso a las llamadas del sistema a través del módulo `os`, permitiéndonos crear y manipular procesos.

#### La llamada fork()

`fork()` crea una copia del proceso actual. Después de la llamada:
- El proceso hijo recibe un valor de retorno 0
- El proceso padre recibe el PID del hijo como valor de retorno

```python
import os

# Creamos un proceso hijo con fork()
pid = os.fork()

if pid == 0:
    # Código ejecutado por el proceso hijo
    print(f"Soy el proceso HIJO. Mi PID es {os.getpid()}")
    print(f"El PID de mi padre es {os.getppid()}")
else:
    # Código ejecutado por el proceso padre
    print(f"Soy el proceso PADRE. Mi PID es {os.getpid()}")
    print(f"Acabo de crear un hijo con PID {pid}")

# Este código se ejecuta tanto en el padre como en el hijo
print(f"Este mensaje aparece dos veces (PID: {os.getpid()})")

```

#### La familia de llamadas exec()

Las llamadas `exec*()` reemplazan la imagen del proceso actual con un nuevo programa:

```python
import os

print(f"Inicio del programa: PID {os.getpid()}")

# Creamos un proceso hijo
pid = os.fork()

if pid == 0:
    # El hijo ejecutará el comando 'ls -l'
    print(f"Soy el hijo ({os.getpid()}) y voy a ejecutar 'ls -l'")
    os.execvp('ls', ['ls', '-l'])
    # Este código nunca se ejecuta porque exec reemplaza el proceso
    print("Este mensaje nunca se mostrará")
else:
    # El padre espera a que el hijo termine
    print(f"Soy el padre ({os.getpid()}) esperando a que mi hijo ({pid}) termine")
    os.waitpid(pid, 0)
    print("Mi hijo ha terminado")

```

### Creación de procesos hijos

Un patrón común es combinar `fork()` y `exec()` para crear nuevos procesos que ejecuten programas diferentes:

```python
import os
import sys

print(f"Programa principal con PID: {os.getpid()}")

# Creamos un proceso hijo
pid = os.fork()

if pid == 0:
    # Código del hijo
    print(f"Hijo creado con PID: {os.getpid()}")
    try:
        # Ejecutamos el comando 'echo' con argumentos
        os.execvp('echo', ['echo', 'Hola', 'desde', 'el', 'proceso', 'hijo'])
    except Exception as e:
        print(f"Error al ejecutar el comando: {e}")
        sys.exit(1)
else:
    # Código del padre
    print(f"Padre con PID: {os.getpid()}, hijo creado con PID: {pid}")
    # Esperamos a que termine el hijo
    child_pid, status = os.waitpid(pid, 0)
    print(f"Hijo {child_pid} terminado con estado: {status}")

```

### Espera y sincronización básica entre procesos

Existen varias formas de esperar a que los procesos hijos terminen:

```python
import os
import sys
import time

def crear_hijo(nombre, tiempo_espera):
    pid = os.fork()
    
    if pid == 0:  # Proceso hijo
        print(f"Hijo '{nombre}' iniciado (PID: {os.getpid()})")
        time.sleep(tiempo_espera)
        print(f"Hijo '{nombre}' terminando...")
        sys.exit(nombre.count('o'))  # Salimos con un código basado en el nombre
    
    return pid  # Retornamos el PID al proceso padre

# Creamos varios hijos
pid1 = crear_hijo("uno", 3)
pid2 = crear_hijo("dos", 1)
pid3 = crear_hijo("tres", 2)

print(f"Padre (PID: {os.getpid()}) esperando a los hijos...")

# Método 1: os.waitpid() - Esperar a un hijo específico
pid, status = os.waitpid(pid2, 0)  # Esperamos específicamente al segundo hijo
print(f"Hijo con PID {pid} terminó primero (estado: {os.WEXITSTATUS(status)})")

# Método 2: os.wait() - Esperar a cualquier hijo
pid, status = os.wait()  # Esperamos a cualquier hijo (probablemente pid3)
print(f"Hijo con PID {pid} terminó segundo (estado: {os.WEXITSTATUS(status)})")

# Método 3: os.waitpid() con opciones - No bloqueante
try:
    # WNOHANG hace que waitpid retorne inmediatamente si no hay hijos terminados
    pid, status = os.waitpid(-1, os.WNOHANG)
    if pid != 0:
        print(f"Hijo con PID {pid} ya había terminado (estado: {os.WEXITSTATUS(status)})")
    else:
        print("No hay hijos terminados en este momento")
except ChildProcessError:
    print("No hay más hijos para esperar")

# Método 4: esperar a todos los hijos restantes
try:
    while True:
        pid, status = os.wait()
        print(f"Hijo con PID {pid} terminó (estado: {os.WEXITSTATUS(status)})")
except ChildProcessError:
    print("Todos los hijos han terminado")

```

**🔍 ALTO PARA PUESTA EN COMÚN CON LA CLASE**

Preguntas de comprensión:
1. ¿Qué valores retorna la llamada `fork()` y cómo se interpretan en el padre y en el hijo?
2. ¿Cuál es la diferencia principal entre las llamadas `fork()` y `exec()`?
3. ¿Por qué es importante utilizar `os.wait()` o `os.waitpid()` en el proceso padre?

Recuerda compartir tus respuestas con el profesor antes de continuar.

## 4. Procesos zombis y huérfanos

### Procesos zombis: causas y consecuencias

Un **proceso zombi** es un proceso hijo que ha terminado su ejecución pero cuyo estado de salida aún no ha sido recogido por su padre.

- **Causas**: El padre no ejecuta `wait()` o `waitpid()` después de que el hijo termina
- **Consecuencias**: 
  - Ocupan entradas en la tabla de procesos del kernel
  - No consumen recursos significativos (CPU, memoria)
  - Si se acumulan en gran número, pueden agotar la tabla de procesos

```python
import os
import sys
import time

def crear_zombi():
    pid = os.fork()
    
    if pid == 0:  # Proceso hijo
        print(f"Hijo iniciado (PID: {os.getpid()})")
        # El hijo termina inmediatamente
        print(f"Hijo terminando... ahora seré un zombi")
        sys.exit(0)
    else:  # Proceso padre
        print(f"Padre (PID: {os.getpid()}) creó un hijo (PID: {pid})")
        print("El padre NO llamará a wait(), creando un zombi")
        
        # El padre sigue ejecutándose sin recoger el estado del hijo
        print("\nEjecuta en otra terminal: ps aux | grep defunct")
        print("o: ps -l | grep Z")
        print("para ver el proceso zombi")
        
        # Esperamos un tiempo para poder observar el zombi
        time.sleep(30)
        
        # Finalmente recogemos el estado
        print("\nRecogiendo el estado del hijo zombi...")
        pid, status = os.waitpid(pid, 0)
        print(f"Hijo zombi (PID: {pid}) recogido, estado: {status}")

crear_zombi()

```

### Procesos huérfanos: causas y consecuencias

Un **proceso huérfano** es un proceso cuyo padre ha terminado antes que él.

- **Causas**: El proceso padre termina sin esperar a que sus hijos terminen
- **Consecuencias**:
  - Son adoptados por el proceso init/systemd (PID 1)
  - Continúan su ejecución normal
  - Al terminar, init recoge su estado de salida (no se convierten en zombis)

```python
import os
import sys
import time

def crear_huerfano():
    pid = os.fork()
    
    if pid == 0:  # Proceso hijo
        # El hijo se ejecutará por más tiempo que el padre
        print(f"Hijo iniciado (PID: {os.getpid()}, Padre original: {os.getppid()})")
        print("El hijo dormirá 30 segundos mientras el padre termina...")
        
        # Esperamos un poco para que el padre tenga tiempo de terminar
        time.sleep(5)
        
        # En este punto, el padre probablemente ya terminó
        nuevo_ppid = os.getppid()
        print(f"PPID actual del hijo: {nuevo_ppid}")
        
        if nuevo_ppid == 1 or nuevo_ppid != pid:
            print("¡Me he convertido en huérfano! He sido adoptado por init/systemd")
        
        # Seguimos ejecutando para poder observar el proceso
        print("\nEjecuta en otra terminal: ps -f")
        print("para ver que mi padre ahora es init/systemd")
        
        time.sleep(25)
        print("Hijo huérfano terminando...")
        sys.exit(0)
    else:  # Proceso padre
        print(f"Padre (PID: {os.getpid()}) creó un hijo (PID: {pid})")
        print("El padre terminará antes que el hijo, creando un huérfano")
        
        # El padre termina rápidamente
        time.sleep(2)
        print("Padre terminando...")
        sys.exit(0)

crear_huerfano()

```

### Detección mediante herramientas del sistema

Para detectar procesos zombis:
```bash
ps aux | grep defunct    # Muestra procesos zombi (aparecen como <defunct>)
ps -l | grep Z           # Los zombis tienen estado 'Z'
```

Para detectar procesos huérfanos:
```bash
pstree -p               # Buscar procesos cuyo padre sea init/systemd (PID 1)
ps -o pid,ppid,cmd      # Buscar procesos con PPID=1
```

**🔍 ALTO PARA PUESTA EN COMÚN CON LA CLASE**

Preguntas de comprensión:
1. ¿Cuál es la principal diferencia entre un proceso zombi y un proceso huérfano?
2. ¿Por qué se crean los procesos zombis y qué problemas pueden causar?
3. ¿Qué sucede con un proceso huérfano en términos de su jerarquía en el árbol de procesos?

Recuerda compartir tus respuestas con el profesor antes de continuar.

## 5. Ejercicios prácticos progresivos

### Ejercicio 1: Creación de múltiples procesos hijos

```python
import os
import sys
import time
import random

def proceso_hijo(id):
    """Función que ejecutará cada proceso hijo"""
    # Simulamos algún trabajo
    sleep_time = random.uniform(1, 5)
    print(f"Hijo {id} (PID: {os.getpid()}) trabajando durante {sleep_time:.2f} segundos...")
    time.sleep(sleep_time)
    
    # Terminamos con un código de salida basado en el ID
    exit_code = id % 5
    print(f"Hijo {id} (PID: {os.getpid()}) terminando con código {exit_code}")
    sys.exit(exit_code)

def main():
    NUM_HIJOS = 5
    hijos = []
    
    print(f"Padre iniciado (PID: {os.getpid()})")
    
    # Creamos varios procesos hijos
    for i in range(NUM_HIJOS):
        pid = os.fork()
        
        if pid == 0:
            # Código del hijo
            proceso_hijo(i+1)
            # El hijo termina en sys.exit(), nunca llega aquí
        else:
            # Código del padre - guardamos el PID del hijo
            hijos.append(pid)
            print(f"Padre creó hijo {i+1} con PID: {pid}")
    
    print(f"Padre: creados {len(hijos)} hijos. Esperando a que terminen...")
    
    # Esperamos a que todos los hijos terminen y recogemos su estado
    resultados = {}
    for _ in range(len(hijos)):
        pid, status = os.wait()
        exit_code = os.WEXITSTATUS(status)
        resultados[pid] = exit_code
        print(f"Padre: hijo con PID {pid} terminó con código {exit_code}")
    
    # Mostramos un resumen
    print("\nResumen de resultados:")
    for pid, codigo in resultados.items():
        print(f"Hijo PID {pid}: código de salida {codigo}")
    
    print("Todos los hijos han terminado. Padre terminando.")

if __name__ == "__main__":
    main()

```

### Ejercicio 2: Ejecución de comandos externos

```python
import os
import sys
import time

def ejecutar_comando(comando, argumentos):
    """Ejecuta un comando externo en un proceso hijo"""
    pid = os.fork()
    
    if pid == 0:  # Proceso hijo
        print(f"Hijo (PID: {os.getpid()}) ejecutando: {comando} {' '.join(argumentos)}")
        try:
            # Intentamos ejecutar el comando
            os.execvp(comando, [comando] + argumentos)
        except Exception as e:
            print(f"Error al ejecutar '{comando}': {e}")
            sys.exit(1)
    else:  # Proceso padre
        return pid

def main():
    # Lista de comandos a ejecutar
    comandos = [
        ("ls", ["-la", "/tmp"]),
        ("echo", ["Hola", "mundo", "desde", "un", "proceso", "hijo"]),
        ("ps", ["aux"]),
        ("comando_inexistente", [])  # Este comando fallará
    ]
    
    print(f"Proceso principal iniciado (PID: {os.getpid()})")
    
    # Ejecutamos cada comando y guardamos sus PIDs
    procesos = []
    for cmd, args in comandos:
        pid = ejecutar_comando(cmd, args)
        procesos.append((pid, cmd))
        print(f"Lanzado comando '{cmd}' en proceso hijo (PID: {pid})")
        
        # Pequeña pausa para no mezclar salidas
        time.sleep(0.5)
    
    # Esperamos a que todos los procesos terminen
    resultados = []
    for pid, cmd in procesos:
        try:
            child_pid, status = os.waitpid(pid, 0)
            codigo_salida = os.WEXITSTATUS(status)
            resultado = "OK" if codigo_salida == 0 else f"ERROR (código {codigo_salida})"
            resultados.append((cmd, resultado))
        except ChildProcessError:
            resultados.append((cmd, "ERROR (proceso no encontrado)"))
    
    # Mostramos el resumen
    print("\nResumen de ejecución:")
    for cmd, resultado in resultados:
        print(f"Comando '{cmd}': {resultado}")

if __name__ == "__main__":
    main()

```

### Ejercicio 3: Servidor multiproceso simple

```python
import os
import sys
import time
import random
import socket
import signal

# Manejador para la señal SIGCHLD para evitar procesos zombis
def recoger_hijos(signum, frame):
    """Recoger el estado de los hijos terminados"""
    while True:
        try:
            # WNOHANG para no bloquear si no hay hijos terminados
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:  # No hay más hijos terminados
                break
            print(f"Hijo con PID {pid} terminado con estado: {os.WEXITSTATUS(status)}")
        except ChildProcessError:
            break

def procesar_cliente(client_socket, client_address, worker_id):
    """Función ejecutada por cada proceso hijo para atender a un cliente"""
    try:
        print(f"Trabajador {worker_id} (PID: {os.getpid()}) atendiendo a cliente {client_address}")
        
        # Enviamos un mensaje de bienvenida
        mensaje = f"Hola desde el servidor (atendido por proceso {os.getpid()})\n"
        client_socket.send(mensaje.encode())
        
        # Simulamos algo de procesamiento
        tiempo_procesamiento = random.uniform(1, 5)
        time.sleep(tiempo_procesamiento)
        
        # Recibimos datos del cliente (con timeout)
        client_socket.settimeout(10)
        try:
            data = client_socket.recv(1024).decode().strip()
            print(f"Trabajador {worker_id}: recibido '{data}' de {client_address}")
            
            # Enviamos respuesta
            respuesta = f"Recibido: '{data}'. Procesado en {tiempo_procesamiento:.2f}s por proceso {os.getpid()}\n"
            client_socket.send(respuesta.encode())
        except socket.timeout:
            client_socket.send(b"Timeout esperando datos\n")
            
    except Exception as e:
        print(f"Error en trabajador {worker_id}: {e}")
    finally:
        # Cerramos la conexión y salimos
        client_socket.close()
        print(f"Trabajador {worker_id} (PID: {os.getpid()}) terminado")
        sys.exit(0)

def main():
    # Configuramos el manejador de señal para recoger hijos terminados
    signal.signal(signal.SIGCHLD, recoger_hijos)
    
    # Creamos el socket del servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Vinculamos el socket a una dirección y puerto
    host = 'localhost'
    port = 8888
    server_socket.bind((host, port))
    
    # Escuchamos conexiones entrantes
    server_socket.listen(5)
    print(f"Servidor iniciado en {host}:{port} (PID: {os.getpid()})")
    print("Para conectarse, use: telnet localhost 8888")
    
    worker_id = 0
    
    try:
        while True:
            print("Esperando conexiones entrantes...")
            client_socket, client_address = server_socket.accept()
            print(f"Conexión establecida desde {client_address}")
            
            worker_id += 1
            
            # Creamos un proceso hijo para manejar al cliente
            pid = os.fork()
            
            if pid == 0:
                # Código del proceso hijo
                server_socket.close()  # El hijo no necesita el socket del servidor
                procesar_cliente(client_socket, client_address, worker_id)
                # El hijo nunca llega aquí debido al sys.exit() en procesar_cliente
            else:
                # Código del proceso padre
                client_socket.close()  # El padre no necesita el socket del cliente
                print(f"Proceso hijo {pid} creado para atender al cliente {client_address}")
                
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
    finally:
        server_socket.close()
        print("Servidor terminado")

if __name__ == "__main__":
    main()

```

Para probar el servidor multiproceso:
1. Ejecuta el script en una terminal
2. En otra terminal, conéctate usando: `telnet localhost 8888`
3. Escribe un mensaje y presiona Enter
4. Puedes abrir múltiples conexiones telnet simultáneamente para ver el comportamiento multiproceso

**🔍 ALTO PARA PUESTA EN COMÚN CON LA CLASE**

Preguntas de comprensión:
1. En el ejercicio del servidor multiproceso, ¿por qué es importante utilizar el manejador de señal SIGCHLD?
2. ¿Qué sucedería si en el código del servidor no cerráramos el socket del servidor en el proceso hijo?
3. ¿Cuáles son las ventajas de utilizar un modelo multiproceso en lugar de atender a todos los clientes en un solo proceso?

Recuerda compartir tus respuestas con el profesor antes de continuar.

## Conclusión y temas futuros

Hemos cubierto los fundamentos de los procesos en sistemas operativos:
- Aprendimos qué es un proceso y sus atributos principales
- Exploramos el modelo de procesos en UNIX/Linux
- Implementamos la creación y manipulación de procesos con Python
- Estudiamos los procesos zombis y huérfanos
- Desarrollamos ejercicios prácticos, incluyendo un servidor multiproceso

Este conocimiento sienta las bases para temas más avanzados como:
- **Comunicación entre procesos (IPC)**: pipes, colas de mensajes, memoria compartida
- **Programación con threads/hilos**: ejecución concurrente dentro de un mismo proceso
- **Sincronización avanzada**: semáforos, mutex, variables de condición

Si tienes dudas específicas sobre los temas vistos o quieres explorar algún concepto en mayor profundidad, estoy aquí para ayudarte.