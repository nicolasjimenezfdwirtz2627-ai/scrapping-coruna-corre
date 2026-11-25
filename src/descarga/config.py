from pathlib import Path

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parents[2]

RAW = RAIZ / "datos" / "raw"
INTERIM = RAIZ / "datos" / "interim"

# Configuración de la web
URL_BASE = "https://corunacorre.com/"
URL_EDICION = "https://corunacorre.com/es/web/resultado/edicion-63"
URL_INSCRITOS = "https://corunacorre.com/es/web/inscripcion/listado/"
URL_ROBOTS = URL_BASE + "robots.txt"

# Configuración de las peticiones HTTP
USER_AGENT = "ProyectoAcademico-CorunaCorre-IESFernandoWirtz/1.0"

CABECERAS = {
    "User-Agent": USER_AGENT
}

PAUSA = 1.5
TIMEOUT = 20

# Alcance del proyecto
NUM_CARREIRAS = 6