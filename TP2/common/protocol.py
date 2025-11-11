"""
Protocolo simple length-prefixed JSON para comunicación entre Servidor A y B.

Formato:
- 4 bytes big-endian (unsigned int) con la longitud del cuerpo en bytes
- cuerpo JSON UTF-8 de longitud indicada

Ventajas:
- Evita problemas de framing en TCP (stream-oriented).
- Es simple y suficiente para intercambio de mensajes JSON relativamente pequeños.

Notas importantes:
- Esta implementación usa asyncio.open_connection para conexión asíncrona.
- Siempre usar readexactly para asegurarse de recibir la cantidad esperada de bytes.
- Maneja timeouts con asyncio.wait_for / reader timeouts.
- En producción conviene añadir límites de tamaño y validación de payloads.
"""
import asyncio
import json
import struct
from typing import Any, Dict

# Estructura para pack/unpack de 4 bytes big-endian (unsigned int)
LEN_STRUCT = struct.Struct("!I")  # network (= big-endian) unsigned int


async def send_request_and_receive_json(host: str, port: int, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Abre una conexión TCP asíncrona a host:port, envía `payload` (serializado a JSON)
    con prefijo de longitud de 4 bytes, y espera una respuesta con el mismo formato.

    Parámetros:
    - host, port: destino (Servidor B)
    - payload: dict serializable a JSON
    - timeout: tiempo máximo (segundos) para la operación completa de lectura

    Retorna:
    - dict decodificado desde la respuesta JSON

    Excepciones:
    - Propaga excepciones de red/timeouts/JSON si ocurren.
    """
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    # Serializar el payload a bytes UTF-8
    data = json.dumps(payload).encode("utf-8")
    length = len(data)
    if length > 10 * 1024 * 1024:
        # Protección básica: rechazar mensajes > 10MB (ajustable)
        raise ValueError("payload too large")

    # Abrir conexión asíncrona (non-blocking)
    reader, writer = await asyncio.open_connection(host, port)
    try:
        # Escribir prefijo de longitud + cuerpo
        writer.write(LEN_STRUCT.pack(length))
        writer.write(data)
        await writer.drain()  # asegurar que los bytes se envían al socket

        # Leer la respuesta: primero 4 bytes con la longitud
        raw = await asyncio.wait_for(reader.readexactly(4), timeout=timeout)
        (resp_len,) = LEN_STRUCT.unpack(raw)

        # Protección: no leer más de un límite razonable
        if resp_len > 50 * 1024 * 1024:
            # evitar leer mensajes absurdamente grandes
            raise ValueError("response too large")

        # Leer exactamente resp_len bytes (bloquea de forma asíncrona hasta recibirlos)
        body = await asyncio.wait_for(reader.readexactly(resp_len), timeout=timeout)
        # Decodificar JSON y devolver dict
        return json.loads(body.decode("utf-8"))
    finally:
        # Cerrar writer correctamente (await writer.wait_closed() en Python 3.7+)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            # En shutdown / errores de red esto puede fallar; ignorar para no enmascarar el error original
            pass