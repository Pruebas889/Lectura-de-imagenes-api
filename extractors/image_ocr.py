from PIL import Image
import os

from extractors.image_preprocessor import procesar_imagen_fotografia
from extractors.ocr_utils import (
    calidad_texto_ocr,
    extraer_texto_por_variantes,
    validar_tesseract
)


def extraer_texto_imagen(ruta_imagen):
    """
    Extrae texto de imagen fotográfica SIN dividir en bloques.
    Procesamiento COMPLETO de la imagen:
    1. Preprocesar (rotación + filtro básico)
    2. OCR directo con Tesseract
    
    Este método es MÁS FIABLE porque:
    - No divide la imagen (evita pérdida de contexto)
    - Mantiene la relación espacial de los datos
    - OCR trabaja con imagen completa
    """

    print("=" * 60)
    print("EXTRAYENDO TEXTO DE IMAGEN - PROCESAMIENTO COMPLETO")
    print("=" * 60)
    validar_tesseract()

    ruta_procesada = None
    try:
        with Image.open(ruta_imagen) as imagen:
            texto_completo = extraer_texto_por_variantes(
                imagen,
                modos_segmentacion=(11, 6, 4),
                escala=2
            )

        puntaje_texto = calidad_texto_ocr(texto_completo)
        if puntaje_texto[0] < 14 or puntaje_texto[1] < 120:
            ruta_procesada = procesar_imagen_fotografia(ruta_imagen)
            with Image.open(ruta_procesada) as imagen_procesada:
                texto_procesado = extraer_texto_por_variantes(
                    imagen_procesada,
                    modos_segmentacion=(11, 6, 4),
                    escala=2
                )
            if calidad_texto_ocr(texto_procesado) > puntaje_texto:
                texto_completo = texto_procesado
        
        texto_completo = texto_completo.strip()
        caracteres = len(texto_completo)
        print(f"[image_ocr] OCR completado ({caracteres} caracteres)")
        
        return texto_completo
    except RuntimeError:
        raise
    except Exception as e:
        print(f"[image_ocr] ERROR en OCR de imagen: {e}")
        raise RuntimeError(f"Fallo el procesamiento OCR de la imagen: {e}") from e
    finally:
        if ruta_procesada and os.path.exists(ruta_procesada):
            os.remove(ruta_procesada)