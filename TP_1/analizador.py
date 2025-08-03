import numpy as np

def proceso_analizador(tipo, pipe, queue):
    ventana = []
    while True:
        data = pipe.recv()
        if data == 'FIN':
            break
        if tipo == 'frecuencia':
            valor = data['frecuencia']
        elif tipo == 'presion':
            valor = data['presion'][0]  # sistólica
        elif tipo == 'oxigeno':
            valor = data['oxigeno']
        ventana.append(valor)
        if len(ventana) > 30:
            ventana.pop(0)
        media = float(np.mean(ventana))
        desv = float(np.std(ventana))
        resultado = {
            "tipo": tipo,
            "timestamp": data['timestamp'],
            "media": media,
            "desv": desv,
            "ultimo": valor 
        }
        queue.put(resultado)