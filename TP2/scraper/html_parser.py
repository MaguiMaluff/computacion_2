"""
Parsing HTML básico con BeautifulSoup para extraer:
- título
- enlaces (normalizados con base_url)
- meta tags (name y property)
- estructura de headers H1-H6 (conteo)
- cantidad de imágenes

"""
from typing import Dict, Any, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def _get_meta_mapping(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extrae meta tags relevantes en un diccionario.
    Considera atributos 'name' y 'property' (ej. og:title).
    """
    meta = {}
    for m in soup.find_all("meta"):
        # meta name="description" content="..."
        name = m.get("name")
        if name:
            meta[name.lower()] = m.get("content", "")
        # meta property="og:title" content="..."
        prop = m.get("property")
        if prop:
            meta[prop.lower()] = m.get("content", "")
    return meta


def _extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extrae enlaces absolutos resolviendo href relativos contra base_url.
    - Ignora enlaces sin href
    - Normaliza via urljoin para manejar redirecciones y base tags
    """
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        links.append(full)
    return links


def parse_html_basic(html: str, base_url: str = "") -> Dict[str, Any]:
    """
    Parsea HTML y devuelve un diccionario con la información principal.

    - `html`: contenido HTML como str
    - `base_url`: URL base para resolver enlaces relativos
    """
    # Crear el parser con lxml
    soup = BeautifulSoup(html, "lxml")

    # Título de la página
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Links
    links = _extract_links(soup, base_url)

    # Meta tags
    meta_tags = _get_meta_mapping(soup)

    # Estructura de headers H1-H6: contar ocurrencias
    structure = {}
    for i in range(1, 7):
        tag = f"h{i}"
        structure[tag] = len(soup.find_all(tag))

    # Cantidad de imágenes
    images_count = len(soup.find_all("img"))

    return {
        "title": title,
        "links": links,
        "meta_tags": meta_tags,
        "structure": structure,
        "images_count": images_count,
    }