import re

from urllib.parse import urljoin, urlparse

from .config import RAW, URL_EDICION, NUM_CARREIRAS
from .scraper import obtener_soup


def descubrir_carreiras():
    """Descubre las carreras de la edición siguiendo sus enlaces."""

    # Obtener la página principal de la edición
    soup = obtener_soup(
        URL_EDICION,
        RAW / "edicion_2026.html"
    )

    # Buscar el enlace a los resultados por evento
    url_eventos = None

    for enlace in soup.find_all("a", href=True):
        texto = enlace.get_text(" ", strip=True).upper()

        if texto == "POR EVENTO":
            url_eventos = urljoin(URL_EDICION, enlace["href"])
            break

    if url_eventos is None:
        raise ValueError("No se encontró el enlace POR EVENTO.")

    print(f"\nPágina de eventos: {url_eventos}")

    # Obtener la página que contiene las carreras
    soup_eventos = obtener_soup(
        url_eventos,
        RAW / "eventos_2026.html"
    )

    carreiras = []
    urls_vistas = set()

    # Buscar los enlaces correspondientes a cada carrera
    for enlace in soup_eventos.find_all("a", href=True):

        url = urljoin(url_eventos, enlace["href"])
        ruta = urlparse(url).path

        if not re.search(r"/evento-\d+/?$", ruta):
            continue

        if url in urls_vistas:
            continue

        nome = enlace.get_text(" ", strip=True)

        if not nome:
            continue

        urls_vistas.add(url)

        carreiras.append({
            "orde": len(carreiras) + 1,
            "nome": nome,
            "url": url
        })

    print(f"\nCarreras encontradas: {len(carreiras)}")

    # Comprobar que hay suficientes carreras
    if len(carreiras) < NUM_CARREIRAS:
        raise ValueError("No se encontraron suficientes carreras.")

    # Mostrar las carreras descubiertas
    for carreira in carreiras:

        estado = (
            "INCLUIDA"
            if carreira["orde"] <= NUM_CARREIRAS
            else "EXCLUIDA"
        )

        print(
            f"[{estado}] "
            f"{carreira['orde']}. "
            f"{carreira['nome']}"
        )

    # Seleccionar únicamente las seis primeras
    seleccionadas = carreiras[:NUM_CARREIRAS]

    print(f"\nCarreras seleccionadas: {len(seleccionadas)}")

    return seleccionadas


if __name__ == "__main__":
    descubrir_carreiras()