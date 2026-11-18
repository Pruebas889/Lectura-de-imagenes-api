import re
import unicodedata
from datetime import date as fecha_calendario


_MESES = {
    "ENE": 1, "ENERO": 1, "JAN": 1, "JANUARY": 1,
    "FEB": 2, "FEBRERO": 2, "FEBRUARY": 2,
    "MAR": 3, "MARZO": 3, "MARCH": 3,
    "ABR": 4, "ABRIL": 4, "APR": 4, "APRIL": 4,
    "MAY": 5, "MAYO": 5,
    "JUN": 6, "JUNIO": 6, "JUNE": 6,
    "JUL": 7, "JULIO": 7, "JULY": 7,
    "AGO": 8, "AGOSTO": 8, "AUG": 8, "AUGUST": 8,
    "SEP": 9, "SEPT": 9, "SEPTIEMBRE": 9, "SETIEMBRE": 9,
    "SEPTEMBER": 9,
    "OCT": 10, "OCTUBRE": 10, "OCTOBER": 10,
    "NOV": 11, "NOVIEMBRE": 11, "NOVEMBER": 11,
    "DIC": 12, "DICIEMBRE": 12, "DEC": 12, "DECEMBER": 12
}
_PATRON_MESES = "|".join(
    sorted((re.escape(mes) for mes in _MESES), key=len, reverse=True)
)
_PATRON_HORA = re.compile(
    r"(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)"
    r"(?:[:.]([0-5]\d))?\s*(A\.?\s*M\.?|P\.?\s*M\.?)?(?!\d)",
    re.IGNORECASE
)
CAMPOS_NO_LEGIBLES = (
    "fecha",
    "hora",
    "total",
    "estado_transaccion",
    "referencia",
    "numero_autorizacion",
    "punto_recaudo",
    "banco"
)
NO_LEGIBLE = "No legible"


def completar_campos_no_legibles(datos: dict) -> dict:
    resultado = datos.copy()
    for campo in CAMPOS_NO_LEGIBLES:
        if not resultado.get(campo):
            resultado[campo] = NO_LEGIBLE
    return resultado


def _sin_acentos(texto: str) -> str:
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )


def _formatear_fecha(anio: int, mes: int, dia: int) -> str:
    if anio < 100:
        anio += 2000 if anio <= 68 else 1900
    try:
        return fecha_calendario(anio, mes, dia).isoformat()
    except ValueError:
        return ""


def _buscar_fecha(texto: str) -> str:
    texto = _sin_acentos(texto).upper()
    patron_iso = re.search(
        r"\b(19\d{2}|20\d{2})[./-](\d{1,2})[./-](\d{1,2})\b",
        texto
    )
    if patron_iso:
        return _formatear_fecha(
            int(patron_iso.group(1)),
            int(patron_iso.group(2)),
            int(patron_iso.group(3))
        )

    patron_numerico = re.search(
        r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b",
        texto
    )
    if patron_numerico:
        primero, segundo, anio = map(int, patron_numerico.groups())
        if primero > 12:
            dia, mes = primero, segundo
        elif segundo > 12:
            mes, dia = primero, segundo
        else:
            dia, mes = primero, segundo
        return _formatear_fecha(anio, mes, dia)

    patron_dia_mes = re.search(
        rf"\b(\d{{1,2}})\s*(?:DE\s+)?({_PATRON_MESES})\.?"
        rf"\s*(?:DE\s+)?(\d{{2,4}})\b",
        texto
    )
    if patron_dia_mes:
        dia, nombre_mes, anio = patron_dia_mes.groups()
        return _formatear_fecha(int(anio), _MESES[nombre_mes], int(dia))

    patron_mes_dia = re.search(
        rf"\b({_PATRON_MESES})\.?\s+(\d{{1,2}}),?\s+(\d{{2,4}})\b",
        texto
    )
    if patron_mes_dia:
        nombre_mes, dia, anio = patron_mes_dia.groups()
        return _formatear_fecha(int(anio), _MESES[nombre_mes], int(dia))
    return ""


