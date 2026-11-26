import re
import pandas as pd

from .config import RAW, INTERIM, URL_INSCRITOS
from .scraper import obtener_soup
from .carreiras import obtener_siguiente_pagina


def obtener_total_inscritos(soup):
    """Obtiene el número de inscritos publicado por la web."""

    for elemento in soup.select("h1, h2, h3, h4, h5"):

        texto = elemento.get_text(" ", strip=True)

        if "INSCRITOS EN" not in texto.upper():
            continue

        coincidencia = re.search(
            r"2026\s+(\d+)\s*$",
            texto
        )

        if coincidencia:
            return int(coincidencia.group(1))

    raise ValueError(
        "No se encontró el contador oficial de inscritos."
    )


def extraer_inscritos(soup):
    """Extrae los campos necesarios de la tabla de inscritos."""

    columnas = {
        "Nombre": "nome",
        "Apellidos": "apelidos",
        "Dorsal": "dorsal"
    }

    # Localizar la tabla mediante sus cabeceras
    for tabla in soup.find_all("table"):

        cabeceras = [
            th.get_text(" ", strip=True)
            for th in tabla.select("thead th")
        ]

        if all(columna in cabeceras for columna in columnas):
            break

    else:
        raise ValueError(
            "No se encontró la tabla de inscritos."
        )

    # Identificar la posición de cada columna
    posiciones = {
        destino: cabeceras.index(origen)
        for origen, destino in columnas.items()
    }

    resultados = []

    for tr in tabla.find_all("tr"):

        celdas = tr.find_all("td", recursive=False)

        if not celdas:
            continue

        if len(celdas) != len(cabeceras):
            raise ValueError(
                "Número inesperado de columnas en inscritos."
            )

        fila = {
            columna: celdas[posicion].get_text(" ", strip=True)
            for columna, posicion in posiciones.items()
        }

        resultados.append(fila)

    return resultados


def descargar_inscritos():
    """Descarga y valida la lista completa de inscritos."""

    url = URL_INSCRITOS
    pagina = 1

    resultados = []
    urls_visitadas = set()
    paginas_vistas = set()
    filas_por_pagina = []

    total_oficial = None

    print("\n=== DESCARGA DE INSCRITOS ===")

    while url is not None:

        # Evitar visitar dos veces la misma URL
        if url in urls_visitadas:
            raise ValueError("URL de inscritos repetida.")

        urls_visitadas.add(url)

        destino = RAW / f"inscritos_p{pagina:03d}.html"

        soup = obtener_soup(url, destino)

        # Obtener y comprobar el contador oficial
        contador = obtener_total_inscritos(soup)

        if total_oficial is None:
            total_oficial = contador
            print(f"Inscritos según la web: {total_oficial}")

        elif contador != total_oficial:
            raise ValueError(
                "El contador de inscritos ha cambiado "
                "durante la descarga."
            )

        # Extraer los registros de la página
        filas = extraer_inscritos(soup)

        if not filas:
            raise ValueError(f"Página {pagina} vacía.")

        # Detectar páginas repetidas
        firma = tuple(
            tuple(fila.values()) for fila in filas
        )

        if firma in paginas_vistas:
            raise ValueError("Página de inscritos repetida.")

        paginas_vistas.add(firma)

        resultados.extend(filas)
        filas_por_pagina.append(len(filas))

        print(
            f"Página {pagina}: {len(filas)} filas | "
            f"Total acumulado: {len(resultados)}"
        )

        # Continuar con la siguiente página
        url = obtener_siguiente_pagina(soup, url)

        if url is not None:
            pagina += 1

    # Comprobar la coherencia de la paginación
    capacidad = filas_por_pagina[0]

    if any(n != capacidad for n in filas_por_pagina[:-1]):
        raise ValueError("Hay páginas intermedias incompletas.")

    if not 1 <= filas_por_pagina[-1] <= capacidad:
        raise ValueError("Última página incoherente.")

    # Contrastar con el contador oficial
    if len(resultados) != total_oficial:
        raise ValueError(
            f"Se han obtenido {len(resultados)} inscritos, "
            f"pero la web indica {total_oficial}."
        )

    # Crear el DataFrame
    df = pd.DataFrame(
        resultados,
        columns=["nome", "apelidos", "dorsal"]
    )

    # Guardar el CSV
    INTERIM.mkdir(parents=True, exist_ok=True)

    destino_csv = INTERIM / "inscritos_raw.csv"

    df.to_csv(
        destino_csv,
        index=False,
        encoding="utf-8"
    )

    print("\n=== RESUMEN DE INSCRITOS ===")
    print(f"Páginas recorridas: {pagina}")
    print(f"Filas por página completa: {capacidad}")
    print(f"Filas en la última página: {filas_por_pagina[-1]}")
    print(f"Inscritos según la web: {total_oficial}")
    print(f"Inscritos extraídos: {len(df)}")
    print("Validación del contador oficial: CORRECTA")
    print(f"Columnas: {df.columns.tolist()}")
    print(f"CSV generado: {destino_csv.name}")

    return df


if __name__ == "__main__":
    descargar_inscritos()