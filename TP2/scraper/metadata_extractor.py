"""
Extractor de meta tags específicos (description, keywords, Open Graph).
Separa la lógica de metadata del parsing general.
"""
from typing import Dict
from bs4 import BeautifulSoup


def extract_standard_meta(html: str) -> Dict[str, str]:
    """
    Devuelve un dict con:
    - "description" y "keywords" si están presentes en meta name
    - cualquier meta con property que empiece por "og:" (Open Graph)
    """
    soup = BeautifulSoup(html, "lxml")
    meta = {}
    for m in soup.find_all("meta"):
        name = m.get("name")
        if name and name.lower() in ("description", "keywords"):
            meta[name.lower()] = m.get("content", "")
        prop = m.get("property")
        if prop and prop.startswith("og:"):
            meta[prop] = m.get("content", "")
    return meta