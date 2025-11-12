#!/usr/bin/env python3
"""
Servidor de Scraping Web Asíncrono (Parte A)

Uso:
  python3 server_scraping.py -i 0.0.0.0 -p 8000 -w 8 --process-host localhost --process-port 9001

Este archivo expone un servidor HTTP (aiohttp) que:
- recibe una URL por query param (?url=...)
- realiza el scraping asíncrono de la página (usando una ClientSession compartida)
- extrae datos básicos (título, enlaces, meta, headers, count imágenes)
- envía los datos al servidor de procesamiento (Parte B) mediante un protocolo
  length-prefixed JSON (función send_request_and_receive_json)
- espera la respuesta de B de forma asíncrona y devuelve un JSON consolidado al cliente
"""
import argparse            # parsing de línea de comandos
import asyncio             # primitives de concurrencia (event loop, Semaphore, etc.)
import json                # serializar / deserializar payloads JSON
import struct
from datetime import datetime
import os
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import socket
import ssl
import asyncio
import math

import aiohttp             # cliente HTTP asíncrono y utilidades
from aiohttp import web    # framework web asíncrono (handlers, respuestas)
from bs4 import BeautifulSoup

# funciones locales modulares: parsing HTML y protocolo de comunicación con B
from scraper.html_parser import parse_html_basic
from common.protocol import send_request_and_receive_json

# valores por defecto configurables
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT = 30  # segundos. Limita cuánto esperamos por una página

PROCESSOR_HOST = os.environ.get("PROC_HOST", "127.0.0.1")
PROCESSOR_PORT = int(os.environ.get("PROC_PORT", "9001"))

# Nuevo: valores por defecto del conector y configuración de reintentos
CONNECTOR_LIMIT = int(os.environ.get("AIO_LIMIT", "100"))
CONNECTOR_LIMIT_PER_HOST = int(os.environ.get("AIO_LIMIT_PER_HOST", "10"))
ASK_RETRIES = int(os.environ.get("ASK_RETRIES", "3"))
ASK_BACKOFF_BASE = float(os.environ.get("ASK_BACKOFF_BASE", "0.5"))


async def fetch_html(session, url):
    timeout = aiohttp.ClientTimeout(total=30)
    async with session.get(url, timeout=timeout) as resp:
        text = await resp.text(errors="ignore")
        return text


