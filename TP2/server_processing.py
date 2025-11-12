#!/usr/bin/env python3
"""
Servidor de Procesamiento (Parte B) - TP2
-----------------------------------------

Este servidor maneja solicitudes intensivas provenientes del Servidor A en procesos separados.

Funciones:
- Captura de screenshots
- Análisis de rendimiento
- Procesamiento de imágenes

Utiliza:
- Multiprocessing para alto rendimiento
- Socketserver para comunicación

"""

import multiprocessing
import socketserver
import json
import struct
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import process_images

# Tamaño de encabezado para el protocolo (4 bytes para longitud del mensaje)
LEN_STRUCT = struct.Struct("!I")


def handle_request(request_data):
    """
    Dispatcher para manejar el tipo de tarea (screenshot, performance, images).

    :param request_data: Diccionario con los datos del cliente
    :return: Resultado del procesamiento
    """
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
    """
    Clase que maneja las solicitudes socket recibidas.
    """
    def handle(self):
        try:
            # Leer encabezado (4 bytes para longitud)
            raw_length = self.request.recv(4)
            if not raw_length:
                return
            (length,) = LEN_STRUCT.unpack(raw_length)

            # Leer cuerpo del mensaje, que es JSON
            raw_body = self.request.recv(length)
            data = json.loads(raw_body.decode("utf-8"))

            # Procesar solicitud en un proceso separado
            with multiprocessing.Pool(processes=1) as pool:
                result = pool.apply(handle_request, (data,))

            # Responder con los resultados como JSON
            response = json.dumps(result).encode("utf-8")
            self.request.sendall(LEN_STRUCT.pack(len(response)))
            self.request.sendall(response)
        except Exception as e:
            # Enviar error al cliente
            error_response = json.dumps({"error": str(e)}).encode("utf-8")
            self.request.sendall(LEN_STRUCT.pack(len(error_response)))
            self.request.sendall(error_response)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Servidor de procesamiento (Parte B)")
    parser.add_argument("-i", "--ip", type=str, required=True, help="Dirección IP del servidor")
    parser.add_argument("-p", "--port", type=int, required=True, help="Puerto del servidor")
    parser.add_argument(
        "-n", "--processes", type=int, default=multiprocessing.cpu_count(), help="Número de procesos en pool"
    )
    args = parser.parse_args()

    # Servidor multithread
    with socketserver.ThreadingTCPServer((args.ip, args.port), RequestHandler) as server:
        print(f"Servidor de procesamiento escuchando en {args.ip}:{args.port}...")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nApagando el servidor...")


if __name__ == "__main__":
    main()