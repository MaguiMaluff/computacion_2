# TP2 - Sistema de Scraping y Análisis Web Distribuido

Este proyecto implementa un sistema distribuido de scraping y análisis web utilizando Python. El sistema está dividido en dos servidores que trabajan de forma coordinada para extraer, analizar y procesar información de sitios web, cumpliendo los requisitos del trabajo práctico TP2 de Computación II.

## Estructura del Proyecto

```
TP2/
├── server_scraping.py          # Servidor asyncio (Parte A)
├── server_processing.py        # Servidor multiprocessing (Parte B)
├── client.py                   # Cliente de prueba
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py          # Funciones de parsing HTML
│   ├── metadata_extractor.py   # Extracción de metadatos
│   └── async_http.py           # Cliente HTTP asíncrono
├── processor/
│   ├── __init__.py
│   ├── screenshot.py           # Generación de screenshots
│   ├── performance.py          # Análisis de rendimiento
│   └── image_processor.py      # Procesamiento de imágenes
├── common/
│   ├── __init__.py
│   ├── protocol.py             # Protocolo de comunicación
│   └── serialization.py        # Serialización de datos
├── tests/
│   ├── test_scraper.py
│   └── test_processor.py
├── requirements.txt
└── README.md
```

## Instalación y Dependencias

Requiere Python >=3.9.

Instala todas las dependencias principales:

```bash
pip install -r requirements.txt
```

## Ejecución

### Parte A: Servidor de Scraping Asíncrono (server_scraping.py)

```bash
python3 TP2/server_scraping.py -i 0.0.0.0 -p 8000 -w 4 --process-host localhost --process-port 9001
```

Opciones:
- `-i IP, --ip IP`: Dirección de escucha (soporta IPv4/IPv6)
- `-p PORT, --port PORT`: Puerto de escucha
- `-w WORKERS, --workers WORKERS`: Número de workers para scraping asíncrono
- `--process-host HOST`: IP servidor de procesamiento (default: localhost)
- `--process-port PORT`: Puerto servidor de procesamiento (default: 9001)

### Parte B: Servidor de Procesamiento Multiproceso (server_processing.py)

```bash
python3 TP2/server_processing.py -i 127.0.0.1 -p 9001 -n 4
```

Opciones:
- `-i IP, --ip IP`: Dirección de escucha
- `-p PORT, --port PORT`: Puerto de escucha
- `-n PROCESSES, --processes PROCESSES`: Número de procesos en el pool (default: cantidad de CPUs)

### Cliente de Prueba (client.py)

Haz una prueba simple con:

```bash
python3 TP2/client.py --server http://127.0.0.1:8000 --url https://example.com
```

Esto devuelve una respuesta JSON con los resultados consolidados del scrape y procesamiento.

## Formato de Respuesta

El servidor responde con un JSON consolidado como:
```json
{
  "url": "https://ejemplo.com",
  "timestamp": "2025-11-12T15:46:33Z",
  "scraping_data": {
    "title": "Título de la página",
    "links": ["url1", "url2", ...],
    "meta_tags": { "description": "...", "keywords": "...", "og:title": "..." },
    "structure": { "h1": 2, "h2": 5, "h3": 10 },
    "images_count": 15
  },
  "processing_data": {
    "screenshot": "base64_encoded_image",
    "performance": { "load_time_ms": 1250, "total_size_kb": 2048, "num_requests": 45 },
    "thumbnails": ["base64_thumb1", "base64_thumb2"]
  },
  "status": "success"
}
```

## Testing

Se incluyen tests automáticos en la carpeta `tests/`.

```bash
pytest TP2/tests/
```

## Ayuda

Cada servidor puede mostrar las opciones disponibles:

```bash
python3 TP2/server_scraping.py -h
python3 TP2/server_processing.py -h
```

