""" Funcións puras para textos, tempos, datas,
separación de columnas mesturadas e categorías especiais. """

import re
import unicodedata
from datetime import datetime
import numpy as np
import pandas as pd


def normalizar_texto(texto: object) -> str | None:
    """
    Converte a MAIÚSCULAS, elimina tildes/diacríticos e colapsa espazos dobres.
    Cumpre estritamente co Contrato de Datos para nome, apelidos e nomes de carreira.
    """
    if pd.isna(texto) or str(texto).strip() == "":
        return None
    s = str(texto).strip().upper()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"\s+", " ", s)
    return s


def normalizar_dorsal(valor: object) -> str | None:
    """
    Limpa o dorsal evitando cadeas 'nan', 'None' ou sufixos decimais '.0'.
    """
    if pd.isna(valor):
        return None
    s = str(valor).strip()
    if s.lower() in {"", "nan", "none", "null", "na"}:
        return None
    s = re.sub(r"\.0$", "", s)
    return s


def separar_posto_sexo(valor: object) -> tuple[str | None, int | None]:
    """
    Separa valores tipo 'M-3' ou 'F-12' en (sexo='M', p_sexo=3).
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return None, None
    s = str(valor).strip().upper()
    match = re.match(r"^([A-Z]+)\s*-\s*(\d+)$", s)
    if match:
        return match.group(1), int(match.group(2))
    if s in {"M", "F", "H", "X"}:
        return s, None
    return None, None


def separar_posto_categoria(valor: object) -> tuple[str | None, str | None, int | None]:
    """
    Separa valores tipo 'MS2M-1', 'SUB-23F-4' ou 'ESPECIAL-2' en (categoria, sexo, p_categoria).
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return None, None, None
    s = normalizar_texto(valor)

    # Caso estándar: código de categoría (incluso con guións internos) rematado en M ou F + posto
    match_std = re.match(r"^([A-Z0-9\s\-]+?)([MF])\s*-\s*(\d+)$", s)
    if match_std:
        cat_completa = f"{match_std.group(1).strip()}{match_std.group(2)}"
        sexo_cat = match_std.group(2)
        posto = int(match_std.group(3))
        return cat_completa, sexo_cat, posto

    # Caso categoría especial con guión e posto (ex: ESPECIAL-1)
    match_esp = re.match(r"^([A-Z0-9\s\-]+?)\s*-\s*(\d+)$", s)
    if match_esp:
        return match_esp.group(1).strip(), None, int(match_esp.group(2))

    # Caso texto sen posto (ex: 'SEN CATEGORIA', 'ESPECIAL')
    return s, None, None


def normalizar_categoria_especial(cat: object) -> str:
    """
    Unifica variantes de categorías especiais ou sen categoría sen descartar filas.
    """
    if pd.isna(cat) or str(cat).strip() == "":
        return "SEN CATEGORIA"
    s = normalizar_texto(cat)
    if "ESPECIAL" in s or "DIVERSIDAD" in s or "DISCAPAC" in s:
        return "ESPECIAL"
    if "SEN" in s or "SIN" in s or s in {"NONE", "NAN", "-"}:
        return "SEN CATEGORIA"
    return s


def tempo_a_segundos(valor: object, min_s: int = 600, max_s: int = 14400) -> tuple[float, str]:
    """
    Converte tempos en formato 'HH:MM:SS' ou 'MM:SS' a segundos (float).
    Devolve (segundos_ou_NaN, estado_interno_para_perfilado).
    Os rexistros faltantes, inválidos ou imposibles devólvense como np.nan para non distorsionar métricas.
    """
    if pd.isna(valor) or str(valor).strip().upper() in {"", "-", "--:--", "--:--:--", "DNF", "DNS", "DSQ", "NAN", "NONE"}:
        return np.nan, "FALTANTE"

    s = str(valor).strip()
    partes = s.split(":")
    try:
        if len(partes) == 3:
            horas, minutos, segundos = float(partes[0]), float(partes[1]), float(partes[2])
            if minutos >= 60 or segundos >= 60 or horas < 0 or minutos < 0 or segundos < 0:
                return np.nan, "FORMATO_INVALIDO"
            total = horas * 3600 + minutos * 60 + segundos
        elif len(partes) == 2:
            minutos, segundos = float(partes[0]), float(partes[1])
            if segundos >= 60 or minutos < 0 or segundos < 0:
                return np.nan, "FORMATO_INVALIDO"
            total = minutos * 60 + segundos
        elif len(partes) == 1:
            total = float(partes[0])
        else:
            return np.nan, "FORMATO_INVALIDO"
    except ValueError:
        return np.nan, "FORMATO_INVALIDO"

    if pd.isna(total) or total <= 0 or total < min_s or total > max_s:
        return np.nan, "IMPOSIBLE"

    return round(total, 2), "VALIDO"


def normalizar_fecha(valor: object) -> str | None:
    """
    Converte distintas representacións de data ao formato estrito dd/mm/yyyy.
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    s = str(valor).strip()
    formatos = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")
    for fmt in formatos:
        try:
            return datetime.strptime(s[:10], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.notna(dt):
        return dt.strftime("%d/%m/%Y")
    return None