def _extraer_fecha(texto: str) -> str:
    lineas = texto.splitlines()
    etiquetas_vencimiento = re.compile(
        r"\b(?:VENCIMIENTO|VENCE|CORTE|SUSPENSION)\b",
        re.IGNORECASE
    )

    for indice, linea in enumerate(lineas):
        linea_normalizada = _sin_acentos(linea).upper()
        if "FECHA" not in linea_normalizada or etiquetas_vencimiento.search(linea_normalizada):
            continue
        fecha = _buscar_fecha(linea)
        if fecha:
            return fecha
        for siguiente in lineas[indice + 1:indice + 3]:
            if not siguiente.strip():
                continue
            if re.search(r"\b(?:FECHA|HORA|TOTAL|VALOR|MONTO)\b", _sin_acentos(siguiente), re.IGNORECASE):
                break
            fecha = _buscar_fecha(siguiente)
            if fecha:
                return fecha

    for linea in lineas:
        if etiquetas_vencimiento.search(_sin_acentos(linea)):
            continue
        fecha = _buscar_fecha(linea)
        if fecha:
            return fecha
    return ""


def _formatear_hora(coincidencia: re.Match) -> str:
    hora = int(coincidencia.group(1))
    minuto = int(coincidencia.group(2))
    segundo = coincidencia.group(3)
    indicador = re.sub(r"[^APM]", "", (coincidencia.group(4) or "").upper())
    if indicador == "AM" and hora == 12:
        hora = 0
    elif indicador == "PM" and hora < 12:
        hora += 12
    resultado = f"{hora:02d}:{minuto:02d}"
    return f"{resultado}:{segundo}" if segundo else resultado


def _extraer_hora(texto: str) -> str:
    lineas = texto.splitlines()
    for linea in lineas:
        if re.search(r"\bHORAS?\b", linea, re.IGNORECASE):
            coincidencia = _PATRON_HORA.search(linea)
            if coincidencia:
                return _formatear_hora(coincidencia)
    coincidencia = _PATRON_HORA.search(texto)
    return _formatear_hora(coincidencia) if coincidencia else ""


_ETIQUETAS_SALIDA = (
    r"NIT(?:\s+(?:DEL\s+)?PROVEEDOR)?|FECHA|HORAS?|"
    r"REFERENCIA|RRN|REN|ARN|AUTORIZACION|APROB(?:ACION|\.?)|"
    r"PUNTO\s+(?:DE|IME|NE)\s+VENTA|PUNTO\s+(?:DE\s+)?RECAUDO|"
    r"TRANSACCION|ESTADO|TOTAL|VALOR|MONTO|BANCO|CONVENIO|"
    r"FORMA\s+DE\s+PAGO"
)


def _extraer_valor_etiquetado(texto: str, etiquetas: list[str]) -> str:
    patron_etiquetas = "|".join(
        sorted(etiquetas, key=len, reverse=True)
    )
    patron_etiqueta = re.compile(
        rf"(?<!\w)(?:{patron_etiquetas})(?!\w)\s*(?:[:#-]\s*)?",
        re.IGNORECASE
    )
    patron_salida = re.compile(
        rf"\s+(?=(?:{_ETIQUETAS_SALIDA})(?!\w))",
        re.IGNORECASE
    )
    lineas = texto.splitlines()

    for indice, linea in enumerate(lineas):
        coincidencia = patron_etiqueta.search(linea)
        if not coincidencia:
            continue
        valor = linea[coincidencia.end():]
        salida = patron_salida.search(valor)
        if salida:
            valor = valor[:salida.start()]
        valor = valor.strip(" \t:;#-|")
        if valor:
            return valor
        for siguiente in lineas[indice + 1:indice + 3]:
            if not siguiente.strip():
                continue
            if patron_salida.search(f" {siguiente}"):
                break
            return siguiente.strip(" \t:;#-|")
    return ""


