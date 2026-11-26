import requests

from time import sleep
from urllib.robotparser import RobotFileParser

from .config import (
    URL_ROBOTS,
    URL_EDICION,
    USER_AGENT,
    CABECERAS,
    TIMEOUT,
    PAUSA
)


def comprobar_robots():
    """Comprueba la existencia y restricciones del robots.txt."""

    print("=== COMPROBACIÓN DEL ROBOTS.TXT ===")
    print(f"URL: {URL_ROBOTS}")

    try:
        respuesta = requests.get(
            URL_ROBOTS,
            headers=CABECERAS,
            timeout=TIMEOUT
        )

        print(f"Código HTTP: {respuesta.status_code}")
        print(f"Tipo de contenido: {respuesta.headers.get('Content-Type')}")

        if respuesta.status_code == 200:

            contenido = respuesta.text.strip()

            if "html" in respuesta.headers.get("Content-Type", "").lower():
                print("La respuesta es HTML, no un robots.txt válido.")
                return None

            print("\nContenido del robots.txt:")
            print(contenido)

            robots = RobotFileParser()
            robots.set_url(URL_ROBOTS)
            robots.parse(contenido.splitlines())

            permitido = robots.can_fetch(USER_AGENT, URL_EDICION)

            print(f"\nAcceso a la edición permitido por robots.txt: {permitido}")

            return permitido

        elif respuesta.status_code in (404, 410):
            print("No se ha encontrado el archivo robots.txt.")
            print("Esto no implica autorización para reutilizar los datos.")

            return None

        else:
            print("No se han podido verificar las restricciones.")
            return None

    except requests.RequestException as error:
        print(f"Error durante la petición: {error}")
        return None

    finally:
        sleep(PAUSA)


if __name__ == "__main__":
    comprobar_robots()