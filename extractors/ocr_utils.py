import re
import unicodedata

import pytesseract
from PIL import Image, ImageOps

from config.settings import TESSERACT_PATH
from extractors.regex_extractor import extraer_con_regex


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


def calidad_texto_ocr(texto: str) -> tuple[int, int, int]:
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_normalizado = "".join(
        caracter
        for caracter in texto_normalizado
        if not unicodedata.combining(caracter)
    ).upper()
    palabras = len(re.findall(r"\b[\w]{2,}\b", texto_normalizado))
    etiquetas = len(
        re.findall(
            r"\b(?:FECHA|HORA|TOTAL|VALOR|MONTO|PAGO|TRANSACCION|"
            r"REFERENCIA|AUTORIZACION|RECAUDO|BANCO|FACTURA|NIT)\b",
            texto_normalizado
        )
    )
    datos = extraer_con_regex(texto_normalizado)
    pesos_campos = {
        "fecha": 3,
        "hora": 2,
        "total": 3,
        "estado_transaccion": 3,
        "referencia": 2,
        "numero_autorizacion": 2,
        "punto_recaudo": 2,
        "banco": 1
    }
    campos = sum(
        peso for campo, peso in pesos_campos.items()
        if datos.get(campo)
    )
    return campos, palabras * 2 + etiquetas * 8, len(texto)


def extraer_texto_por_variantes(
    imagen: Image.Image,
    modos_segmentacion: tuple[int, ...],
    escala: float = 1.0
) -> str:
    imagen_copia = imagen.copy()
    imagen_base = ImageOps.exif_transpose(imagen_copia)
    if imagen_base is not imagen_copia:
        imagen_copia.close()

    if escala > 1:
        imagen_escalada = imagen_base.resize(
            (
                int(round(imagen_base.width * escala)),
                int(round(imagen_base.height * escala))
            ),
            Image.Resampling.LANCZOS
        )
        imagen_base.close()
        imagen_base = imagen_escalada

    mejor_texto = ""
    mejor_puntaje = (-1, -1, -1)
    angulos_probados = set()

    def probar_angulo(angulo: int) -> None:
        nonlocal mejor_texto, mejor_puntaje
        if angulo in angulos_probados:
            return
        angulos_probados.add(angulo)

        imagen_candidata = (
            imagen_base.rotate(angulo, expand=True)
            if angulo
            else imagen_base
        )
        try:
            for modo in modos_segmentacion:
                configuracion = (
                    f"--oem 3 --psm {modo} "
                    "-c preserve_interword_spaces=1 "
                    "-c textord_heavy_nr=1"
                )
                texto = pytesseract.image_to_string(
                    imagen_candidata,
                    lang="spa+eng",
                    config=configuracion
                ).strip()
                puntaje = calidad_texto_ocr(texto)
                if puntaje > mejor_puntaje:
                    mejor_texto = texto
                    mejor_puntaje = puntaje
        finally:
            if angulo:
                imagen_candidata.close()

    try:
        angulos = [0]
        try:
            orientacion = pytesseract.image_to_osd(
                imagen_base,
                lang="osd",
                config="--psm 0"
            )
        except pytesseract.TesseractError:
            orientacion = ""

        rotacion = re.search(r"Rotate:\s*(\d+)", orientacion)
        if rotacion:
            angulo = (-int(rotacion.group(1))) % 360
            if angulo:
                angulos.append(angulo)

        for angulo in angulos:
            probar_angulo(angulo)

        if mejor_puntaje[0] < 4 and mejor_puntaje[1] < 120:
            for angulo in (90, 180, 270):
                probar_angulo(angulo)

        return mejor_texto
    finally:
        imagen_base.close()