def _extraer_estado_transaccion(texto: str) -> str:
    estados = re.compile(
        r"\b(NO\s+EXITOS[AO]|EXITOS[AO]|APROBAD[AO]|RECHAZAD[AO]|"
        r"FALLID[AO]|DECLINAD[AO]|PENDIENTE|CANCELAD[AO])\b"
    )
    contexto = re.compile(r"\b(?:TRANSACCION|ESTADO|PAGO|RECAUDO)\b")
    for linea in texto.splitlines():
        linea_normalizada = _sin_acentos(linea).upper()
        if not contexto.search(linea_normalizada):
            continue
        estado = estados.search(linea_normalizada)
        if estado:
            return f"TRANSACCION {estado.group(1)}"
    return ""


def _extraer_total(texto: str) -> str:
    prioridades = (
        r"VALOR\s+NETO\s+ABONADO",
        r"NETO\s+A\s*PAGAR",
        r"VALOR\s+NETO\s+A\s*PAGAR",
        r"TOTAL\s+(?:DE\s+)?(?:LA\s+)?DEUDA",
        r"TOTAL\s+(?:DE\s+)?(?:LA\s+)?FACTURA",
        r"TOTAL\s+A\s*PAGAR",
        r"(?:V|Y)ALOR\s+TOTAL",
        r"(?:V|Y)ALOR\s+(?:P|F)AGO",
        r"VALOR\s+TRANSACCION",
        r"VALOR\s+CONSIGNADO",
        r"TOTAL\s+COMPRA",
        r"IMPORTE\s+TOTAL",
        r"VR\.?\s*TOTAL",
        r"MONTO",
        r"TOTAL(?!\s+(?:ITEMS?|UNIDADES|LINEAS|PRODUCTOS|NRO|NUMERO|IVA|DESCUENTO))"
    )
    patron_valor = re.compile(
        r"(?<!\w)(?:COP\s*)?\$?\s*(\d[\d., ]*\d|\d)(?!\w)",
        re.IGNORECASE
    )
    lineas = texto.splitlines()

    for prioridad in prioridades:
        patron_etiqueta = re.compile(
            rf"(?<!\w)(?:{prioridad})(?!\w)\s*(?:[:=<>-]\s*)?",
            re.IGNORECASE
        )
        for indice, linea in enumerate(lineas):
            coincidencia = patron_etiqueta.search(linea)
            if not coincidencia:
                continue
            valor_en_linea = linea[coincidencia.end():]
            if re.match(r"\s*(?:CON\s+LETRA|EN\s+LETRAS)\b", valor_en_linea, re.IGNORECASE):
                continue
            candidatos = [valor_en_linea]
            candidatos.extend(lineas[indice + 1:indice + 3])
            for candidato in candidatos:
                monto = patron_valor.search(candidato)
                if monto:
                    return re.sub(r"\s+", "", monto.group(1)).strip(".,")
                if candidato is not valor_en_linea and re.search(
                    r"\b(?:TOTAL|VALOR|MONTO|FECHA|HORA)\b",
                    candidato,
                    re.IGNORECASE
                ):
                    break
    return ""

