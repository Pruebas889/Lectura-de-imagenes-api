from config.imports import *
from config.settings import POPPLER_PATH
from pdf2image import pdfinfo_from_path
from extractors.ocr_utils import validar_tesseract


def extraer_texto_ocr(ruta_pdf):
    """
    Lee un PDF escaneado, convierte cada pagina en imagen y luego lee la imagen.
    Es util para recibos fisicos escaneados, facturas en papel, etc.
    """

    texto_completo = ""
    validar_tesseract()

    try:
        info_pdf = pdfinfo_from_path(ruta_pdf, poppler_path=POPPLER_PATH)
        total_paginas = int(info_pdf.get("Pages", 0))
        if total_paginas < 1:
            raise RuntimeError("El PDF no contiene páginas.")

        for numero_pagina in range(1, total_paginas + 1):
            print(f"Procesando pagina {numero_pagina} con OCR...")
            paginas = convert_from_path(
                ruta_pdf,
                dpi=200,
                first_page=numero_pagina,
                last_page=numero_pagina,
                poppler_path=POPPLER_PATH
            )
            if not paginas:
                continue

            imagen = paginas[0]
            imagen_ocr = None
            try:
                config_ocr = (
                    "--oem 3 "
                    "--psm 6 "
                    "-l spa+eng "
                    "-c preserve_interword_spaces=1 "
                    "-c textord_heavy_nr=1 "
                    "-c textord_min_linesize=2.5"
                )
                imagen_ocr = imagen.convert("L")
                texto = pytesseract.image_to_string(imagen_ocr, config=config_ocr)
            finally:
                if imagen_ocr is not None:
                    imagen_ocr.close()
                for pagina in paginas:
                    pagina.close()

            if texto.strip():
                texto_completo += f"\n--- Pagina {numero_pagina} (OCR) ---\n"
                texto_completo += texto
    except Exception as e:
        print(f"Error en OCR de {ruta_pdf}: {e}")
        raise RuntimeError(f"No se pudo convertir o leer el PDF con OCR: {e}") from e

    return texto_completo


def es_pdf_escaneado(ruta_pdf):
    """
    Detecta automaticamente si un PDF es escaneado o tiene texto real.
    Asi el programa decide solo que metodo usar.
    """

    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()

            # Si hay menos de 30 caracteres, se asume que es escaneado.
            if texto is None or len(texto.strip()) < 30:
                return True

            return False
    except Exception as error:
        print(f"No se pudo inspeccionar {ruta_pdf}; se intentará OCR: {error}")
        return True
