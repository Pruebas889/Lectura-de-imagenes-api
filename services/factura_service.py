import os
import shutil
import tempfile
import uuid

from pdf2image import convert_from_path

from config.settings import DOCUMENT_FOLDER, GROQ_API_KEY, POPPLER_PATH

from extractors.image_ocr import extraer_texto_imagen

from database.db_manager import guardar_factura

from extractors.pdf_text import extraer_texto_pdf
from extractors.pdf_ocr import extraer_texto_ocr, es_pdf_escaneado
from extractors.cleaner import limpiar_texto, extraer_patrones
from extractors.regex_extractor import extraer_con_regex
from extractors.ai_extractor import (
    GroqQuotaExceeded,
    extraer_con_ia_desde_imagen,
    es_imagen
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
    for campo in ("total", "fecha", "banco", "proveedor"):
        if not datos.get(campo) and respaldo.get(campo):
            datos[campo] = respaldo[campo]
    return datos


def _completar_con_vision(ruta: str, datos: dict) -> tuple[dict, bool]:
    if _tiene_datos(datos) or not GROQ_API_KEY:
        return datos, False

    try:
        datos_vision = extraer_con_ia_desde_imagen(ruta, datos)
        return {**datos, **{k: v for k, v in datos_vision.items() if v}}, False
    except GroqQuotaExceeded as error:
        print(f"[Groq] {error} Se conserva el resultado local.")
        return datos, True


def _procesar_archivo(ruta: str, nombre: str) -> Factura:
    ext = os.path.splitext(nombre)[1].lower()
    advertencia_cuota_groq = False

    if es_imagen(nombre):
        tipo = "imagen"
        print("Imagen detectada -> Tesseract OCR y extracción local...")
        texto_crudo = extraer_texto_imagen(ruta)
        texto_limpio = limpiar_texto(texto_crudo)
        datos = extraer_con_regex(texto_limpio.upper())
        datos = _completar_con_patrones(datos, texto_limpio)
        datos, advertencia_cuota_groq = _completar_con_vision(ruta, datos)
    elif ext == ".pdf":
        if es_pdf_escaneado(ruta):
            tipo = "escaneado"
            print("PDF escaneado -> Tesseract OCR y extracción local...")
            texto_crudo = extraer_texto_ocr(ruta)
            texto_limpio = limpiar_texto(texto_crudo)
            datos = extraer_con_regex(texto_limpio.upper())
            datos = _completar_con_patrones(datos, texto_limpio)
            if not _tiene_datos(datos) and GROQ_API_KEY:
                paginas = convert_from_path(
                    ruta,
                    dpi=150,
                    first_page=1,
                    last_page=1,
                    poppler_path=POPPLER_PATH
                )
                try:
                    if paginas:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                            ruta_img_tmp = tmp_img.name
                        try:
                            paginas[0].save(ruta_img_tmp, "PNG")
                            datos, advertencia_cuota_groq = _completar_con_vision(
                                ruta_img_tmp,
                                datos
                            )
                        finally:
                            if os.path.exists(ruta_img_tmp):
                                os.unlink(ruta_img_tmp)
                finally:
                    for pagina in paginas:
                        pagina.close()
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

    if not _tiene_datos(datos):
        raise RuntimeError(
            "No se pudieron extraer datos del documento. Verifica la calidad del archivo "
            "y que Tesseract esté instalado y configurado."
        )

    factura = Factura(
        nombre_archivo=nombre,
        tipo_pdf=tipo,
        texto_extraido=texto_limpio,
        banco=datos.get("banco", ""),
        total=datos.get("total", ""),
        fecha=datos.get("fecha", ""),
        proveedor=datos.get("proveedor", ""),
        advertencia_cuota_groq=advertencia_cuota_groq,
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