from services.factura_service import _procesar_archivo


def procesar_lote(lista_archivos):
    """
    Procesa una lista de archivos uno por uno utilizando
    exactamente el mismo motor del proyecto.

    lista_archivos debe contener tuplas:

        (ruta_archivo, nombre_archivo)

    Retorna una lista con todas las facturas procesadas.
    """

    resultados = []

    total = len(lista_archivos)

    print("=" * 70)
    print(f"INICIANDO PROCESAMIENTO MASIVO ({total} archivos)")
    print("=" * 70)

    for indice, (ruta, nombre) in enumerate(lista_archivos, start=1):

        print(f"\n[{indice}/{total}] Procesando: {nombre}")

        try:

            factura = _procesar_archivo(ruta, nombre)

            resultados.append(factura)

            print(f"✓ Finalizado: {nombre}")

        except Exception as e:

            print(f"✗ Error en {nombre}: {e}")

    print("\n" + "=" * 70)
    print("PROCESAMIENTO MASIVO FINALIZADO")
    print("=" * 70)

    return resultados