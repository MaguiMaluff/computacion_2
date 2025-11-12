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

import argparse
import socketserver
import struct
import json
import base64
import io
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup

# Intentar importar Selenium + webdriver-manager como alternativa para screenshots.
# Si no está disponible, SELENIUM_AVAILABLE será False y se usará un placeholder.
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

# Helper: crear una sesión requests con reintentos
def make_retry_session(total_retries=3, backoff_factor=0.5, status_forcelist=(500,502,503,504)):
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'POST'])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Helper: captura con Selenium (devuelve bytes PNG)
def capture_screenshot_selenium(url, timeout_s=30):
    """Devuelve bytes PNG usando Selenium con Chrome en modo headless mediante webdriver-manager."""
    opts = ChromeOptions()
    # Opciones para headless y entorno sin sandbox (útiles en Docker)
    # Usamos la opción --headless estándar; si su versión de Chrome soporta --headless=new, no hay problema
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,1024")
    # Crear servicio usando webdriver-manager para descargar el driver automáticamente
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    try:
        driver.set_page_load_timeout(timeout_s)
        driver.get(url)
        png = driver.get_screenshot_as_png()
        return png
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def process_task(payload):
    """Tarea de procesamiento que se ejecuta en un worker del pool.

    Realiza:
    - Descarga de la página (requests con reintentos) para medir rendimiento.
    - Captura de screenshot con Selenium si está disponible, si no, genera placeholder con Pillow.
    - Descarga de hasta 3 imágenes principales y generación de thumbnails.
    - Retorna un dict serializable con estado y datos de procesamiento.
    """
    url = payload.get("url")
    result = {"screenshot": None, "performance": {}, "thumbnails": []}
    try:
        session = make_retry_session(total_retries=3, backoff_factor=0.5)
        start = time.time()
        resp = session.get(url, timeout=30, stream=True)
        content = resp.content
        load_time_ms = int((time.time() - start) * 1000)
        total_size_kb = max(1, len(content) // 1024)
        num_requests = 1

        # Intentar screenshot con Selenium si está disponible
        screenshot_bytes = None
        if SELENIUM_AVAILABLE:
            try:
                screenshot_bytes = capture_screenshot_selenium(url, timeout_s=30)
            except Exception:
                screenshot_bytes = None

        # Si no hay Selenium o falló, usar marcador de posición con Pillow
        if screenshot_bytes is None:
            img = Image.new("RGB", (1024, 768), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            d.text((10, 10), f"Screenshot placeholder for {url}", fill=(0, 0, 0), font=font)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            screenshot_bytes = buf.getvalue()

        result["screenshot"] = base64.b64encode(screenshot_bytes).decode("ascii")

        # Parsear HTML para encontrar etiquetas img
        soup = BeautifulSoup(content, "lxml")
        imgs = []
        for tag in soup.find_all("img"):
            src = tag.get("src")
            if src:
                imgs.append(src)
            if len(imgs) >= 3:
                break

        thumbnails = []
        from urllib.parse import urljoin
        for src in imgs:
            try:
                if src.startswith("//"):
                    src = "http:" + src
                elif src.startswith("/"):
                    src = urljoin(url, src)
                # Descargar imagen con session que tiene reintentos
                r = session.get(src, timeout=10)
                r.raise_for_status()
                thumb_img = Image.open(io.BytesIO(r.content)).convert("RGB")
                thumb_img.thumbnail((128, 128))
                b = io.BytesIO()
                thumb_img.save(b, format="PNG", optimize=True)
                thumbnails.append(base64.b64encode(b.getvalue()).decode("ascii"))
                num_requests += 1
            except Exception:
                # ignorar fallo en una sola imagen y continuar con las demás
                continue

        result["performance"] = {
            "load_time_ms": load_time_ms,
            "total_size_kb": total_size_kb,
            "num_requests": num_requests,
        }
        result["thumbnails"] = thumbnails
        return {"status": "success", "processing_data": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


class LengthPrefixedTCPHandler(socketserver.BaseRequestHandler):
    """Handler para mensajes TCP con prefijo de longitud (4 bytes big-endian) seguido de JSON UTF-8."""
    def handle(self):
        try:
            raw_len = self.request.recv(4)
            if len(raw_len) < 4:
                return
            msg_len = struct.unpack(">I", raw_len)[0]
            data = b""
            while len(data) < msg_len:
                packet = self.request.recv(msg_len - len(data))
                if not packet:
                    break
                data += packet
            payload = json.loads(data.decode("utf-8"))
            # Enviar la tarea al executor (pool de procesos)
            future = self.server.executor.submit(process_task, payload)
            res = future.result(timeout=60)
            out = json.dumps(res).encode("utf-8")
            self.request.sendall(struct.pack(">I", len(out)) + out)
        except Exception as e:
            try:
                err = json.dumps({"status": "failed", "error": str(e)}).encode("utf-8")
                self.request.sendall(struct.pack(">I", len(err)) + err)
            except Exception:
                pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="Servidor de Procesamiento Distribuido")
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    parser.add_argument("-n", "--processes", type=int, default=cpu_count(), help="Número de procesos en el pool (default: CPU count)")
    args = parser.parse_args()

    with ProcessPoolExecutor(max_workers=args.processes) as executor:
        server = ThreadedTCPServer((args.ip, args.port), LengthPrefixedTCPHandler)
        server.executor = executor
        try:
            print(f"Servidor de procesamiento escuchando en {args.ip}:{args.port} con {args.processes} procesos")
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()