import hashlib
import json

def sha256_hex(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def proceso_verificador(queue_a, queue_b, queue_c):
    blockchain = []
    prev_hash = '0' * 64
    for idx in range(60):
        res_a = queue_a.get()
        res_b = queue_b.get()
        res_c = queue_c.get()
        datos = {
            res_a['tipo']: {
                "media": res_a['media'],
                "desv": res_a['desv'],
                "ultimo": res_a['ultimo']
            },
            res_b['tipo']: {
                "media": res_b['media'],
                "desv": res_b['desv'],
                "ultimo": res_b['ultimo']
            },
            res_c['tipo']: {
                "media": res_c['media'],
                "desv": res_c['desv'],
                "ultimo": res_c['ultimo']
            }
        }
        alerta = (
            datos['frecuencia']['media'] >= 200 or
            datos['frecuencia']['ultimo'] >= 200 or
            datos['oxigeno']['media'] < 90 or
            datos['oxigeno']['media'] > 100 or
            datos['oxigeno']['ultimo'] < 90 or
            datos['oxigeno']['ultimo'] > 100 or
            datos['presion']['media'] >= 200 or
            datos['presion']['ultimo'] >= 200
        )
        timestamp = res_a['timestamp']
        block_data = {
            "timestamp": timestamp,
            "datos": datos,
            "alerta": alerta,
            "prev_hash": prev_hash
        }
        block_str = str(block_data['prev_hash']) + str(block_data['datos']) + block_data['timestamp']
        block_hash = sha256_hex(block_str)
        block_data['hash'] = block_hash
        blockchain.append(block_data)
        prev_hash = block_hash
        print(f"[{idx}] Hash: {block_hash} Alerta: {alerta}")

        with open("blockchain.json", "w") as f:
            json.dump(blockchain, f, indent=2)