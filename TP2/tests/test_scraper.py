import asyncio
import json
import pathlib
import importlib.util
import importlib
import sys
import pytest
from aiohttp import web

# Helper para cargar un módulo desde un path (evita problemas de paquetes)
def load_module_from_path(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

@pytest.mark.asyncio
async def test_parse_html_basic_minimal():
    # Cargar html_parser desde TP2/scraper/html_parser.py
    base = pathlib.Path(__file__).resolve().parents[1]
    html_parser = load_module_from_path("html_parser", base / "scraper" / "html_parser.py")

    html = (
        "<html><head>"
        "<title>Hola</title>"
        "<meta name='description' content='desc'>"
        "</head><body>"
        "<h1>Hi</h1>"
        "<a href='/a'>link</a>"
        "<img src='i.png'/>"
        "</body></html>"
    )
    out = html_parser.parse_html_basic(html, base_url="https://example.com")
    assert out["title"] == "Hola"
    assert "https://example.com/a" in out["links"]
    assert out["meta_tags"].get("description") == "desc"
    assert out["structure"]["h1"] == 1
    assert out["images_count"] == 1

@pytest.mark.asyncio
async def test_parse_html_basic_empty():
    base = pathlib.Path(__file__).resolve().parents[1]
    html_parser = load_module_from_path("html_parser", base / "scraper" / "html_parser.py")
    out = html_parser.parse_html_basic("", base_url="")
    assert out["title"] == ""
    assert out["links"] == []
    assert out["meta_tags"] == {}
    assert out["images_count"] == 0
    for i in range(1, 7):
        assert out["structure"].get(f"h{i}") == 0

@pytest.mark.asyncio
async def test_handle_scrape_endpoint_success(aiohttp_client, monkeypatch):
    """
    Test del handler /scrape de server_scraping.py.
    - Añade el root del proyecto a sys.path para que 'scraper' sea importable.
    - Mockea scrape_worker para no depender de la red.
    - Mockea la comunicación con la Parte B (send_request_and_receive_json).
    - Verifica respuesta consolidada y códigos HTTP.
    """
    base = pathlib.Path(__file__).resolve().parents[1]

    # Asegurar que el directorio TP2 esté en sys.path para que 'scraper' y 'common' sean importables
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    # Importar el módulo normalmente (de este modo las importaciones relativas/absolutas dentro del módulo funcionan)
    server_mod = importlib.import_module("server_scraping")

    # Fake scrape_worker: devuelve scraping_data simple
    async def fake_scrape_worker(url, session, timeout):
        return {
            "title": "Fake",
            "links": ["https://example/"],
            "meta_tags": {"description": "x"},
            "structure": {f"h{i}": 0 for i in range(1, 7)},
            "images_count": 0,
        }

    # Fake processing server response
    async def fake_send_request_and_receive_json(host, port, payload):
        return {"processed": True, "note": "ok"}

    # Parchear en el módulo cargado
    monkeypatch.setattr(server_mod, "scrape_worker", fake_scrape_worker)
    monkeypatch.setattr(server_mod, "send_request_and_receive_json", fake_send_request_and_receive_json)

    # Crear app y cliente de pruebas
    app: web.Application = server_mod.create_app(process_host="127.0.0.1", process_port=9001, workers=2, timeout=5)
    client = await aiohttp_client(app)

    # Petición válida
    resp = await client.get("/scrape", params={"url": "https://example.com"})
    assert resp.status == 200
    data = await resp.json()
    assert data["scraping_data"]["title"] == "Fake"
    assert data["processing_data"]["processed"] is True
    assert data["status"] == "success"

    # Petición sin parámetro url -> 400
    resp2 = await client.get("/scrape")
    assert resp2.status == 400
    txt = await resp2.text()
    assert "missing url" in txt or "error" in txt.lower()