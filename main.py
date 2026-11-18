from config.imports import *
from config.settings import PDF_FOLDER
from database.db_manager import crear_tabla, guardar_factura
from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.image_ocr import extraer_texto_imagen
from extractors.cleaner import limpiar_texto, extraer_patrones
from extractors.regex_extractor import completar_campos_no_legibles, extraer_con_regex
from models.factura import Factura

def procesar_pdf(ruta_pdf):
    nombre = os.path.basename(ruta_pdf)
    print(f"\nProcesando: {nombre}")

    if ruta_pdf.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):

        print("Tipo: imagen -> OCR local")
        tipo = "imagen"
        texto_crudo = extraer_texto_imagen(ruta_pdf)

    elif es_pdf_escaneado(ruta_pdf):

        print("Tipo: escaneado -> OCR local")
        tipo = "escaneado"
        texto_crudo = extraer_texto_ocr(ruta_pdf)

    else:

        print("Tipo: digital -> extracción local")
        tipo = "digital"
        texto_crudo = extraer_texto_pdf(ruta_pdf)

    texto_limpio = limpiar_texto(texto_crudo)

    datos = extraer_con_regex(texto_limpio.upper())
    respaldo = extraer_patrones(texto_limpio)
    for campo in ("banco", "proveedor"):
        if not datos.get(campo) and respaldo.get(campo):
            datos[campo] = respaldo[campo]
    datos = completar_campos_no_legibles(datos)

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio,
        banco=datos["banco"],
        total=datos["total"],
        fecha=datos["fecha"],
        proveedor=datos["proveedor"],
        nit_proveedor=datos.get("nit_proveedor") or datos.get("nit", ""),
        estado_transaccion=datos["estado_transaccion"],
        hora=datos["hora"],
        referencia=datos["referencia"],
        numero_autorizacion=datos["numero_autorizacion"],
        punto_recaudo=datos["punto_recaudo"]
    )

    guardar_factura(
        factura.nombre_archivo,
        factura.tipo_pdf,
        factura.texto_extraido,
        factura.banco,
        factura.total,
        factura.fecha,
        factura.proveedor,
        nit_proveedor=factura.nit_proveedor,
        estado_transaccion=factura.estado_transaccion,
        hora=factura.hora,
        referencia=factura.referencia,
        numero_autorizacion=factura.numero_autorizacion,
        punto_recaudo=factura.punto_recaudo
    )

    print(f"Proveedor : {factura.proveedor or 'No detectado'}")
    print(f"Banco     : {factura.banco     or 'No detectado'}")
    print(f"Total     : {factura.total     or 'No detectado'}")
    print(f"Fecha     : {factura.fecha     or 'No detectada'}")
    return factura


def main():
    print("Iniciando procesamiento de facturas...\n")

    crear_tabla()
    os.makedirs(PDF_FOLDER, exist_ok=True)

    archivos_pdf = [
        f for f in os.listdir(PDF_FOLDER)
        if f.lower().endswith(
            (".pdf", ".jpg", ".jpeg", ".png", ".webp")
        )
    ]

    if not archivos_pdf:
        print(f"No hay PDFs en la carpeta: {PDF_FOLDER}")
        print("Mete tus archivos PDF en esa carpeta y vuelve a correr el programa.")
        return

    print(f"Se encontraron {len(archivos_pdf)} PDF(s) para procesar.\n")

    for archivo in archivos_pdf:
        ruta_completa = os.path.join(PDF_FOLDER, archivo)
        procesar_pdf(ruta_completa)

    print(f"\nListo! {len(archivos_pdf)} factura(s) procesada(s) y guardada(s).")
    print("Ahora corre 'python web/app.py' para ver la visualizacion web.\n")


if __name__ == "__main__":
    main()
