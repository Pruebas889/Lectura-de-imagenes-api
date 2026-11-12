import re

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

    def extraer_valor_etiquetado(etiquetas):
        etiqueta = "|".join(sorted(etiquetas, key=len, reverse=True))
        etiquetas_siguientes = (
            r"NIT(?:[ \t]+(?:DEL[ \t]+)?PROVEEDOR)?|"
            r"FECHA|HORA|REFERENCIA|"
            r"NRO\.?[ \t]+AUTORIZACI[ÓO]N|AUTORIZACI[ÓO]N|"
            r"PUNTO[ \t]+(?:DE[ \t]+)?RECAUDO|"
            r"TRANSACCI[ÓO]N"
        )
        coincidencia = re.search(
            rf"(?<!\w)(?:{etiqueta})\s*(?:[:#-]\s*)?"
            rf"([^\r\n]*?)(?=\s+(?:{etiquetas_siguientes})"
            rf"(?:\s*[:#-]|\s)|[\r\n]|$)",
            texto,
            re.IGNORECASE | re.MULTILINE
        )
        return coincidencia.group(1).strip(" \t:;#-") if coincidencia else ""

    estado = re.search(
        r"\bTRANSACCI[ÓO]N\s*,?\s*(EXITOSA|FALLIDA|RECHAZADA)\b",
        texto,
        re.IGNORECASE
    )
    if estado:
        datos["estado_transaccion"] = (
            f"TRANSACCION {estado.group(1).upper()}"
        )
    datos["hora"] = extraer_valor_etiquetado([
        r"HORA\s+(?:DE\s+)?TRANSACCI[ÓO]N",
        r"HORA"
    ])
    hora = re.search(
        r"\b([01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\s*(?:A\.?M\.?|P\.?M\.?)?\b",
        datos["hora"],
        re.IGNORECASE
    )
    if hora:
        datos["hora"] = hora.group(0).strip()
    datos["referencia"] = extraer_valor_etiquetado([
        r"REFERENCIA\s+(?:DE\s+)?(?:PAGO|TRANSACCI[ÓO]N)",
        r"REFERENCIA"
    ])
    datos["numero_autorizacion"] = extraer_valor_etiquetado([
        r"N(?:RO|[ÚU]M(?:ERO)?|O\.?)\.?\s+(?:DE\s+)?AUTORIZACI[ÓO]N",
        r"AUTORIZACI[ÓO]N"
    ])
    datos["punto_recaudo"] = extraer_valor_etiquetado([
        r"PUNTO\s+DE\s+RECAUDO",
        r"PUNTO\s+RECAUDO"
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
        "BANCO OCCIDENTE COLOMBIA", "BANCOLOMBIA", "BANCO DE BOGOTA",
        "BANCO DE OCCIDENTE",
        "BANCO POPULAR", "BANCO AV VILLAS", "DAVIVIENDA", "DAVIPLATA",
        "BBVA", "SCOTIABANK", "COLPATRIA", "BANCO AGRARIO", "NEQUI",
        "BANCO FALABELLA", "BANCO CAJA SOCIAL", "BANCOOMEVA", "ITAU",
        "LULO BANK", "BAN100"
    ]
    for banco in bancos:
        if re.search(r"\b" + re.escape(banco) + r"\b", texto, re.IGNORECASE):
            datos["banco"] = banco
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


    #-----------FECHA---------------
    formatos_fecha = r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    patron = re.search(
        rf"(?:FECHA(?:\s+(?:DE\s+)?(?:EMISION|EXPEDICION|FACTURA))?)"
        rf"\s*[:.]?\s*{formatos_fecha}",
        texto,
        re.IGNORECASE
    )

    if patron:
        fecha = patron.group(1)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
            datos["fecha"] = fecha
        else:
            partes = re.split(r"[/-]", fecha)
            if len(partes[2]) == 4:
                datos["fecha"] = f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
            else:
                datos["fecha"] = f"{partes[0]}-{partes[1].zfill(2)}-{partes[2]}"

    else:

        patron = re.search(
            r'(\d{2})[/-](\d{2})[/-](\d{4})',
            texto
        )

        if patron:

            dia = patron.group(1)
            mes = patron.group(2)
            anio = patron.group(3)

            datos["fecha"] = f"{anio}-{mes}-{dia}"


    #---------TOTAL-----------------

    prioridades = [
        "VALOR NETO ABONADO",
        "NETO A PAGAR",
        "VALOR NETO A PAGAR",
        "TOTAL A PAGAR",
        "VALOR TOTAL",
        "VALOR VENTA",
        "SUBTOTAL",
        "VALOR PAGO",
        "VALOR CONSIGNADO",
        "VALOR TRANSACCION",
        "VALOR TRANSACCIÓN",
    ]

    lineas = texto.splitlines()

    for prioridad in prioridades:

        for i, linea in enumerate(lineas):

            if prioridad not in linea.upper():
                continue

            # Revisar la línea actual y las dos siguientes
            bloque = "\n".join(lineas[i:i+3])

            # Buscar únicamente valores precedidos por $
            # Buscar el valor inmediatamente después de ":"
            encontrados = re.findall(
                rf"{re.escape(prioridad)}\s*(?:\:|=>)?\s*\$?\s*([\d][\d\.,]*)",
                bloque,
                re.IGNORECASE
            )

            if encontrados:
                datos["total"] = encontrados[-1]
                break

        if datos["total"]:
            break

    return datos