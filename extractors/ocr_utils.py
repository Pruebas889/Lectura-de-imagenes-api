import pytesseract

from config.settings import TESSERACT_PATH


if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def validar_tesseract():
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError(
            "No se encontro Tesseract. Instala Tesseract OCR y configura "
            "TESSERACT_PATH o agregalo al PATH del sistema."
        ) from error
