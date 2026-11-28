""" Tests unitarios e de integracion para o modulo src.limpeza """

import numpy as np
import pandas as pd
import pytest

from src.limpeza.config import (
    COLS_CARREIRA_CLEAN,
    COLS_CARREIRAS_CLEAN,
    COLS_INSCRITOS_CLEAN,
)
from src.limpeza.limpador import (
    executar_pipeline_limpeza,
    limpar_carreira,
    limpar_carreiras_meta,
    limpar_inscritos,
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
from src.limpeza.perfilado import auditar_taboa_clean, perfilar_carreira


# --- TESTS DE NORMALIZADORES ---


def test_normalizar_texto():
    assert normalizar_texto("  José   Mª  Álvarez  ") == "JOSE Mª ALVAREZ"
    assert normalizar_texto("Ñoño") == "NONO"
    assert normalizar_texto("") is None
    assert normalizar_texto("   ") is None
    assert normalizar_texto(None) is None
    assert normalizar_texto(np.nan) is None


def test_normalizar_dorsal():
    assert normalizar_dorsal("104.0") == "104"
    assert normalizar_dorsal(104.0) == "104"
    assert normalizar_dorsal("  0045 ") == "0045"
    assert normalizar_dorsal("nan") is None
    assert normalizar_dorsal("None") is None
    assert normalizar_dorsal("") is None
    assert normalizar_dorsal(np.nan) is None


def test_separar_posto_sexo():
    assert separar_posto_sexo("M-3") == ("M", 3)
    assert separar_posto_sexo(" f - 12 ") == ("F", 12)
    assert separar_posto_sexo("M") == ("M", None)
    assert separar_posto_sexo("") == (None, None)
    assert separar_posto_sexo(np.nan) == (None, None)


def test_separar_posto_categoria():
    assert separar_posto_categoria("MS2M-1") == ("MS2M", "M", 1)
    assert separar_posto_categoria("SUB-23F-4") == ("SUB-23F", "F", 4)
    assert separar_posto_categoria("ESPECIAL-2") == ("ESPECIAL", None, 2)
    assert separar_posto_categoria("SEN CATEGORIA") == ("SEN CATEGORIA", None, None)
    assert separar_posto_categoria(np.nan) == (None, None, None)


def test_normalizar_categoria_especial():
    assert normalizar_categoria_especial("Diversidad Funcional") == "ESPECIAL"
    assert normalizar_categoria_especial("Especial") == "ESPECIAL"
    assert normalizar_categoria_especial("Sin categoría") == "SEN CATEGORIA"
    assert normalizar_categoria_especial("") == "SEN CATEGORIA"
    assert normalizar_categoria_especial(None) == "SEN CATEGORIA"
    assert normalizar_categoria_especial("snrm") == "SNRM"


def test_tempo_a_segundos():
    assert tempo_a_segundos("00:20:30") == (1230.0, "VALIDO")
    assert tempo_a_segundos("35:10") == (2110.0, "VALIDO")
    assert tempo_a_segundos("DNF") == (np.nan, "FALTANTE")
    assert tempo_a_segundos("--:--") == (np.nan, "FALTANTE")
    assert tempo_a_segundos(np.nan) == (np.nan, "FALTANTE")
    # Tempos fora de rango (imposibles) devólvense como NaN sen borrar a fila
    seg_baixo, est_baixo = tempo_a_segundos("00:01:30")
    assert np.isnan(seg_baixo) and est_baixo == "IMPOSIBLE"
    seg_alto, est_alto = tempo_a_segundos("05:00:00")
    assert np.isnan(seg_alto) and est_alto == "IMPOSIBLE"
    # Formato invalido
    seg_inv, est_inv = tempo_a_segundos("00:75:00")
    assert np.isnan(seg_inv) and est_inv == "FORMATO_INVALIDO"


def test_normalizar_fecha():
    assert normalizar_fecha("2026-03-14") == "14/03/2026"
    assert normalizar_fecha("14-03-2026") == "14/03/2026"
    assert normalizar_fecha("14/03/2026") == "14/03/2026"
    assert normalizar_fecha("") is None
    assert normalizar_fecha(np.nan) is None


# --- TESTS DE LIMPADOR E CONTRATO DE DATOS ---


def test_limpar_carreira_contrato():
    df_raw = pd.DataFrame({
        "puesto": [1, 2, 2, 3],
        "dorsal": ["101.0", "202", "202", "303"],
        "nome": ["  Ángel ", "María", "MARIA", "Luis"],
        "apelidos": ["Pérez  López", "Gómez", "GOMEZ", "Ruiz"],
        "p_sexo": ["M-1", None, None, None],
        "p_categoria": ["SNRM-1", "MS1F-1", "MS1F-1", "ESPECIAL-1"],
        "tempo": ["00:20:30", "00:25:00", "00:25:00", "00:00:10"],
    })

    df_clean = limpar_carreira(df_raw)

    # Cumpre estritamente coas columnas do contrato (sen tempo_estado)
    assert list(df_clean.columns) == COLS_CARREIRA_CLEAN
    # Eliminou o duplicado tras normalizar 'María' -> 'MARIA'
    assert len(df_clean) == 3
    # Rescatou o sexo 'F' dende p_categoria='MS1F-1'
    assert df_clean.loc[1, "sexo"] == "F"
    assert df_clean.loc[1, "p_categoria"] == 1
    # Na categoria ESPECIAL manteve sexo como nulo e tempo imposible como NaN sen borrar fila
    assert pd.isna(df_clean.loc[2, "sexo"])
    assert pd.isna(df_clean.loc[2, "tempo"])


def test_limpar_inscritos_e_carreiras_meta():
    df_ins_raw = pd.DataFrame({
        "nome": ["Ana", "ANA"],
        "apelidos": ["García", "GARCIA"],
        "dorsal": [55.0, "55"],
        "extra": ["ignorar", "ignorar"],
    })
    df_ins_clean = limpar_inscritos(df_ins_raw)
    assert list(df_ins_clean.columns) == COLS_INSCRITOS_CLEAN
    assert len(df_ins_clean) == 1
    assert df_ins_clean.loc[0, "dorsal"] == "55"

    df_car_raw = pd.DataFrame({
        "orde": ["1"],
        "nome": ["  Carreira   Torre de Hércules "],
        "fecha": ["2026-03-14"],
    })
    df_car_clean = limpar_carreiras_meta(df_car_raw)
    assert list(df_car_clean.columns) == COLS_CARREIRAS_CLEAN
    assert df_car_clean.loc[0, "nome"] == "CARREIRA TORRE DE HERCULES"
    assert df_car_clean.loc[0, "fecha"] == "14/03/2026"


def test_pipeline_e_auditoria_completa(tmp_path):
    interim = tmp_path / "interim"
    external = tmp_path / "external"
    interim.mkdir()

    pd.DataFrame({
        "puesto": [1],
        "dorsal": ["10"],
        "nome": ["Antón"],
        "apelidos": ["Gómez"],
        "p_sexo": ["M-1"],
        "p_categoria": ["SNRM-1"],
        "tempo": ["00:21:44"],
    }).to_csv(interim / "carreira_01_raw.csv", index=False)

    executar_pipeline_limpeza(interim, external)

    ruta_saida = external / "carreira_01_clean.csv"
    assert ruta_saida.exists()

    taboa_tipos, erros = auditar_taboa_clean(ruta_saida)
    assert erros == []
    assert list(taboa_tipos["Columna"]) == COLS_CARREIRA_CLEAN