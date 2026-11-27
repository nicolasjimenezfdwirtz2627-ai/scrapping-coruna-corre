""" Rutas e constantes. """
from pathlib import Path

# Rutas base relativas á raíz do proxecto
ROOT_DIR = Path(__file__).resolve().parents[2]
INTERIM_DIR = ROOT_DIR / "datos" / "interim"
EXTERNAL_DIR = ROOT_DIR / "datos" / "external"

# Esquemas finais esixidos polo Contrato de Datos
COLS_CARREIRA_CLEAN = [
    "p_absoluto",
    "dorsal",
    "nome",
    "apelidos",
    "sexo",
    "p_sexo",
    "categoria",
    "p_categoria",
    "tempo",
]

COLS_INSCRITOS_CLEAN = ["nome", "apelidos", "dorsal"]
COLS_CARREIRAS_CLEAN = ["orde", "nome", "fecha"]

# Limiares razoables para detección de valores imposibles (en segundos)
TEMPO_MIN_SEGUNDOS = 600     # 10 min
TEMPO_MAX_SEGUNDOS = 14400   # 4 horas