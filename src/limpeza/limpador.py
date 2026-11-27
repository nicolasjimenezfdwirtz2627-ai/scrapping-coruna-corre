""" Orquestra a limpeza das carreiras, inscritos_raw.csv e carreiras_raw.csv segundo o contrato """

from pathlib import Path
import pandas as pd
from src.limpeza.config import (
    COLS_CARREIRA_CLEAN,
    COLS_CARREIRAS_CLEAN,
    COLS_INSCRITOS_CLEAN,
    TEMPO_MAX_SEGUNDOS,
    TEMPO_MIN_SEGUNDOS,
)
from src.limpeza.normalizadores import (
    normalizar_categoria_especial,
    normalizar_dorsal,
    normalizar_fecha,
    normalizar_texto,
    separar_posto_categoria,
    separar_posto_sexo,
    tempo_a_segundos,
)


def limpar_carreira(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Limpa e normaliza o DataFrame dunha carreira individual segundo o contrato."""
    df = df_raw.copy()

    # 1. Renomear 'puesto' a 'p_absoluto' se vén co nome de descarga
    if "puesto" in df.columns and "p_absoluto" not in df.columns:
        df = df.rename(columns={"puesto": "p_absoluto"})

    df["p_absoluto"] = pd.to_numeric(df["p_absoluto"], errors="coerce").astype("Int64")
    df["dorsal"] = df["dorsal"].apply(normalizar_dorsal)

    # 2. Normalización de nome e apelidos (MAIÚSCULAS, sen tildes, sen dobles espazos)
    df["nome"] = df["nome"].apply(normalizar_texto)
    df["apelidos"] = df["apelidos"].apply(normalizar_texto)

    # 3. Separar columna p_sexo (ex: 'M-3' -> sexo='M', p_sexo=3)
    if "p_sexo" in df.columns:
        res_sexo = df["p_sexo"].apply(separar_posto_sexo)
        df["sexo"] = res_sexo.apply(lambda t: t[0])
        df["p_sexo"] = pd.to_numeric(res_sexo.apply(lambda t: t[1]), errors="coerce").astype("Int64")
    else:
        df["sexo"] = None
        df["p_sexo"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    # 4. Separar columna p_categoria (ex: 'MS2M-1')
    if "p_categoria" in df.columns:
        res_cat = df["p_categoria"].apply(separar_posto_categoria)
        df["categoria"] = res_cat.apply(lambda t: normalizar_categoria_especial(t[0]))
        sexo_cat = res_cat.apply(lambda t: t[1])
        df["sexo"] = df["sexo"].fillna(sexo_cat)
        df["p_categoria"] = pd.to_numeric(res_cat.apply(lambda t: t[2]), errors="coerce").astype("Int64")
    else:
        df["categoria"] = "SEN CATEGORIA"
        df["p_categoria"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    df["sexo"] = df["sexo"].apply(lambda x: x.upper() if pd.notna(x) else None)

    # 5. Conversión de tempos a segundos (faltantes/imposibles quedan como NaN sen borrar a fila)
    df["tempo"] = df["tempo"].apply(
        lambda x: tempo_a_segundos(x, TEMPO_MIN_SEGUNDOS, TEMPO_MAX_SEGUNDOS)[0]
    ).astype("float64")

    # 6. Eliminar filas completamente baleiras e duplicados estritos despois de normalizar
    df = df[COLS_CARREIRA_CLEAN].dropna(how="all").drop_duplicates().reset_index(drop=True)
    return df


def limpar_inscritos(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Limpa inscritos_raw.csv -> inscritos_clean.csv."""
    df = df_raw.copy()
    df["nome"] = df["nome"].apply(normalizar_texto)
    df["apelidos"] = df["apelidos"].apply(normalizar_texto)
    df["dorsal"] = df["dorsal"].apply(normalizar_dorsal)
    df = df[COLS_INSCRITOS_CLEAN].dropna(how="all").drop_duplicates().reset_index(drop=True)
    return df


def limpar_carreiras_meta(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Limpa carreiras_raw.csv -> carreiras_clean.csv (fecha dd/mm/yyyy)."""
    df = df_raw.copy()
    df["orde"] = pd.to_numeric(df["orde"], errors="coerce").astype("Int64")
    df["nome"] = df["nome"].apply(normalizar_texto)
    df["fecha"] = df["fecha"].apply(normalizar_fecha)
    df = df[COLS_CARREIRAS_CLEAN].dropna(how="all").drop_duplicates().reset_index(drop=True)
    return df


def executar_pipeline_limpeza(interim_dir: Path, external_dir: Path) -> None:
    """Le de datos/interim, limpa todos os CSVs e gárdaos en datos/external."""
    external_dir.mkdir(parents=True, exist_ok=True)

    # 1. Inscritos
    ruta_inscritos = interim_dir / "inscritos_raw.csv"
    if ruta_inscritos.exists():
        df_ins = pd.read_csv(ruta_inscritos, dtype={"dorsal": str})
        limpar_inscritos(df_ins).to_csv(external_dir / "inscritos_clean.csv", index=False)

    # 2. Metadatos das carreiras
    ruta_carreiras = interim_dir / "carreiras_raw.csv"
    if ruta_carreiras.exists():
        df_car = pd.read_csv(ruta_carreiras)
        limpar_carreiras_meta(df_car).to_csv(external_dir / "carreiras_clean.csv", index=False)

    # 3. Resultados de cada carreira (todos os CSVs agás inscritos e carreiras)
    excluidos = {"inscritos_raw.csv", "carreiras_raw.csv"}
    for arquivo in sorted(interim_dir.glob("*.csv")):
        if arquivo.name in excluidos:
            continue
        df_raw = pd.read_csv(arquivo, dtype={"dorsal": str})
        df_clean = limpar_carreira(df_raw)
        nome_saida = arquivo.name.replace("_raw", "_clean")
        if nome_saida == arquivo.name:
            nome_saida = f"{arquivo.stem}_clean.csv"
        df_clean.to_csv(external_dir / nome_saida, index=False)