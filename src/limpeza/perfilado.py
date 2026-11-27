""" Funcions con pandas para detectar nulos, duplicados, formatos erroneos e validar o contrato sen exponer nomes """

from pathlib import Path
import pandas as pd
from src.limpeza.config import (
    COLS_CARREIRA_CLEAN,
    COLS_CARREIRAS_CLEAN,
    COLS_INSCRITOS_CLEAN,
    TEMPO_MAX_SEGUNDOS,
    TEMPO_MIN_SEGUNDOS,
)
from src.limpeza.normalizadores import normalizar_texto, tempo_a_segundos


def perfilar_carreira(df: pd.DataFrame, nome_arquivo: str) -> dict:
    """
    Analiza a calidade dunha carreira antes da limpeza sen exponer datos persoais (RGPD).
    """
    n_filas = len(df)
    nulos_por_col = df.isna().sum().to_dict()
    dup_filas = int(df.duplicated().sum())
    dup_dorsal = int(df["dorsal"].dropna().duplicated().sum()) if "dorsal" in df.columns else 0

    estados_tempo = (
        df["tempo"]
        .apply(lambda x: tempo_a_segundos(x, TEMPO_MIN_SEGUNDOS, TEMPO_MAX_SEGUNDOS)[1])
        .value_counts()
        .to_dict()
    )

    nomes_non_norm = 0
    for col in ("nome", "apelidos"):
        if col in df.columns:
            nomes_non_norm += int(
                df[col].dropna().apply(lambda x: str(x) != normalizar_texto(x)).sum()
            )

    return {
        "arquivo": nome_arquivo,
        "total_filas": n_filas,
        "nulos": nulos_por_col,
        "duplicados_exactos": dup_filas,
        "dorsais_duplicados": dup_dorsal,
        "estados_tempo": estados_tempo,
        "textos_sen_normalizar": nomes_non_norm,
    }


def xerar_resumo_calidade(perfis: list[dict]) -> pd.DataFrame:
    """Converte a lista de perfis nun DataFrame seguro para mostrar no notebook."""
    filas = []
    for p in perfis:
        filas.append({
            "arquivo": p["arquivo"],
            "filas": p["total_filas"],
            "dup_exactos": p["duplicados_exactos"],
            "dup_dorsal": p["dorsais_duplicados"],
            "tempos_validos": p["estados_tempo"].get("VALIDO", 0),
            "tempos_faltantes": p["estados_tempo"].get("FALTANTE", 0),
            "tempos_imposibles": p["estados_tempo"].get("IMPOSIBLE", 0),
            "tempos_fmt_invalido": p["estados_tempo"].get("FORMATO_INVALIDO", 0),
            "textos_sen_normalizar": p["textos_sen_normalizar"],
        })
    return pd.DataFrame(filas)


def auditar_taboa_clean(ruta_csv: Path) -> tuple[pd.DataFrame, list[str]]:
    """
    Verifica un CSV limpo de datos/external contra o Contrato de Datos:
    - Exactitude de columnas e orde (sen columnas extra).
    - Tipos de datos (dtypes) esperados.
    - Nulos reais e baleiros ocultos ('', 'nan', espazos dobres, tildes).
    - Rangos validos en tempos e formato dd/mm/yyyy en datas.
    """
    nome_arq = ruta_csv.name
    erros: list[str] = []

    if nome_arq == "inscritos_clean.csv":
        cols_esperadas = COLS_INSCRITOS_CLEAN
        tipos_esperados = {"nome": "string", "apelidos": "string", "dorsal": "string"}
    elif nome_arq == "carreiras_clean.csv":
        cols_esperadas = COLS_CARREIRAS_CLEAN
        tipos_esperados = {"orde": "Int64", "nome": "string", "fecha": "string"}
    else:
        cols_esperadas = COLS_CARREIRA_CLEAN
        tipos_esperados = {
            "p_absoluto": "Int64",
            "dorsal": "string",
            "nome": "string",
            "apelidos": "string",
            "sexo": "string",
            "p_sexo": "Int64",
            "categoria": "string",
            "p_categoria": "Int64",
            "tempo": "float64",
        }

    # Lectura tipada segundo contrato
    df = pd.read_csv(ruta_csv, dtype={"dorsal": "string"})
    for col, tipo in tipos_esperados.items():
        if col in df.columns:
            if tipo == "Int64":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            elif tipo == "float64":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            elif tipo == "string":
                df[col] = df[col].astype("string")

    # 1. Validacion de esquema do contrato
    if list(df.columns) != cols_esperadas:
        erros.append(f"Esquema non coincide co contrato. Esperado: {cols_esperadas} | Actual: {list(df.columns)}")

    # 2. Validacion de duplicados exactos
    dups = int(df.duplicated().sum())
    if dups > 0:
        erros.append(f"Atopáronse {dups} filas duplicadas.")

    # 3. Validacion de normalizacion de texto e ausencia de 'nan' literal
    for col in ("nome", "apelidos", "categoria", "sexo"):
        if col in df.columns:
            serie = df[col].dropna()
            non_norm = serie[serie.apply(lambda x: str(x) != normalizar_texto(x))]
            if len(non_norm) > 0:
                erros.append(f"Columna '{col}' ten {len(non_norm)} valores sen normalizar (tildes, minúsculas ou espazos).")

    if "dorsal" in df.columns:
        dorsais_lixo = df["dorsal"].dropna()
        dorsais_lixo = dorsais_lixo[dorsais_lixo.str.lower().isin({"nan", "none", ""}) | dorsais_lixo.str.endswith(".0")]
        if len(dorsais_lixo) > 0:
            erros.append(f"Columna 'dorsal' contén {len(dorsais_lixo)} valores mal formateados.")

    # 4. Validacion de tempos (sen valores imposibles)
    if "tempo" in df.columns:
        tempos_validos = df["tempo"].dropna()
        fora_rango = tempos_validos[(tempos_validos < TEMPO_MIN_SEGUNDOS) | (tempos_validos > TEMPO_MAX_SEGUNDOS)]
        if len(fora_rango) > 0:
            erros.append(f"Columna 'tempo' contén {len(fora_rango)} valores fóra de rango [{TEMPO_MIN_SEGUNDOS}s, {TEMPO_MAX_SEGUNDOS}s].")

    # 5. Validacion de formato de data dd/mm/yyyy
    if "fecha" in df.columns:
        datas = df["fecha"].dropna()
        datas_mal = datas[~datas.str.match(r"^\d{2}/\d{2}/\d{4}$")]
        if len(datas_mal) > 0:
            erros.append(f"Columna 'fecha' ten {len(datas_mal)} datas que non cumpren dd/mm/yyyy.")

    # 6. Taboa resumo de tipos e nulos
    taboa_tipos = pd.DataFrame({
        "Columna": df.columns,
        "Tipo (dtype)": [str(df[c].dtype) for c in df.columns],
        "Non nulos": [int(df[c].notna().sum()) for c in df.columns],
        "Nulos (NaN)": [int(df[c].isna().sum()) for c in df.columns],
        "Unicos": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })

    return taboa_tipos, erros