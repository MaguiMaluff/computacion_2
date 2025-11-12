#!/usr/bin/env python3
"""
Servidor de Procesamiento (Parte B) - TP2
-----------------------------------------

Mejoras a la interfaz:
- Validación de argumentos (IP, puerto).
- Modo verbose/debug.
- Tolerancia a errores comunes durante la inicialización.

Ejecución:
    python3 server_processing.py -i 127.0.0.1 -p 9001

"""

import multiprocessing
import socketserver
import json
import struct
import socket
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import process_images

LEN_STRUCT = struct.Struct("!I")


def handle_request(request_data):
    task = request_data.get("task")
    if task == "screenshot":
        return generate_screenshot(request_data)
    elif task == "performance":
        return analyze_performance(request_data)
    elif task == "images":
        return process_images(request_data)
    else:
        return {"error": f"Tarea desconocida: {task}"}


class RequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            raw_length = self.request.recv(4)
            if not raw_length:
                return
            (length,) = LEN_STRUCT.unpack(raw_length)

            raw_body = self.request.recv(length)
            data = json.loads(raw_body.decode("utf-8"))

            with multiprocessing.Pool(processes=1) as pool:
                result = pool.apply(handle_request, (data,))

            response = json.dumps(result).encode("utf-8")
            self.request.sendall(LEN_STRUCT.pack(len(response)))
            self.request.sendall(response)
        except Exception as e:
            error_response = json.dumps({"error": str(e)}).encode("utf-8")
            self.request.sendall(LEN_STRUCT.pack(len(error_response)))
            self.request.sendall(error_response)


def validate_port(port):
    """
    Verifica si el puerto está disponible.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("localhost", port)) == 0:
            raise ValueError(f"El puerto {port} ya está en uso. Intente otro.")


def validate_ip(ip):
    """
    Verifica si la dirección IP es válida.
    """
    try:
        socket.inet_aton(ip)
    except socket.error:
        raise ValueError(f"La IP '{ip}' no es válida.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Servidor de procesamiento (Parte B)")
    parser.add_argument("-i", "--ip", type=str, required=True, help="Dirección IP del servidor")
    parser.add_argument("-p", "--port", type=int, required=True, help="Puerto del servidor")
    parser.add_argument("-n", "--processes", type=int, default=multiprocessing.cpu_count(), help="Número de procesos en pool")
    parser.add_argument("-v", "--verbose", action="store_true", help="Habilita el modo verbose para depuración")
    args = parser.parse_args()

    # Validar dirección IP
    try:
        validate_ip(args.ip)
        validate_port(args.port)
    except ValueError as e:
        print(f"Error de validación: {e}")
        return

    # Modo verbose
    if args.verbose:
        print(f"Iniciando el servidor de procesamiento con {args.processes} procesos...")
        print(f"Escuchando en {args.ip}:{args.port}")

    # Inicializar el servidor TCP
    try:
        with socketserver.ThreadingTCPServer((args.ip, args.port), RequestHandler) as server:
            print(f"Servidor de procesamiento escuchando en {args.ip}:{args.port}...")
            server.serve_forever()
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
    except KeyboardInterrupt:
        print("\nApagando el servidor...")


if __name__ == "__main__":
    main()