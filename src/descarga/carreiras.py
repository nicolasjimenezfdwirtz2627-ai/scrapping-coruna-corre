import re
import pandas as pd

from urllib.parse import urljoin, urlparse, parse_qs

from .config import RAW, INTERIM, URL_EDICION, NUM_CARREIRAS
from .scraper import obtener_soup
from datetime import date


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


def descubrir_absolutas(carreiras):
    """Localiza la categoría Absoluta de cada carrera."""

    resultados = []

    print("\n=== DESCUBRIMIENTO DE CATEGORÍAS ABSOLUTAS ===")

    for carreira in carreiras:

        orde = carreira["orde"]
        url = carreira["url"]

        print(f"\nCarrera {orde}: {carreira['nome']}")

        # Obtener la página de categorías de la carrera
        soup = obtener_soup(
            url,
            RAW / f"carreira_{orde:02d}.html"
        )

        candidatas = {}

        # Buscar el enlace de la categoría Absoluta
        for enlace in soup.find_all("a", href=True):

            texto = enlace.get_text(" ", strip=True)

            if not re.match(r"^ABSOLUTA\b", texto, re.IGNORECASE):
                continue

            url_categoria = urljoin(url, enlace["href"])
            ruta = urlparse(url_categoria).path

            if re.search(r"/competicion-\d+/?$", ruta):
                candidatas[url_categoria] = texto

        # Comprobar que existe una única categoría Absoluta
        if len(candidatas) != 1:
            raise ValueError(
                f"Carrera {orde}: se esperaba una categoría "
                f"Absoluta y se encontraron {len(candidatas)}."
            )

        url_absoluta, categoria = next(iter(candidatas.items()))

        # Añadir la información descubierta
        resultados.append({
            **carreira,
            "categoria": categoria,
            "url_absoluta": url_absoluta
        })

        print(f"[OK] Categoría: {categoria}")
        print(f"[OK] URL: {url_absoluta}")

    print(f"\nCategorías Absolutas encontradas: {len(resultados)}")

    return resultados


def extraer_filas(soup):
    """Extrae los resultados de una página de clasificación."""

    columnas = {
        "Puesto": "puesto",
        "Dorsal": "dorsal",
        "Nombre": "nome",
        "Apellidos": "apelidos",
        "P. Sexo": "p_sexo",
        "P. Categoría": "p_categoria",
        "Tiempo": "tempo"
    }

    # Localizar la tabla de resultados por sus cabeceras
    for tabla in soup.find_all("table"):

        cabeceras = [
            th.get_text(" ", strip=True)
            for th in tabla.select("thead th")
        ]

        if all(columna in cabeceras for columna in columnas):
            break

    else:
        raise ValueError("No se encontró la tabla de resultados.")

    # Relacionar cada columna con su posición
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
                "Se encontró una fila con un número "
                "inesperado de columnas."
            )

        fila = {
            columna: celdas[posicion].get_text(" ", strip=True)
            for columna, posicion in posiciones.items()
        }

        resultados.append(fila)

    return resultados


def obtener_siguiente_pagina(soup, url_actual):
    """Localiza el enlace habilitado a la siguiente página."""

    for enlace in soup.select(".pagination a[href]"):

        texto = enlace.get_text(" ", strip=True).casefold()

        if texto != "siguiente":
            continue

        padre = enlace.find_parent("li")

        # Comprobar si el enlace está deshabilitado
        if "disabled" in enlace.get("class", []):
            continue

        if enlace.get("aria-disabled") == "true":
            continue

        if padre and "disabled" in padre.get("class", []):
            continue

        url_siguiente = urljoin(url_actual, enlace["href"])

        # Verificar que seguimos en la misma clasificación
        actual = urlparse(url_actual)
        siguiente = urlparse(url_siguiente)

        if (
            actual.netloc != siguiente.netloc
            or actual.path != siguiente.path
        ):
            raise ValueError(
                "El enlace de paginación apunta a otra clasificación."
            )

        # Comprobar que avanzamos exactamente una página
        pagina_actual = int(
            parse_qs(actual.query).get("page", ["1"])[0]
        )

        pagina_siguiente = int(
            parse_qs(siguiente.query).get("page", ["1"])[0]
        )

        if pagina_siguiente != pagina_actual + 1:
            raise ValueError("Salto inesperado en la paginación.")

        return url_siguiente

    return None


