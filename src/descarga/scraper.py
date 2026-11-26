import requests

from pathlib import Path
from time import sleep
from bs4 import BeautifulSoup

from .config import CABECERAS, PAUSA, TIMEOUT


def descargar(url: str, destino: Path) -> bytes:
    """Descarga una página o reutiliza su copia local."""

    destino.parent.mkdir(parents=True, exist_ok=True)

    # Si ya existe, reutilizamos el archivo local
    if destino.exists():
        print(f"[CACHÉ] {destino.name}")
        return destino.read_bytes()

    print(f"[DESCARGA] {url}")

    try:
        respuesta = requests.get(
            url,
            headers=CABECERAS,
            timeout=TIMEOUT
        )

        respuesta.raise_for_status()

        # Guardamos el HTML original en bytes
        destino.write_bytes(respuesta.content)

        print(f"[OK] Guardado: {destino.name}")

        return respuesta.content

    finally:
        # Respetamos la pausa incluso si ocurre un error
        sleep(PAUSA)


def obtener_soup(url: str, destino: Path) -> BeautifulSoup:
    """Obtiene una página HTML y la interpreta con BeautifulSoup."""

    contenido = descargar(url, destino)

    return BeautifulSoup(contenido, "html.parser")