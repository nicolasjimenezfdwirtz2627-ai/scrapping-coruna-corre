import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bs4 import BeautifulSoup

from src.descarga.config import PAUSA
from src.descarga.scraper import descargar

from src.descarga.carreiras import (
    extraer_filas,
    obtener_siguiente_pagina
)

from src.descarga.inscritos import (
    extraer_inscritos,
    obtener_total_inscritos
)


class TestDescarga(unittest.TestCase):

    def test_descarga_y_cache(self):
        """Comprueba que un HTML se descarga una sola vez."""

        contenido = b"<html>Pagina de prueba</html>"

        with TemporaryDirectory() as carpeta:

            destino = Path(carpeta) / "prueba.html"

            with patch(
                "src.descarga.scraper.requests.get"
            ) as peticion, patch(
                "src.descarga.scraper.sleep"
            ) as pausa:

                peticion.return_value.content = contenido

                primera = descargar(
                    "https://example.com",
                    destino
                )

                segunda = descargar(
                    "https://example.com",
                    destino
                )

                self.assertEqual(primera, contenido)
                self.assertEqual(segunda, contenido)
                self.assertEqual(destino.read_bytes(), contenido)

                peticion.assert_called_once()
                pausa.assert_called_once_with(PAUSA)


    def test_extraer_resultados(self):
        """Comprueba la extracción de las siete columnas."""

        html = """
        <table>
            <thead>
                <tr>
                    <th></th>
                    <th>Puesto</th>
                    <th>Dorsal</th>
                    <th>Nombre</th>
                    <th>Apellidos</th>
                    <th>P. Sexo</th>
                    <th>P. Categoría</th>
                    <th>Tiempo</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td></td>
                    <td>1</td>
                    <td>999</td>
                    <td>PERSONA</td>
                    <td>FICTICIA</td>
                    <td>M-1</td>
                    <td>MS2M-1</td>
                    <td>00:25:30</td>
                </tr>
            </tbody>
        </table>
        """

        soup = BeautifulSoup(html, "html.parser")

        resultado = extraer_filas(soup)

        self.assertEqual(resultado, [{
            "puesto": "1",
            "dorsal": "999",
            "nome": "PERSONA",
            "apelidos": "FICTICIA",
            "p_sexo": "M-1",
            "p_categoria": "MS2M-1",
            "tempo": "00:25:30"
        }])


    def test_tabla_incorrecta(self):
        """Comprueba que se detecta una tabla incorrecta."""

        html = """
        <table>
            <thead>
                <tr><th>Nombre</th></tr>
            </thead>
        </table>
        """

        soup = BeautifulSoup(html, "html.parser")

        with self.assertRaises(ValueError):
            extraer_filas(soup)


    def test_siguiente_pagina(self):
        """Comprueba que se localiza la siguiente página."""

        html = """
        <ul class="pagination">
            <li>
                <a href="?page=2">Siguiente</a>
            </li>
        </ul>
        """

        soup = BeautifulSoup(html, "html.parser")

        resultado = obtener_siguiente_pagina(
            soup,
            "https://example.com/resultados"
        )

        self.assertEqual(
            resultado,
            "https://example.com/resultados?page=2"
        )


    def test_fin_paginacion(self):
        """Comprueba que se detiene en la última página."""

        html = """
        <ul class="pagination">
            <li class="disabled">
                <a href="?page=3">Siguiente</a>
            </li>
        </ul>
        """

        soup = BeautifulSoup(html, "html.parser")

        resultado = obtener_siguiente_pagina(
            soup,
            "https://example.com/resultados?page=2"
        )

        self.assertIsNone(resultado)


    def test_salto_pagina(self):
        """Comprueba que no se permiten saltos de página."""

        html = """
        <ul class="pagination">
            <li>
                <a href="?page=5">Siguiente</a>
            </li>
        </ul>
        """

        soup = BeautifulSoup(html, "html.parser")

        with self.assertRaises(ValueError):

            obtener_siguiente_pagina(
                soup,
                "https://example.com/resultados?page=2"
            )


    def test_extraer_inscritos(self):
        """Comprueba que solo se extraen los campos necesarios."""

        html = """
        <table>
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Apellidos</th>
                    <th>Dorsal</th>
                    <th>Pagado</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>PERSONA</td>
                    <td>FICTICIA</td>
                    <td>999</td>
                    <td>Sí</td>
                    <td>Confirmado</td>
                </tr>
            </tbody>
        </table>
        """

        soup = BeautifulSoup(html, "html.parser")

        resultado = extraer_inscritos(soup)

        self.assertEqual(resultado, [{
            "nome": "PERSONA",
            "apelidos": "FICTICIA",
            "dorsal": "999"
        }])


    def test_contador_inscritos(self):
        """Comprueba la extracción del contador oficial."""

        html = """
        <h2>
            INSCRITOS EN
            CIRCUITO DE CARREIRAS POPULARES
            CORUÑA CORRE 2026 125
        </h2>
        """

        soup = BeautifulSoup(html, "html.parser")

        self.assertEqual(
            obtener_total_inscritos(soup),
            125
        )


if __name__ == "__main__":
    unittest.main()