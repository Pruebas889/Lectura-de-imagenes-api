import os
import shutil
import uuid

from config.settings import DOCUMENT_FOLDER

from extractors.image_ocr import extraer_texto_imagen

from database.db_manager import guardar_factura

from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner import limpiar_texto, extraer_patrones
from extractors.regex_extractor import (
    completar_campos_no_legibles,
    extraer_con_regex
)

from models.factura import Factura


def _tiene_datos(datos: dict) -> bool:
    campos = (
        "proveedor",
        "nit_proveedor",
        "nit",
        "total",
        "estado_transaccion",
        "fecha",
        "hora",
        "referencia",
        "numero_autorizacion",
        "punto_recaudo",
        "banco"
    )
    return any(datos.get(campo) for campo in campos)


def _completar_con_patrones(datos: dict, texto: str) -> dict:
    respaldo = extraer_patrones(texto)
    for campo in ("banco", "proveedor"):
        if not datos.get(campo) and respaldo.get(campo):
            datos[campo] = respaldo[campo]
    return datos


def _procesar_archivo(ruta: str, nombre: str) -> Factura:
    ext = os.path.splitext(nombre)[1].lower()

    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
        tipo = "imagen"
        print("Imagen detectada -> Tesseract OCR y extracción local...")
        texto_crudo = extraer_texto_imagen(ruta)
        texto_limpio = limpiar_texto(texto_crudo)
        datos = extraer_con_regex(texto_limpio.upper())
        datos = _completar_con_patrones(datos, texto_limpio)
    elif ext == ".pdf":
        if es_pdf_escaneado(ruta):
            tipo = "escaneado"
            print("PDF escaneado -> Tesseract OCR y extracción local...")
            texto_crudo = extraer_texto_ocr(ruta)
            texto_limpio = limpiar_texto(texto_crudo)
            datos = extraer_con_regex(texto_limpio.upper())
            datos = _completar_con_patrones(datos, texto_limpio)
        else:
            tipo = "digital"
            texto_crudo = extraer_texto_pdf(ruta)
            texto_limpio = limpiar_texto(texto_crudo)
            datos = extraer_con_regex(texto_limpio.upper())
            datos = _completar_con_patrones(datos, texto_limpio)
            if not _tiene_datos(datos):
                print("El texto del PDF no dio datos; se intenta OCR como respaldo...")
                texto_ocr = extraer_texto_ocr(ruta)
                texto_limpio = limpiar_texto(f"{texto_limpio}\n{texto_ocr}")
                datos = extraer_con_regex(texto_limpio.upper())
                datos = _completar_con_patrones(datos, texto_limpio)
    else:
        raise ValueError(
            f"Formato no soportado: {ext or '(sin extensión)'}. "
            "Usa PDF, JPG, PNG, WEBP, BMP o TIFF."
        )

    datos = completar_campos_no_legibles(datos)

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio,
        banco=datos.get("banco", ""),
        total=datos.get("total", ""),
        fecha=datos.get("fecha", ""),
        proveedor=datos.get("proveedor", ""),
        nit_proveedor=datos.get("nit_proveedor") or datos.get("nit", ""),
        estado_transaccion=datos.get("estado_transaccion", ""),
        hora=datos.get("hora", ""),
        referencia=datos.get("referencia", ""),
        numero_autorizacion=datos.get("numero_autorizacion", ""),
        punto_recaudo=datos.get("punto_recaudo", "")
    )

    archivo_original = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(DOCUMENT_FOLDER, exist_ok=True)
    ruta_original = os.path.join(DOCUMENT_FOLDER, archivo_original)
    shutil.copyfile(ruta, ruta_original)
    try:
        factura.id = guardar_factura(
            factura.nombre_archivo,
            factura.tipo_pdf,
            factura.texto_extraido,
            factura.banco,
            factura.total,
            factura.fecha,
            factura.proveedor,
            archivo_original,
            factura.nit_proveedor,
            factura.estado_transaccion,
            factura.hora,
            factura.referencia,
            factura.numero_autorizacion,
            factura.punto_recaudo
        )
    except Exception:
        os.unlink(ruta_original)
        raise
    return factura