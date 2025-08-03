import json
import hashlib

def sha256_hex(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

with open("blockchain.json", "r") as f:
    blocks = json.load(f)

corruptos = []
alertas = 0
sum_frec = 0
sum_pres = 0
sum_oxi = 0

for i, blk in enumerate(blocks):
    prev_hash = blk['prev_hash']
    datos = blk['datos']
    timestamp = blk['timestamp']
    block_str = str(prev_hash) + str(datos) + timestamp
    hash_calc = sha256_hex(block_str)
    if blk['hash'] != hash_calc:
        corruptos.append(i)
    if blk.get("alerta"):
        alertas += 1
    sum_frec += datos['frecuencia']['media']
    sum_pres += datos['presion']['media']
    sum_oxi += datos['oxigeno']['media']

total = len(blocks)

with open("reporte.txt", "w") as f:
    f.write(f"Total de bloques: {total}\n")
    f.write(f"Bloques corruptos: {','.join(map(str, corruptos)) if corruptos else '0'}\n")
    f.write(f"Bloques con alerta: {alertas}\n")
    f.write(f"Promedio frecuencia: {sum_frec/total:.2f}\n")
    f.write(f"Promedio presión: {sum_pres/total:.2f}\n")
    f.write(f"Promedio oxígeno: {sum_oxi/total:.2f}\n")