def extract_data(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        links.append(urljoin(base_url, href))
    meta = {}
    for m in soup.find_all("meta"):
        if m.get("name"):
            meta[m.get("name")] = m.get("content", "")
        if m.get("property"):
            meta[m.get("property")] = m.get("content", "")
    headers = {}
    for i in range(1, 7):
        headers[f"h{i}"] = len(soup.find_all(f"h{i}"))
    images_count = len(soup.find_all("img"))
    return {
        "title": title,
        "links": links,
        "meta_tags": meta,
        "structure": headers,
        "images_count": images_count,
    }


async def ask_processor(host, port, payload):
    # Bucle de reintentos con backoff exponencial y manejo amplio de excepciones
    last_exc = None
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(1, ASK_RETRIES + 1):
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(struct.pack(">I", len(data)) + data)
            await writer.drain()
            raw_len = await reader.readexactly(4)
            msg_len = struct.unpack(">I", raw_len)[0]
            data_in = await reader.readexactly(msg_len)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return json.loads(data_in.decode("utf-8"))
        except (asyncio.IncompleteReadError, ConnectionRefusedError, OSError, asyncio.TimeoutError,
                socket.gaierror, ssl.SSLError, asyncio.CancelledError) as e:
            last_exc = e
            # backoff (no dormir si fue cancelado)
            if isinstance(e, asyncio.CancelledError):
                raise
            await asyncio.sleep(ASK_BACKOFF_BASE * (2 ** (attempt - 1)))
            continue
    raise last_exc


# Handler HTTP para el endpoint /scrape
async def handle_scrape(request: web.Request) -> web.Response:
    """
    Handler que:
    - valida parámetros de la request (url)
    - limita concurrencia con un Semaphore almacenado en app["sem"]
    - invoca scrape_worker para obtener scraping_data
    - comunica el resultado a la Parte B mediante send_request_and_receive_json
    - consolida la respuesta (scraping + processing) y la devuelve como JSON
    """
    # obtener parámetros query (?url=...)
    params = request.rel_url.query
    url = params.get("url")
    if not url:
        # Falta parámetro obligatorio: respondemos 400 con JSON explicativo
        raise web.HTTPBadRequest(
            text=json.dumps({"error": "missing url parameter"}),
            content_type="application/json",
        )

    # Accedemos al estado compartido de la app
    app = request.app
    sem: asyncio.Semaphore = app["sem"]  # controla número concurrente de scrapers
    session: aiohttp.ClientSession = app["http_session"]  # session compartida (pool de conexiones)
    timeout = app["timeout"]  # timeout configurado
    process_host = app["process_host"]  # host del Servidor B
    process_port = app["process_port"]  # puerto del Servidor B

    # `async with sem` limita cuantas coroutines pueden ejecutar scraping simultáneamente.
    async with sem:
        try:
            # Ejecutamos la tarea de scraping. Es awaitable y no bloquea el loop.
            scraping_data = await scrape_worker(url, session, timeout)
        except web.HTTPException as e:
            # Propagamos excepciones HTTP lanzadas por scrape_worker (p. ej. 400 en fetch_error)
            return e
        except Exception as e:
            # Errores inesperados: devolvemos 500 con detalle mínimo.
            return web.json_response({"url": url, "status": "failed", "error": str(e)}, status=500)

        # Preparamos el payload que mandaremos al Servidor B para procesamiento adicional.
        payload = {
            "url": url,
            "scraping_data": scraping_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        processing_data: Optional[Dict[str, Any]] = None
        try:
            # send_request_and_receive_json abre una conexión TCP asíncrona (asyncio.open_connection),
            # envía JSON con prefijo de longitud (4 bytes big-endian) y espera la respuesta con el mismo formato.
            processing_data = await send_request_and_receive_json(process_host, process_port, payload)
        except Exception as e:
            # Si la comunicación con B falla (timeout, conexión rechazada, datos inválidos, etc.),
            # devolvemos scraping_data y un processing_data con la info del error.
            processing_data = {"error": f"processing_server_error: {str(e)}"}

        # Consolidamos la respuesta final para el cliente
        response = {
            "url": url,
            "timestamp": payload["timestamp"],
            "scraping_data": scraping_data,
            "processing_data": processing_data,
            "status": "success" if not processing_data.get("error") else "partial_failure",
        }
        # web.json_response serializa a JSON, añade header Content-Type y devuelve una Response.
        return web.json_response(response)


# Factory que crea la aplicación aiohttp y gestiona recursos
def create_app(
    process_host: str = "127.0.0.1",
    process_port: int = 9001,
    workers: int = DEFAULT_WORKERS,
    timeout: int = DEFAULT_TIMEOUT,
) -> web.Application:
    """
    Crea y configura la aiohttp.web.Application.
    """
    app = web.Application()

    # Registrar ruta /scrape
    app.add_routes([web.get("/scrape", handle_scrape)])

    # Estado compartido accesible desde handlers vía request.app
    app["sem"] = asyncio.Semaphore(workers)  # controla concurrencia
    app["timeout"] = timeout
    app["process_host"] = process_host
    app["process_port"] = process_port

    # Hooks de ciclo de vida: on_startup y on_cleanup son coroutines ejecutadas por aiohttp
    # on_startup corre cuando web.run_app inicia el servidor (ya hay un event loop en ejecución)
    async def on_startup(app: web.Application):
        # Crear ClientSession DENTRO del event loop activo.
        # ClientSession crea recursos asíncronos ligados al loop.
        app["http_session"] = aiohttp.ClientSession()

    async def on_cleanup(app: web.Application):
        # Cerrar la ClientSession al apagar la app para liberar sockets y recursos.
        session = app.get("http_session")
        if session:
            await session.close()

    # Registrar los hooks en la app para que aiohttp los invoque automáticamente
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def parse_args():
    p = argparse.ArgumentParser(description="Servidor de Scraping Web Asíncrono")
    p.add_argument("-i", "--ip", required=True, help="Dirección de escucha (IPv4/IPv6)")
    p.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    p.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Número de workers (default: 4)")
    p.add_argument("--process-host", default="127.0.0.1", help="Host del servidor de procesamiento (Parte B)")
    p.add_argument("--process-port", default=9001, type=int, help="Puerto del servidor de procesamiento (Parte B)")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout de scraping en segundos (default: 30)")
    return p.parse_args()


# Entrypoint: construir la app y arrancarla
def main():
    # Obtener parámetros CLI
    args = parse_args()
    # Crear la app con la configuración deseada
    app = create_app(
        process_host=args.process_host,
        process_port=args.process_port,
        workers=args.workers,
        timeout=args.timeout,
    )
    # web.run_app:
    # - crea y administra el event loop
    web.run_app(app, host=args.ip, port=args.port)


# A continuación está la implementación consolidada de `scrape_worker`.
async def scrape_worker(url: str, session: aiohttp.ClientSession, timeout: int) -> Dict[str, Any]:
    """
    Realiza un GET asíncrono a `url` y usa parse_html_basic para extraer scraping_data.
    Mapea errores de red a excepciones HTTP precisas (400, 502, 504) que aiohttp
    interpretará y enviará al cliente como respuestas con JSON.
    """
    try:
        # Abrimos la petición usando la session compartida y aplicamos timeout global.
        # El `async with` garantiza que la respuesta se cierre/retorne al pool.
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            # Levanta ClientResponseError si el status es 4xx/5xx
            resp.raise_for_status()

            if resp.content_length and resp.content_length > 5 * 1024 * 1024:  # > 5 MB
                raise web.HTTPRequestEntityTooLarge(
                    text=json.dumps(
                        {"error": f"El contenido es demasiado grande ({resp.content_length} bytes)"}
                    ),
                    content_type="application/json",
                )

            # Leer el cuerpo de forma asíncrona (no bloqueante).
            html = await resp.text()

    # Mapeos de excepciones frecuentes a respuestas HTTP con JSON explicativo:
    except asyncio.TimeoutError:
        # Timeout de la operación de red
        raise web.HTTPGatewayTimeout(
            text=json.dumps({"error": "Timeout mientras se conectaba al servidor"}),
            content_type="application/json",
        )
    except aiohttp.ClientConnectorError as e:
        # Error al conectar (host inaccesible / conexión rechazada)
        raise web.HTTPBadGateway(
            text=json.dumps({"error": f"Conexión rechazada o fallida: {str(e)}"}),
            content_type="application/json",
        )
    except aiohttp.ClientResponseError as e:
        # El servidor remoto devolvió un status 4xx/5xx
        status = e.status
        raise web.HTTPBadRequest(
            text=json.dumps({"error": f"Error HTTP recibido del servidor: {status}"}),
            content_type="application/json",
        )
    except Exception as e:
        # Cualquier otro error se mapea a 400 con mensaje minimalista
        raise web.HTTPBadRequest(
            text=json.dumps({"error": f"Fallo inesperado: {str(e)}"}),
            content_type="application/json",
        )

    # Si llegamos acá, tenemos el HTML; parse_html_basic extrae título, links, meta, headers, count imágenes.
    # Usamos str(resp.url) para resolver URLs relativas y reflejar redirecciones.
    scraping_data = parse_html_basic(html, base_url=str(resp.url))
    return scraping_data


if __name__ == "__main__":
    main()