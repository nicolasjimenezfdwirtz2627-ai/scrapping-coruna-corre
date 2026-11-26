""" Punto de entrada """

from src.limpeza.config import EXTERNAL_DIR, INTERIM_DIR
from src.limpeza.limpador import executar_pipeline_limpeza

if __name__ == "__main__":
    executar_pipeline_limpeza(INTERIM_DIR, EXTERNAL_DIR)
    print(f"Limpeza completada. Arquivos gardados en: {EXTERNAL_DIR}")