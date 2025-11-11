"""
Helpers para uso de aiohttp ClientSession en el scraper.

Contiene:
- make_session: crea una ClientSession con un TCPConnector configurado (limits, ssl)
- fetch_text: wrapper para obtener texto de una URL con manejo básico de errores/timeouts

La idea es encapsular la configuración del pool de conexiones y la política
de timeouts en un único lugar, para reusar y cambiar parámetros fácilmente.
"""
from typing import Tuple, Optional
import aiohttp
import asyncio

# Valores por defecto
DEFAULT_LIMIT = 100          # max conexiones totales en el pool
DEFAULT_LIMIT_PER_HOST = 10  # max conexiones simultáneas por host


def make_session(limit: int = DEFAULT_LIMIT, limit_per_host: int = DEFAULT_LIMIT_PER_HOST, headers: dict | None = None) -> aiohttp.ClientSession:
    """
    Crea y devuelve una aiohttp.ClientSession con un connector configurado.
    - limit: número máximo de conexiones totales
    - limit_per_host: número máximo de conexiones por host
    - headers: headers por defecto
    """
    connector = aiohttp.TCPConnector(limit=limit, limit_per_host=limit_per_host)
    session = aiohttp.ClientSession(connector=connector, headers=headers)
    return session


async def fetch_text(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[Optional[str], int, str]:
    """
    Hace un GET asíncrono y devuelve (text_or_none, status, final_url).

    - Si ocurre un error controlado (timeout, conexión, invalid URL), devuelve (None, status_estimate, error_msg)
    """
    try:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        async with session.get(url, timeout=timeout_cfg) as resp:
            resp.raise_for_status()  # lanza ClientResponseError si status >=400
            text = await resp.text()
            return text, resp.status, str(resp.url)
    except asyncio.TimeoutError as e:
        # Timeout: devolver None y un status simbólico (504)
        return None, 504, f"timeout: {e}"
    except aiohttp.ClientResponseError as e:
        # Respuesta con status 4xx/5xx
        return None, e.status, f"response_error: {e}"
    except aiohttp.InvalidURL as e:
        return None, 400, f"invalid_url: {e}"
    except Exception as e:
        # Errores de conexión, DNS, etc.
        return None, 502, f"connection_error: {e}"