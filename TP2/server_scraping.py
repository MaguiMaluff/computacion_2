#!/usr/bin/env python3
"""
Servidor de Scraping Web Asíncrono (Parte A)

Uso:
  python3 TP2/server_scraping.py -i 0.0.0.0 -p 8000 -w 8 --process-host localhost --process-port 9001

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
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp             # cliente HTTP asíncrono y utilidades
from aiohttp import web    # framework web asíncrono (handlers, respuestas)

# funciones locales modulares: parsing HTML y protocolo de comunicación con B
from scraper.html_parser import parse_html_basic
from common.protocol import send_request_and_receive_json

# valores por defecto configurables
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT = 30  # segundos. Limita cuánto esperamos por una página

# Función que realiza la petición HTTP y parsea el HTML
async def scrape_worker(url: str, session: aiohttp.ClientSession, timeout: int) -> Dict[str, Any]:
    """
    Realiza un GET asíncrono a `url` usando la ClientSession compartida `session`.
    - Usa `async with` para asegurar liberación correcta del objeto Response.
    - Aplica un timeout (ClientTimeout) para evitar bloquear el event loop indefinidamente.
    - Valida el status con resp.raise_for_status() (lanza excepción si 4xx/5xx).
    - Lee el cuerpo con await resp.text() (operación I/O no bloqueante).
    - Pasa el HTML a parse_html_basic para obtener el diccionario de scraping.
    - En caso de errores de fetch/parsing lanza una excepción HTTP (400) con JSON.
    """
    try:
        # `async with session.get(...) as resp`:
        # - mantiene la conexión en el pool mientras se trabaja con la respuesta
        # - garantiza que la conexión se cierra / retorna al pool aun en caso de excepción
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            # Si el servidor respondió 4xx/5xx, raise_for_status lanza ClientResponseError
            resp.raise_for_status()
            # Leer el cuerpo de forma asíncrona; permite que el event loop atienda otras tareas
            html = await resp.text()
    except Exception as e:
        # Capturamos cualquier excepción de la fase de fetch/lectura y la mapeamos
        # a una excepción HTTP comprensible por el cliente (aquí usamos 400).
        raise web.HTTPBadRequest(
            text=json.dumps({"error": f"fetch_error: {str(e)}"}),
            content_type='application/json'
        )

    # parse_html_basic realiza extracción de título, links, meta tags, headers y cantidad de imágenes
    # Le pasamos base_url=str(resp.url) para resolver links relativos (y para respetar redirecciones).
    scraping_data = parse_html_basic(html, base_url=str(resp.url))
    return scraping_data


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
            content_type='application/json'
        )

    # Accedemos al estado compartido de la app
    app = request.app
    sem: asyncio.Semaphore = app["sem"]                 # controla número concurrente de scrapers
    session: aiohttp.ClientSession = app["http_session"]  # session compartida (pool de conexiones)
    timeout = app["timeout"]                            # timeout configurado
    process_host = app["process_host"]                  # host del Servidor B
    process_port = app["process_port"]                  # puerto del Servidor B

    # `async with sem` limita cuantas coroutines pueden ejecutar scraping simultáneamente.
    # Esto protege recursos locales (file descriptors, ancho de banda) y evita saturar destinos.
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
            "timestamp": datetime.utcnow().isoformat() + "Z"
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
            "status": "success" if not processing_data.get("error") else "partial_failure"
        }
        # web.json_response serializa a JSON, añade header Content-Type y devuelve una Response.
        return web.json_response(response)


# Factory que crea la aplicación aiohttp y gestiona recursos
def create_app(
    process_host: str = "127.0.0.1",
    process_port: int = 9001,
    workers: int = DEFAULT_WORKERS,
    timeout: int = DEFAULT_TIMEOUT
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
        timeout=args.timeout
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
                    text=json.dumps({
                        "error": f"El contenido es demasiado grande ({resp.content_length} bytes)"
                    }),
                    content_type='application/json'
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