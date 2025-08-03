# Ejercicio 1: Eco Simple
import os
import sys

def eco_simple():
    r1, w1 = os.pipe()  # padre -> hijo
    r2, w2 = os.pipe()  # hijo -> padre

    pid = os.fork()
    if pid == 0:
        os.close(w1)
        os.close(r2)
        r = os.fdopen(r1, 'r')
        w = os.fdopen(w2, 'w')
        mensaje = r.readline().strip()
        w.write(mensaje + '\n')
        w.flush()
        r.close()
        w.close()
        sys.exit(0)
    else:
        os.close(r1)
        os.close(w2)
        w = os.fdopen(w1, 'w')
        r = os.fdopen(r2, 'r')
        w.write("Hola, hijo!\n")
        w.flush()
        respuesta = r.readline().strip()
        print("Padre recibe:", respuesta)
        w.close()
        r.close()
        os.waitpid(pid, 0)

# Ejercicio 2: Contador de Palabras
import time

def contador_palabras(archivo):
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()
    
    pid = os.fork()
    if pid == 0:
        os.close(w1)
        os.close(r2)
        r = os.fdopen(r1, 'r')
        w = os.fdopen(w2, 'w')
        for linea in r:
            cantidad = len(linea.strip().split())
            w.write(f"{cantidad}\n")
            w.flush()
        r.close()
        w.close()
        sys.exit(0)
    else:
        os.close(r1)
        os.close(w2)
        w = os.fdopen(w1, 'w')
        r = os.fdopen(r2, 'r')
        with open(archivo, 'r') as f:
            for linea in f:
                w.write(linea)
                w.flush()
        w.close()
        for resultado in r:
            print("Palabras en línea:", resultado.strip())
        r.close()
        os.waitpid(pid, 0)

# Ejercicio 3: Pipeline de Filtrado
import random

def pipeline_filtrado():
    p1r, p1w = os.pipe()
    p2r, p2w = os.pipe()

    pid1 = os.fork()
    if pid1 == 0:
        os.close(p1r)
        os.close(p2r)
        os.close(p2w)
        w = os.fdopen(p1w, 'w')
        for _ in range(10):
            num = random.randint(1, 100)
            print("Generado:", num)
            w.write(f"{num}\n")
            w.flush()
            time.sleep(0.2)
        w.close()
        sys.exit(0)

    pid2 = os.fork()
    if pid2 == 0:
        os.close(p1w)
        os.close(p2r)
        r = os.fdopen(p1r, 'r')
        w = os.fdopen(p2w, 'w')
        for linea in r:
            num = int(linea.strip())
            if num % 2 == 0:
                print("Filtrado par:", num)
                w.write(f"{num}\n")
                w.flush()
        r.close()
        w.close()
        sys.exit(0)

    os.close(p1r)
    os.close(p1w)
    os.close(p2w)
    r = os.fdopen(p2r, 'r')
    for linea in r:
        num = int(linea.strip())
        print("Cuadrado:", num * num)
    r.close()
    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)

# Ejercicio 4: Simulador de Shell
import subprocess

def simulador_shell(cmd1, cmd2):
    p1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()[0]
    print(output.decode())

# Ejercicio 5: Chat Bidireccional
import threading

def chat_bidireccional():
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()

    pid = os.fork()
    if pid == 0:
        os.close(w1)
        os.close(r2)
        r = os.fdopen(r1, 'r')
        w = os.fdopen(w2, 'w')

        def recibir():
            for linea in r:
                print("[PADRE]:", linea.strip())

        threading.Thread(target=recibir, daemon=True).start()
        while True:
            msg = input("[HIJO]> ")
            if msg == "salir": break
            w.write(msg + '\n')
            w.flush()
        r.close()
        w.close()
        sys.exit(0)
    else:
        os.close(r1)
        os.close(w2)
        r = os.fdopen(r2, 'r')
        w = os.fdopen(w1, 'w')

        def recibir():
            for linea in r:
                print("[HIJO]:", linea.strip())

        threading.Thread(target=recibir, daemon=True).start()
        while True:
            msg = input("[PADRE]> ")
            if msg == "salir": break
            w.write(msg + '\n')
            w.flush()
        r.close()
        w.close()
        os.waitpid(pid, 0)

# Ejercicio 6: Servidor de Operaciones Matemáticas
def servidor_operaciones():
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()

    pid = os.fork()
    if pid == 0:
        os.close(w1)
        os.close(r2)
        r = os.fdopen(r1, 'r')
        w = os.fdopen(w2, 'w')
        for linea in r:
            operacion = linea.strip()
            try:
                resultado = str(eval(operacion, {}, {}))
            except:
                resultado = "ERROR"
            w.write(resultado + '\n')
            w.flush()
        r.close()
        w.close()
        sys.exit(0)
    else:
        os.close(r1)
        os.close(w2)
        w = os.fdopen(w1, 'w')
        r = os.fdopen(r2, 'r')
        operaciones = ["5 + 3", "10 * 2", "7 / 0", "15 - 4"]
        for op in operaciones:
            w.write(op + '\n')
            w.flush()
            print("Resultado:", r.readline().strip())
        w.close()
        r.close()
        os.waitpid(pid, 0)

# Ejercicio 7: Sistema de Procesamiento de Transacciones
def sistema_transacciones():
    p1r, p1w = os.pipe()
    p2r, p2w = os.pipe()

    pid_validador = os.fork()
    if pid_validador == 0:
        os.close(p1w)
        os.close(p2r)
        r = os.fdopen(p1r, 'r')
        w = os.fdopen(p2w, 'w')
        for linea in r:
            partes = linea.strip().split(',')
            if len(partes) == 3:
                w.write(linea)
                w.flush()
        r.close()
        w.close()
        sys.exit(0)

    pid_registrador = os.fork()
    if pid_registrador == 0:
        os.close(p1r)
        os.close(p1w)
        os.close(p2w)
        r = os.fdopen(p2r, 'r')
        total = 0
        for linea in r:
            _, _, monto = linea.strip().split(',')
            total += float(monto)
        r.close()
        print("Monto total procesado:", total)
        sys.exit(0)

    os.close(p1r)
    os.close(p2r)
    os.close(p2w)
    w = os.fdopen(p1w, 'w')
    transacciones = ["1,COMPRA,100.50", "2,VENTA,50.00", "3,COMPRA,25.00"]
    for t in transacciones:
        w.write(t + '\n')
        w.flush()
    w.close()
    os.waitpid(pid_validador, 0)
    os.waitpid(pid_registrador, 0)


# eco_simple()
# contador_palabras('archivo.txt')
# pipeline_filtrado()
# simulador_shell('ls', 'wc -l')
# chat_bidireccional()
# servidor_operaciones()
# sistema_transacciones()
