from PIL import Image
import pytesseract
import os

from extractors.image_preprocessor import procesar_imagen_fotografia
from extractors.ocr_utils import validar_tesseract


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
        ruta_procesada = procesar_imagen_fotografia(ruta_imagen)
        
        if ruta_procesada is None:
            print("[image_ocr] ERROR: Preprocesamiento falló")
            raise RuntimeError("No se pudo preprocesar la imagen para OCR.")
        
        config_ocr = (
            "--oem 3 "
            "--psm 4 "
            "-l spa+eng "
            "-c preserve_interword_spaces=1 "
            "-c textord_heavy_nr=1"
        )
        
        try:
            with Image.open(ruta_procesada) as img_procesada:
                print(f"[image_ocr] Imagen procesada: {img_procesada.size}")
                texto_completo = pytesseract.image_to_string(
                    img_procesada,
                    config=config_ocr
                )
        except Exception as e:
            raise RuntimeError(f"No se pudo leer el texto de la imagen: {e}") from e
        
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