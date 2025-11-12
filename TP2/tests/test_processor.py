import os
import socket
import struct
import json
import pytest

# Host y puerto por defecto para el servidor de procesamiento
HOST = os.environ.get("PROCESSOR_HOST", "127.0.0.1")
PORT = int(os.environ.get("PROCESSOR_PORT", "9001"))

def send_request(payload, host=HOST, port=PORT, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    msg = struct.pack(">I", len(data)) + data
    with socket.create_connection((host, port), timeout=10) as s:
        s.sendall(msg)
        raw_len = s.recv(4)
        if len(raw_len) < 4:
            raise RuntimeError("No se recibió el prefijo de longitud")
        msg_len = struct.unpack(">I", raw_len)[0]
        chunks = []
        remaining = msg_len
        while remaining:
            chunk = s.recv(min(4096, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        resp = b"".join(chunks)
    return json.loads(resp.decode("utf-8"))

def test_processor_returns_processing_data_or_error():
    payload = {"url": "https://example.com"}
    res = send_request(payload)
    assert "status" in res
    # O bien éxito con processing_data, o fallo con clave error
    if res.get("status") == "success":
        assert "processing_data" in res
        pd = res["processing_data"]
        assert "screenshot" in pd
        assert "performance" in pd
    else:
        assert "error" in res

