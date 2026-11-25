from .config import INTERIM, NUM_CARREIRAS

from .carreiras import (
    descubrir_carreiras,
    descubrir_absolutas,
    descargar_resultados,
    descargar_metadatos
)

from .inscritos import descargar_inscritos


def main():
    """Ejecuta el pipeline completo de descarga de Coruña Corre."""

    print("=" * 60)
    print("CORUÑA CORRE 2026 - DESCARGA DE DATOS")
    print("=" * 60)

    # 1. Descubrir las carreras
    carreiras = descubrir_carreiras()

    # 2. Localizar las categorías Absolutas
    carreiras = descubrir_absolutas(carreiras)

    if len(carreiras) != NUM_CARREIRAS:
        raise ValueError("Número incorrecto de carreras.")

    # 3. Descargar los resultados de cada carrera
    total_participacions = 0
    resumen = []

    for carreira in carreiras:

        df = descargar_resultados(carreira)

        total_participacions += len(df)

        resumen.append({
            "orde": carreira["orde"],
            "nome": carreira["nome"],
            "participacions": len(df)
        })

    # 4. Descargar los metadatos
    df_carreiras = descargar_metadatos(carreiras)

    # 5. Descargar los inscritos en el circuito
    df_inscritos = descargar_inscritos()

    # 6. Mostrar el resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL DEL PIPELINE")
    print("=" * 60)

    for carreira in resumen:
        print(
            f"{carreira['orde']}. "
            f"{carreira['nome']}: "
            f"{carreira['participacions']} participaciones"
        )

    print(f"\nCarreras procesadas: {len(df_carreiras)}")
    print(f"Participaciones totales: {total_participacions}")
    print(f"Inscritos en el circuito: {len(df_inscritos)}")
    print(f"Archivos CSV generados: {len(resumen) + 2}")
    print(f"Directorio de salida: {INTERIM}")

    print("\nDescarga completada correctamente.")


if __name__ == "__main__":
    main()