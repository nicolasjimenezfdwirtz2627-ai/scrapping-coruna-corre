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