def extraer_con_regex(texto: str) -> dict:

    datos = {
        "proveedor": "",
        "total": "",
        "fecha": "",
        "nit": "",
        "cliente": "",
        "nombre_cliente": "",
        "numero_factura": "",
        "banco": "",
        "nit_proveedor": "",
        "estado_transaccion": "",
        "hora": "",
        "referencia": "",
        "numero_autorizacion": "",
        "punto_recaudo": ""
    }

    #-------------NIT---------------

    patron = re.search(
        r'NIT(?:[ \t]+(?:DEL[ \t]+)?PROVEEDOR)?[: \t]*([\d][\d.,\- ]*)',
        texto,
        re.IGNORECASE
    )

    if patron:
        datos["nit"] = (
        patron.group(1)
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .strip()
    )
    datos["nit_proveedor"] = datos["nit"]

    datos["estado_transaccion"] = _extraer_estado_transaccion(texto)
    datos["hora"] = _extraer_hora(texto)
    datos["referencia"] = _extraer_valor_etiquetado(texto, [
        r"N(?:RO|[ÚU]M(?:ERO)?|O\.?)\.?\s*(?:DE\s+)?REFERENCIA",
        r"REFERENCIA\s+(?:DE\s+)?(?:PAGO|TRANSACCI[ÓO]N)",
        r"REFERENCIA",
        r"RRN",
        r"REN",
        r"ARN",
        r"REF\.?"
    ])
    if not datos["referencia"]:
        datos["referencia"] = _extraer_valor_etiquetado(texto, [
            r"N(?:RO|[ÚU]M(?:ERO)?|O\.?)\.?\s*(?:DE\s+)?TRANSACCI[ÓO]N",
            r"TRANSACCI[ÓO]N\s+(?:NRO|N[ÚU]MERO|NO\.?)"
        ])
    datos["numero_autorizacion"] = _extraer_valor_etiquetado(texto, [
        r"N(?:RO|[ÚU]M(?:ERO)?|O\.?)\.?\s*(?:DE\s+)?AUTORIZACI[ÓO]N",
        r"(?:CODIGO|C[ÓO]DIGO)\s+(?:DE\s+)?AUTORIZACI[ÓO]N",
        r"N[UÚJ]M(?:ERO)?\.?\s*(?:DE\s+)?APROBACI[ÓO]N",
        r"(?:CODIGO|C[ÓO]DIGO)\s+(?:DE\s+)?APROBACI[ÓO]N",
        r"AUTORIZACI[ÓO]N",
        r"APROBACI[ÓO]N",
        r"APROB\.?",
        r"(?:AUTHORIZATION|AUTH)\s+CODE"
    ])
    datos["punto_recaudo"] = _extraer_valor_etiquetado(texto, [
        r"PUNTO\s+(?:DE|IME|NE)\s+VENTA",
        r"PUNTO\s+(?:DE\s+)?(?:RECAUDO|SERVICIO)",
        r"CORRESPONSAL",
        r"TERMINAL",
        r"CAJA"
    ])


    #-----------------NUMERO FACTURA-----------------

    patrones_factura = [

        # Caso:
        # FACTURA ... NO. 2669
        # 126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{3,})\s*\n+\s*([A-Z0-9]{3,})',

        # Caso:
        # FACTURA ... NO. 2669 126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{3,})\s+([A-Z0-9]{3,})',

        # Caso:
        # FACTURA ... NO.2669126313
        r'FACTURA.*?NO[\.,:]?\s*([A-Z0-9]{8,})'
    ]

    for patron in patrones_factura:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if not encontrado:
            continue

        if len(encontrado.groups()) == 2:

            parte1 = encontrado.group(1).replace(" ", "").upper()
            parte2 = encontrado.group(2).replace(" ", "").upper()

            datos["numero_factura"] = parte1 + parte2

        else:

            datos["numero_factura"] = (
                encontrado.group(1)
                .replace(" ", "")
                .upper()
            )

        break



    #-------------------PROVEEDOR----------------

    # 1. Buscar establecimientos muy comunes al inicio del documento

    patron_empresa = re.search(
        r"^\s*([A-ZÁÉÍÓÚÑ0-9&.,\- ]{4,}?"
        r"(?:S\.A\.S\.?|SAS|S\.A\.?|SA|LTDA\.?|E\.U\.?|EU))\s*$",
        texto,
        re.IGNORECASE | re.MULTILINE
    )
    if patron_empresa:
        datos["proveedor"] = patron_empresa.group(1).strip()

    patrones_proveedor = [
        r"REBAJA\s+PLUS[^\n]*", r"LA\s+REBAJA[^\n]*",
        r"CRUZ\s+VERDE[^\n]*", r"FARMATODO[^\n]*",
        r"EXITO[^\n]*", r"CARULLA[^\n]*", r"OLIMPICA[^\n]*",
        r"\bD1\b[^\n]*", r"\bARA\b[^\n]*", r"JUMBO[^\n]*",
        r"ALKOSTO[^\n]*", r"SURTIMAX[^\n]*", r"ISIMO[^\n]*",
        r"METRO[^\n]*", r"KTRONIX[^\n]*", r"LOCATEL[^\n]*",
        r"HOMECENTER[^\n]*", r"EASY[^\n]*", r"PANAMERICANA[^\n]*",
        r"TERPEL[^\n]*", r"PRIMAX[^\n]*", r"BIOMAX[^\n]*",
        r"TEXACO[^\n]*", r"ESSO[^\n]*", r"CLARO[^\n]*",
        r"MOVISTAR[^\n]*", r"TIGO[^\n]*", r"WOM[^\n]*",
        r"DIRECTV[^\n]*", r"ENEL[^\n]*", r"EMCALI[^\n]*"
    ]
    if not datos["proveedor"]:
        for patron in patrones_proveedor:
            encontrado = re.search(patron, texto, re.IGNORECASE)
            if encontrado:
                datos["proveedor"] = encontrado.group(0).strip()
                break

    bancos = [
        (r"BANCO\s+OCCIDENTE\s+COLOMBIA", "BANCO OCCIDENTE COLOMBIA"),
        (r"BANCOLOMB[I1L]A", "BANCOLOMBIA"),
        (r"BANCO\s+DE\s+BOGOT[ÁA]", "BANCO DE BOGOTA"),
        (r"BANCO\s+DE\s+OCCIDENTE", "BANCO DE OCCIDENTE"),
        (r"BANCO\s+POPULAR", "BANCO POPULAR"),
        (r"BANCO\s+AV\s+VILLAS", "BANCO AV VILLAS"),
        (r"DAVIVIENDA", "DAVIVIENDA"),
        (r"DAVIPLATA", "DAVIPLATA"),
        (r"BBVA", "BBVA"),
        (r"SCOTIABANK", "SCOTIABANK"),
        (r"COLPATRIA", "COLPATRIA"),
        (r"BANCO\s+AGRARIO", "BANCO AGRARIO"),
        (r"NEQUI", "NEQUI"),
        (r"BANCO\s+FALABELLA", "BANCO FALABELLA"),
        (r"BANCO\s+CAJA\s+SOCIAL", "BANCO CAJA SOCIAL"),
        (r"BANCOOMEVA", "BANCOOMEVA"),
        (r"ITAU", "ITAU"),
        (r"LULO\s+BANK", "LULO BANK"),
        (r"BAN100", "BAN100"),
        (r"BANCO\s+PICHINCHA", "BANCO PICHINCHA"),
        (r"BANCO\s+FINANDINA", "BANCO FINANDINA"),
        (r"BANCO\s+SERFINANZA", "BANCO SERFINANZA"),
        (r"BANCO\s+W\b", "BANCO W")
    ]
    texto_bancos = _sin_acentos(texto)
    for patron_banco, nombre_banco in bancos:
        if re.search(r"\b" + patron_banco + r"\b", texto_bancos, re.IGNORECASE):
            datos["banco"] = nombre_banco
            break

    #-------------------CLIENTE------------

    patrones_cliente = [

        r'CLIENTE[:;\s]*([0-9]{6,})',

        r'CLIENTE[.;:\s]*([0-9]{6,})'

    ]

    for patron in patrones_cliente:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE | re.DOTALL

        )

        if encontrado:

            datos["cliente"] = encontrado.group(1)
            break



    #---------------NOMBRE CLIENTE---------

    patrones_nombre = [

        r'NOMBRE[:;\s]*([A-ZÁÉÍÓÚÑ ]+)',

        r'NOMBRE[.;:\s]*([A-ZÁÉÍÓÚÑ ]+)',

        r'NOMBRE.*?([A-ZÁÉÍÓÚÑ ]{5,})'
        
    ]

    for patron in patrones_nombre:

        coincidencias = re.findall(

            patron,
            texto,
            re.IGNORECASE | re.DOTALL

        )

        for nombre in coincidencias:

            nombre = nombre.strip()

            if (
                "SW" not in nombre.upper()
                and "FINANCIERO" not in nombre.upper()
                and "CARVAJAL" not in nombre.upper()
                and len(nombre) > 5
            ):

                datos["nombre_cliente"] = nombre
                break


    datos["fecha"] = _extraer_fecha(texto)
    datos["total"] = _extraer_total(texto)

    return datos