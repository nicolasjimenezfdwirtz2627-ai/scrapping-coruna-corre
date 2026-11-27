# scrapping-coruna-corre

## Estructura do proxecto

```
scrapping-coruna-corre/
├── .env                  # Configuración
├── requirements.txt      # Depedencias de python
├── datos/                # Os datos
    ├── clean/            # Os datos limpos
    ├── external/         # Os datos que non veñen da páxina da carreira
    ├── interim/          # Os datos sen anonimizar
    └── raw/              # Os datos tal e como chegan
└── notebooks/            # Os notebooks do proxecto

```

## Legalidade e protección de datos

### Comprobación do robots.txt

Antes de realizar la descarga de los datos, hemos comprobado si la web de Coruña Corre dispone de un archivo `robots.txt`.

- URL consultada: https://corunacorre.com/robots.txt
- Fecha de comprobación: 25/11/2026.
- Código de respuesta HTTP: 404 (Not Found).
- Tipo de contenido: `text/html; charset=utf-8`.

La comprobación se ha realizado mediante el script `src/descarga/legalidad.py`, utilizando la librería `requests` y un User-Agent propio.

El resultado indica que no se ha encontrado un archivo `robots.txt` en la ubicación estándar. Según el apartado 2.3.1.3 del RFC 9309, esto no establece una restricción de acceso mediante dicho protocolo.

Sin embargo, la ausencia de este archivo no implica que exista autorización para reutilizar libremente los datos. Debemos respetar igualmente las condiciones de uso de la web y la normativa de protección de datos.

Referencia: https://www.rfc-editor.org/rfc/rfc9309.html

### Aviso legal y reglamento

Hemos consultado el aviso legal de Coruña Corre y el artículo 13 del reglamento del circuito de 2026, relativo a la protección de datos personales.

El aviso legal identifica a MULTISPORTS GALICIA, S.L. como titular del dominio y establece limitaciones sobre la reproducción, distribución y almacenamiento de sus contenidos.

El artículo 13 identifica al Concello da Coruña como responsable del tratamiento de los datos personales de los participantes.

La reutilización de estos datos con fines académicos requiere comprobar que existe una base jurídica adecuada y que se respetan las condiciones de uso.

Fuentes consultadas:

- [Aviso legal](https://corunacorre.com/gl/web/nota/legal/)
- [Artículo 13 del reglamento](https://corunacorre.com/gl/page/lopd-carrera)

### Datos personales y finalidad

Los resultados de las carreras y la lista de inscritos contienen datos personales como nombres, apellidos, dorsales, categorías, posiciones y tiempos de carrera.

La finalidad prevista del tratamiento es exclusivamente académica: analizar la participación, la evolución del rendimiento deportivo y las diferencias entre los corredores inscritos en el circuito y los inscritos por prueba.

Limitaremos la extracción a la categoría Absoluta de las seis primeras carreras de la edición de 2026 y a los datos necesarios para el proyecto.

### Medidas de protección de datos

Para proteger los datos personales y realizar una extracción responsable, aplicaremos las siguientes medidas:

- Utilizar un User-Agent propio que identifique el proyecto académico.
- Establecer una pausa de 1,5 segundos entre peticiones HTTP.
- Almacenar las páginas descargadas localmente para evitar peticiones repetidas.
- Excluir mediante `.gitignore` las carpetas `datos/raw/`, `datos/interim/` y `datos/clean/`, así como el archivo `.env`.
- No mostrar nombres, apellidos ni dorsales reales en las salidas de ejecución, notebooks, capturas o presentación.
- No compartir datos personales reales con herramientas de inteligencia artificial.
- Pseudonimizar los participantes mediante HMAC-SHA256 durante la fase de integración.
- Publicar únicamente resultados que no permitan identificar a los participantes.
- Limitar el acceso a los datos personales y su conservación a lo necesario para el proyecto.

## Fase 1. Descarga de datos

La primera fase del pipeline consiste en obtener automáticamente los resultados de las carreras, la información de cada evento y la lista de inscritos en el circuito Coruña Corre de 2026.

### Fuentes de datos

- Resultados de la edición: https://corunacorre.com/es/web/resultado/edicion-63
- Información de las carreras: páginas individuales de los eventos de Coruña Corre.
- Lista de inscritos: https://corunacorre.com/es/web/inscripcion/listado/

Fecha de descarga: 25/11/2026.

Se han seleccionado las seis primeras carreras del circuito y únicamente sus categorías Absolutas (2008 e anteriores). Se ha excluido la séptima carrera, Novo Mesoiro, para respetar el alcance establecido en el enunciado.

### Estructura del código

El código de descarga se ha organizado en módulos dentro de `src/descarga/`:

| Archivo | Función |
|---|---|
| `config.py` | Configuración de rutas, URLs y parámetros de las peticiones. |
| `legalidad.py` | Comprobación de la existencia y restricciones del robots.txt. |
| `scraper.py` | Descarga de páginas HTML y gestión de la caché local. |
| `carreiras.py` | Descubrimiento de carreras, categorías Absolutas, paginación, extracción de resultados y metadatos. |
| `inscritos.py` | Extracción de inscritos y validación del contador oficial. |
| `main.py` | Ejecución completa del pipeline de descarga. |

### Funcionamiento

El programa parte de la página de resultados de la edición de 2026 y sigue el enlace de resultados por evento para descubrir las carreras disponibles.

A continuación, identifica la categoría Absoluta de cada carrera mediante el texto de sus enlaces, sin depender de identificadores ni posiciones establecidos manualmente.

Para recorrer las clasificaciones, sigue el enlace habilitado `Siguiente` hasta alcanzar la última página. De esta forma, no necesita conocer previamente el número de páginas.

Las peticiones se realizan mediante `requests`, utilizando un User-Agent propio, un tiempo máximo de espera de 20 segundos y una pausa de 1,5 segundos.

Cada página se almacena en bytes dentro de `datos/raw/`. Si el archivo ya existe, se reutiliza su contenido sin realizar otra petición HTTP.

Los resultados extraídos se guardan en `datos/interim/` mediante pandas, respetando el contrato de datos acordado por el grupo.

### Ejecución de la descarga

Desde la raíz del repositorio, utilizando Python 3 y un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Comprobación previa del robots.txt:

```bash
python -m src.descarga.legalidad
```

Ejecución completa de la descarga:

```bash
python -m src.descarga.main
```

También es posible ejecutar las extracciones de forma independiente:

```bash
python -m src.descarga.carreiras
python -m src.descarga.inscritos
```

### Resultados obtenidos

| Carrera | Páginas HTML | Filas extraídas |
|---|---:|---:|
| Torre de Hércules | 60 | 1489 |
| Matogrande - Xuxán | 38 | 929 |
| San Pedro de Visma | 32 | 795 |
| Os Rosales | 35 | 875 |
| Volta a Oza | 27 | 659 |
| Ventorrillo | 26 | 643 |
| **Total** | **218** | **5390** |

La lista de inscritos se ha obtenido recorriendo 94 páginas y extrayendo 2345 registros, coincidiendo exactamente con el contador publicado por la web.

### Contrato de datos

Los archivos generados en `datos/interim/` son:

| Archivo | Columnas |
|---|---|
| `carreira_01_raw.csv` a `carreira_06_raw.csv` | puesto, dorsal, nome, apelidos, p_sexo, p_categoria, tempo |
| `carreiras_raw.csv` | orde, nome, fecha |
| `inscritos_raw.csv` | nome, apelidos, dorsal |

Todos los CSV se generan con codificación UTF-8, separador de coma y sin incluir el índice de pandas.

Los nombres, apellidos, posiciones y tiempos se conservan sin aplicar transformaciones de limpieza, ya que estas corresponden a la siguiente fase del pipeline.

Las fechas de las carreras se representan mediante el formato `dd/mm/yyyy`.

En la lista de inscritos no se incorporan al CSV los campos relativos al pago y al estado de inscripción, puesto que no forman parte del contrato de datos.

### Validación de la descarga

Se han realizado las siguientes comprobaciones:

- Descubrimiento de las siete carreras y selección de las seis primeras.
- Localización automática de las seis categorías Absolutas.
- Ausencia de URLs y páginas completas repetidas durante la paginación.
- Validación de las cabeceras de las tablas.
- Coherencia entre el número de páginas y las filas extraídas.
- Comprobación del orden cronológico de las carreras.
- Coincidencia entre el número de inscritos extraídos y el contador oficial.
- Verificación de las columnas de los ocho CSV.
- Comprobación de la protección de los archivos mediante `.gitignore`.

También se ha ejecutado el pipeline completo bloqueando las peticiones HTTP mediante `unittest.mock`. El resultado ha sido satisfactorio: se han regenerado los ocho CSV sin realizar ninguna llamada a `requests.get()`.

### Pruebas automatizadas

Se han desarrollado ocho pruebas unitarias en `tests/test_descarga.py`, utilizando datos ficticios y peticiones HTTP simuladas.

Para ejecutarlas:

```bash
python -m unittest discover -s tests -p "test_descarga.py" -v
```

Resultado obtenido:

- Pruebas ejecutadas: 8.
- Pruebas superadas: 8.
- Errores: 0.

Las pruebas permiten comprobar el funcionamiento de la descarga, la caché, la extracción de tablas, la paginación y el contador de inscritos sin necesidad de conectarse a la web.

### Protección de los archivos generados

Los HTML originales y los CSV intermedios contienen datos personales, por lo que no se incluyen en el repositorio.

Cada integrante del grupo puede generar los archivos localmente mediante el código proporcionado, evitando publicar los datos personales en GitHub.

## USO DE IA

Durante el desarrollo de la fase de descarga se ha utilizado ChatGPT como herramienta de apoyo para comprender el funcionamiento del scraping, organizar la estructura del código, desarrollar y revisar funciones, resolver dudas técnicas y preparar las pruebas y la documentación.

Las funciones se han ejecutado y comprobado progresivamente en el entorno local, verificando los resultados obtenidos y su adecuación a los requisitos del proyecto.

No se han compartido nombres, apellidos ni registros personales reales con la herramienta de inteligencia artificial. Las pruebas automatizadas se han realizado utilizando datos ficticios.