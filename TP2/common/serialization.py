"""
Módulo: serialization.py
-------------------------
Maneja la serialización y deserialización de datos entre el Servidor A y el Servidor B.

Funciones principales:
- serialize: Convierte datos (dict) a JSON.
- deserialize: Convierte JSON a datos (dict).
"""

import json


def serialize(data):
    """
    Serializa un diccionario (dict) a una cadena JSON (str).

    Args:
        data (dict): El diccionario a serializar.

    Returns:
        str: La representación en formato JSON del diccionario.

    Raises:
        ValueError: Si los datos no son serializables.
    """
    try:
        return json.dumps(data)
    except TypeError as e:
        raise ValueError(f"Error al serializar los datos: {str(e)}")


def deserialize(json_data):
    """
    Deserializa una cadena JSON (str) a un diccionario (dict).

    Args:
        json_data (str): La cadena JSON.

    Returns:
        dict: El diccionario obtenido del JSON.

    Raises:
        ValueError: Si el JSON no es válido.
    """
    try:
        return json.loads(json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al deserializar los datos: {str(e)}")