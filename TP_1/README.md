# Sistema Concurrente de Análisis Biométrico con Cadena de Bloques Local

## Descripción

Este sistema simula una prueba de esfuerzo biométrica, analizando en tiempo real señales de frecuencia cardíaca, presión arterial y saturación de oxígeno, y almacenando los resultados procesados en una cadena de bloques local para garantizar la integridad. La arquitectura utiliza procesos concurrentes y comunicación por IPC, asegurando análisis paralelos y persistencia segura de los datos.

## Arquitectura

- **Proceso Principal:** Genera una muestra biométrica por segundo durante 60 segundos y la envía a los analizadores.
- **Procesos Analizadores (A/B/C):** Cada uno recibe la muestra, extrae su señal respectiva (frecuencia, presión, oxígeno), mantiene una ventana móvil de los últimos 30 valores, calcula la media y desviación estándar, y envía el resultado al verificador.
- **Proceso Verificador:** Recibe los resultados de los analizadores, verifica que estén dentro de los rangos aceptables, construye el bloque correspondiente, lo encadena y lo guarda en `blockchain.json`.
- **Cadena de Bloques:** Archivo persistente que almacena todos los bloques generados, cada uno con hash propio y del anterior.
- **Script de Verificación:** Analiza la integridad de la cadena y genera un reporte estadístico en `reporte.txt`.

## Requisitos

- Python ≥ 3.9
- `numpy` (instalable vía pip)
- Sistema operativo compatible con multiprocessing (Linux, Windows, macOS)

## Instalación

1. Clona el repositorio y entra en la carpeta del proyecto.
2. Instala la dependencia requerida:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

### 1. Ejecutar el sistema principal

Esto generará el archivo `blockchain.json` con los resultados de la simulación.

```bash
python main.py
```

Al finalizar, verás impresos los hashes de los bloques y el estado de alerta, además de la confirmación `"Fin"`.

### 2. Verificar la cadena y generar el reporte

Esto leerá la cadena de bloques y generará el reporte final en `reporte.txt`.

```bash
python verificar_cadena.py
```

Encontrarás el reporte en el archivo `reporte.txt`.

## Archivos generados

- `blockchain.json`: Cadena de bloques con todos los datos y hashes.
- `reporte.txt`: Resumen estadístico y verificación de integridad.

## Estructura de archivos

```
main.py                  # Proceso principal y coordinación
analizador.py            # Procesos analizadores de señales
verificador.py           # Proceso verificador y blockchain
verificar_cadena.py      # Verificador de integridad y reporte final
blockchain.json          # Cadena de bloques generada
reporte.txt              # Reporte final
requirements.txt         # Dependencias
README.md                # Este archivo
```

## Ejemplo de reporte generado

```plaintext
Total de bloques: 60
Bloques corruptos: 0
Bloques con alerta: 2
Promedio frecuencia: 79.35
Promedio presión: 120.42
Promedio oxígeno: 97.60
```

## Notas técnicas

- El sistema usa `multiprocessing.Pipe` para enviar muestras del proceso principal a cada analizador, y `multiprocessing.Queue` para enviar resultados de los analizadores al verificador.
- La persistencia se realiza a disco en formato JSON, garantizando integridad vía hashes encadenados (SHA-256).
- El cierre es limpio: todos los procesos hijos terminan correctamente y los recursos se liberan.