def descargar_resultados(carreira):
    """Descarga todas las páginas de resultados de una carrera."""

    orde = carreira["orde"]
    url = carreira["url_absoluta"]

    pagina = 1
    resultados = []

    urls_visitadas = set()
    paginas_vistas = set()
    filas_por_pagina = []

    print(f"\n=== RESULTADOS DE LA CARRERA {orde} ===")
    print(carreira["nome"])

    while url is not None:

        # Evitar bucles infinitos
        if url in urls_visitadas:
            raise ValueError("Se ha detectado una URL repetida.")

        urls_visitadas.add(url)

        # Descargar o reutilizar la página
        destino = RAW / (
            f"carreira_{orde:02d}_resultados_p{pagina:03d}.html"
        )

        soup = obtener_soup(url, destino)

        # Extraer las filas de la página
        filas = extraer_filas(soup)

        if not filas:
            raise ValueError(f"La página {pagina} no contiene resultados.")

        # Detectar páginas con contenido repetido
        firma = tuple(tuple(fila.values()) for fila in filas)

        if firma in paginas_vistas:
            raise ValueError("Se han detectado páginas repetidas.")

        paginas_vistas.add(firma)

        resultados.extend(filas)
        filas_por_pagina.append(len(filas))

        print(
            f"Página {pagina}: {len(filas)} filas | "
            f"Total acumulado: {len(resultados)}"
        )

        # Buscar la siguiente página
        url = obtener_siguiente_pagina(soup, url)

        if url is not None:
            pagina += 1

    # Comprobar la coherencia del número de filas
    capacidad = filas_por_pagina[0]

    if any(n != capacidad for n in filas_por_pagina[:-1]):
        raise ValueError("Hay páginas intermedias incompletas.")

    if not 1 <= filas_por_pagina[-1] <= capacidad:
        raise ValueError("Número de filas inesperado en la última página.")

    # Crear el DataFrame
    df = pd.DataFrame(resultados)

    # Guardar el CSV
    INTERIM.mkdir(parents=True, exist_ok=True)

    destino_csv = INTERIM / f"carreira_{orde:02d}_raw.csv"

    df.to_csv(
        destino_csv,
        index=False,
        encoding="utf-8"
    )

    print("\n=== RESUMEN DE LA DESCARGA ===")
    print(f"Páginas descargadas o reutilizadas: {pagina}")
    print(f"Filas por página completa: {capacidad}")
    print(f"Filas en la última página: {filas_por_pagina[-1]}")
    print(f"Total de resultados: {len(df)}")
    print(f"Columnas: {df.columns.tolist()}")
    print(f"CSV generado: {destino_csv.name}")

    return df


def obtener_fecha(carreira):
    """Obtiene la fecha desde la página informativa del evento."""

    # Extraer el identificador del evento
    coincidencia = re.search(
        r"/evento-(\d+)/?$",
        urlparse(carreira["url"]).path
    )

    if not coincidencia:
        raise ValueError("No se encontró el identificador del evento.")

    evento_id = coincidencia.group(1)

    # Construir la URL de información
    url_info = urljoin(
        carreira["url"],
        f"/es/web/evento/{evento_id}/"
    )

    # Descargar o reutilizar el HTML
    soup = obtener_soup(
        url_info,
        RAW / f"carreira_{carreira['orde']:02d}_info.html"
    )

    texto = soup.get_text(" ", strip=True)

    # Buscar la fecha dentro del apartado Lugar y Horarios
    coincidencia = re.search(
        r"Lugar\s+y\s+Horarios\s*"
        r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)"
        r"\s+de\s+(\d{4})",
        texto,
        re.IGNORECASE
    )

    if not coincidencia:
        raise ValueError(
            f"No se encontró la fecha de la carrera "
            f"{carreira['orde']}."
        )

    dia, mes, anio = coincidencia.groups()

    meses = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12
    }

    fecha = date(
        int(anio),
        meses[mes.lower()],
        int(dia)
    )

    return fecha


def descargar_metadatos(carreiras):
    """Extrae y guarda la información de las carreras."""

    resultados = []
    fechas = []

    print("\n=== EXTRACCIÓN DE METADATOS ===")

    for carreira in carreiras:

        fecha = obtener_fecha(carreira)
        fechas.append(fecha)

        resultados.append({
            "orde": carreira["orde"],
            "nome": carreira["nome"],
            "fecha": fecha.strftime("%d/%m/%Y")
        })

        print(
            f"[OK] Carrera {carreira['orde']}: "
            f"{fecha.strftime('%d/%m/%Y')}"
        )

    # Comprobar el orden cronológico
    if fechas != sorted(fechas):
        raise ValueError(
            "Las carreras no están ordenadas cronológicamente."
        )

    if len(set(fechas)) != len(fechas):
        raise ValueError("Se encontraron fechas repetidas.")

    df = pd.DataFrame(
        resultados,
        columns=["orde", "nome", "fecha"]
    )

    INTERIM.mkdir(parents=True, exist_ok=True)

    destino = INTERIM / "carreiras_raw.csv"

    df.to_csv(
        destino,
        index=False,
        encoding="utf-8"
    )

    print("\n=== RESUMEN DE METADATOS ===")
    print(df.to_string(index=False))

    print(f"\nCarreras: {len(df)}")
    print("Orden cronológico: correcto")
    print(f"Columnas: {df.columns.tolist()}")
    print(f"CSV generado: {destino.name}")

    return df




if __name__ == "__main__":

    carreiras = descubrir_carreiras()
    carreiras = descubrir_absolutas(carreiras)

    resumen = []

    # Descargar los resultados de cada carrera
    for carreira in carreiras:

        df = descargar_resultados(carreira)

        resumen.append({
            "orde": carreira["orde"],
            "nome": carreira["nome"],
            "participacions": len(df)
        })

    # Mostrar un resumen global
    df_resumen = pd.DataFrame(resumen)

    print("\n=== RESUMEN GLOBAL DE LAS CARRERAS ===")

    print(df_resumen.to_string(index=False))

    print(f"\nCarreras procesadas: {len(df_resumen)}")

    print(
        "Total de participaciones:",
        df_resumen["participacions"].sum()
    )