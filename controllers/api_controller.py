import base64
import json
import mimetypes
import os
import zipfile
from datetime import datetime
from flask import jsonify, request, send_file
from io import BytesIO
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
from werkzeug.utils import secure_filename
from database.db_manager import (
    obtener_todas,
    obtener_resumenes,
    obtener_por_ids,
    obtener_por_id,
    contar_facturas,
    borrar_todas
)
from config.settings import (
    DOCUMENT_FOLDER,
    PDF_FOLDER,
    POPPLER_PATH,
)
import tempfile

from services.factura_service import _procesar_archivo

EXTENSIONES_DOCUMENTO = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _ruta_documento_factura(factura):
    try:
        nombre_guardado = factura["archivo_original"]
    except (IndexError, KeyError):
        nombre_guardado = None

    carpeta = DOCUMENT_FOLDER
    nombre = nombre_guardado
    if not nombre:
        carpeta = PDF_FOLDER
        nombre = factura["nombre_archivo"]

    if not nombre or os.path.basename(nombre) != nombre:
        return None

    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_DOCUMENTO:
        return None

    ruta = os.path.join(carpeta, nombre)
    return ruta if os.path.isfile(ruta) else None


def api_miniatura_factura(factura_id):
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "Factura no encontrada"}), 404

    ruta = _ruta_documento_factura(factura)
    if not ruta:
        return jsonify({"error": "El documento original no está disponible"}), 404

    try:
        extension = os.path.splitext(ruta)[1].lower()
        if extension == ".pdf":
            paginas = convert_from_path(
                ruta,
                dpi=90,
                first_page=1,
                last_page=1,
                poppler_path=POPPLER_PATH
            )
            if not paginas:
                return jsonify({"error": "El PDF no contiene páginas para mostrar"}), 422
            imagen = paginas[0]
        else:
            imagen = Image.open(ruta)

        imagen.thumbnail((900, 1100))
        salida = BytesIO()
        imagen.convert("RGB").save(salida, format="JPEG", quality=82, optimize=True)
        salida.seek(0)
        return send_file(salida, mimetype="image/jpeg")
    except Exception as error:
        print(f"[Invoice thumbnail] No se pudo renderizar factura {factura_id}: {error}")
        return jsonify({"error": "No se pudo generar la miniatura del documento"}), 422


def api_previsualizar_factura(factura_id):
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "Factura no encontrada"}), 404

    ruta = _ruta_documento_factura(factura)
    if not ruta:
        return jsonify({"error": "El documento original no está disponible"}), 404

    try:
        extension = os.path.splitext(ruta)[1].lower()
        if extension == ".pdf":
            paginas = convert_from_path(ruta, dpi=120, poppler_path=POPPLER_PATH)
        else:
            paginas = [Image.open(ruta)]

        if not paginas:
            return jsonify({"error": "El documento no contiene páginas para mostrar"}), 422

        resultado = []
        for numero, pagina in enumerate(paginas, start=1):
            imagen = BytesIO()
            pagina.convert("RGB").save(
                imagen,
                format="JPEG",
                quality=82,
                optimize=True
            )
            contenido = base64.b64encode(imagen.getvalue()).decode("ascii")
            resultado.append({
                "numero": numero,
                "imagen": f"data:image/jpeg;base64,{contenido}"
            })

        return jsonify({"paginas": resultado})
    except Exception as error:
        print(f"[Invoice viewer] No se pudo abrir factura {factura_id}: {error}")
        return jsonify({"error": "No se pudo abrir el documento original"}), 422


def api_abrir_documento_factura(factura_id):
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "Factura no encontrada"}), 404

    ruta = _ruta_documento_factura(factura)
    if not ruta:
        return jsonify({"error": "El documento original no está disponible"}), 404

    respuesta = send_file(
        ruta,
        mimetype=mimetypes.guess_type(ruta)[0] or "application/octet-stream",
        as_attachment=False,
        download_name=os.path.basename(ruta)
    )
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    return respuesta


def api_previsualizar_pdf():
    """Renderiza la primera página del PDF como imagen para la vista previa."""
    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return jsonify({"error": "Falta un archivo PDF"}), 400
    if not archivo.filename.lower().endswith(".pdf"):
        return jsonify({"error": "El archivo debe ser un PDF"}), 415

    try:
        paginas = convert_from_bytes(
            archivo.read(),
            dpi=120,
            first_page=1,
            last_page=1,
            poppler_path=POPPLER_PATH
        )
        if not paginas:
            return jsonify({"error": "El PDF no contiene páginas para mostrar"}), 422

        paginas[0].thumbnail((1000, 1200))
        imagen = BytesIO()
        paginas[0].save(imagen, format="PNG", optimize=True)
        imagen.seek(0)
        return send_file(imagen, mimetype="image/png")
    except Exception as error:
        print(f"[PDF preview] No se pudo renderizar {archivo.filename}: {error}")
        return jsonify({
            "error": "No se pudo generar la vista previa. Verifica que Poppler esté instalado."
        }), 422


def api_previsualizar_pdf_completo():
    """Renderiza todas las páginas de un PDF para mostrarlas en el visor."""
    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return jsonify({"error": "Falta un archivo PDF"}), 400
    if not archivo.filename.lower().endswith(".pdf"):
        return jsonify({"error": "El archivo debe ser un PDF"}), 415

    try:
        paginas = convert_from_bytes(
            archivo.read(),
            dpi=120,
            poppler_path=POPPLER_PATH
        )
        if not paginas:
            return jsonify({"error": "El PDF no contiene páginas para mostrar"}), 422

        resultado = []
        for numero, pagina in enumerate(paginas, start=1):
            pagina.thumbnail((1400, 1800))
            imagen = BytesIO()
            pagina.convert("RGB").save(
                imagen,
                format="JPEG",
                quality=82,
                optimize=True
            )
            contenido = base64.b64encode(imagen.getvalue()).decode("ascii")
            resultado.append({
                "numero": numero,
                "imagen": f"data:image/jpeg;base64,{contenido}"
            })

        return jsonify({"paginas": resultado})
    except Exception as error:
        print(f"[PDF viewer] No se pudo renderizar {archivo.filename}: {error}")
        return jsonify({
            "error": "No se pudo abrir el documento. Verifica que Poppler esté instalado."
        }), 422


def _procesar_archivo_subido(archivo):
    nombre = os.path.basename((archivo.filename or "").replace("\\", "/"))
    if not nombre:
        raise ValueError("Nombre de archivo vacío")

    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_DOCUMENTO:
        raise ValueError(
            "Formato no soportado. Usa PDF, JPG, PNG, WEBP, BMP o TIFF."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temporal:
        ruta_tmp = temporal.name
    try:
        archivo.save(ruta_tmp)
        return _procesar_archivo(ruta_tmp, nombre)
    finally:
        if os.path.exists(ruta_tmp):
            os.unlink(ruta_tmp)


def _resultado_procesamiento(archivo):
    nombre = os.path.basename((archivo.filename or "").replace("\\", "/"))
    try:
        factura = _procesar_archivo_subido(archivo)
        return {
            "archivo": nombre,
            "ok": True,
            "datos": {
                "factura_id": factura.id,
                "nombre_archivo": factura.nombre_archivo,
                "tipo": factura.tipo_pdf,
                "proveedor": factura.proveedor,
                "total": factura.total,
                "fecha": factura.fecha,
                "banco": factura.banco,
                "nit_proveedor": factura.nit_proveedor,
                "estado_transaccion": factura.estado_transaccion,
                "hora": factura.hora,
                "referencia": factura.referencia,
                "numero_autorizacion": factura.numero_autorizacion,
                "punto_recaudo": factura.punto_recaudo,
                "texto_extraido": factura.texto_extraido,
                "advertencia_cuota_groq": factura.advertencia_cuota_groq
            }
        }
    except (ValueError, RuntimeError) as error:
        if isinstance(error, ValueError):
            estado = 400 if str(error) == "Nombre de archivo vacío" else 415
        else:
            estado = 422
        return {
            "archivo": nombre,
            "ok": False,
            "error": str(error),
            "estado_http": estado
        }
    except Exception as error:
        print(f"[API processing] Error inesperado al procesar {nombre!r}: {error}")
        return {
            "archivo": nombre,
            "ok": False,
            "error": "Error interno al procesar el archivo.",
            "estado_http": 500
        }


def _respuesta_lote(archivos):
    if not archivos:
        return jsonify({"error": "Selecciona al menos un archivo."}), 400

    resultados = [_resultado_procesamiento(archivo) for archivo in archivos]
    exitosos = sum(resultado["ok"] for resultado in resultados)
    fallidos = len(resultados) - exitosos
    return jsonify({
        "ok": fallidos == 0,
        "total": len(resultados),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "resultados": resultados
    })


def api_procesar():
    """Procesa un archivo legado o varios archivos enviados como 'archivos'."""
    archivos_lote = request.files.getlist("archivos")
    if archivos_lote:
        return _respuesta_lote(archivos_lote)

    archivo = request.files.get("archivo")
    if archivo is None:
        return jsonify({
            "error": "Falta el campo 'archivo' o 'archivos' en el form-data."
        }), 400

    resultado = _resultado_procesamiento(archivo)
    if not resultado["ok"]:
        return jsonify({"error": resultado["error"]}), resultado["estado_http"]
    return jsonify({"ok": True, "datos": resultado["datos"]})


def api_procesar_lote():
    """Procesa varios archivos y devuelve un resultado independiente por archivo."""
    return _respuesta_lote(request.files.getlist("archivos"))


def api_listar():
    """GET /api/facturas → devuelve todas las facturas guardadas"""
    return jsonify([dict(f) for f in obtener_todas()])


def api_detalle(factura_id):
    """GET /api/facturas/5 → detalle de una factura por ID"""
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "No encontrada"}), 404
    return jsonify(dict(factura))


def _valor_api(valor):
    return None if valor in (None, "") else valor


def _fecha_api(valor):
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor).isoformat()
        except ValueError:
            return valor
    return valor


def _resumen_documento_api(factura):
    fila = dict(factura)
    documento_id = fila["id"]
    return {
        "id": documento_id,
        "archivo": {
            "nombre": fila["nombre_archivo"],
            "original_url": f"/api/facturas/{documento_id}/original"
        },
        "documento": {
            "tipo": _valor_api(fila.get("tipo_pdf")),
            "entidad": _valor_api(fila.get("banco"))
        },
        "procesamiento": {
            "fecha": _fecha_api(fila.get("fecha_procesado"))
        }
    }


def _detalle_documento_api(factura):
    fila = dict(factura)
    documento = _resumen_documento_api(fila)
    documento["datos"] = {
        "proveedor": _valor_api(fila.get("proveedor")),
        "nit": _valor_api(fila.get("nit_proveedor")),
        "total": _valor_api(fila.get("total")),
        "fecha": _valor_api(fila.get("fecha")),
        "hora": _valor_api(fila.get("hora")),
        "estado_transaccion": _valor_api(fila.get("estado_transaccion")),
        "referencia": _valor_api(fila.get("referencia")),
        "numero_autorizacion": _valor_api(fila.get("numero_autorizacion")),
        "punto_recaudo": _valor_api(fila.get("punto_recaudo"))
    }
    documento["otros_campos"] = {}
    documento["texto_extraido"] = _valor_api(fila.get("texto_extraido"))
    return documento


def api_v1_listar_documentos():
    """Lista documentos resumidos; pagina bajo demanda sin cargar OCR."""
    pagina_param = request.args.get("pagina")
    por_pagina_param = request.args.get("por_pagina")
    pagina = None
    por_pagina = None
    if pagina_param is not None or por_pagina_param is not None:
        try:
            pagina = int(pagina_param or "1")
            por_pagina = int(por_pagina_param or "100")
        except ValueError:
            return jsonify({
                "error": "'pagina' y 'por_pagina' deben ser números enteros."
            }), 400
        if pagina < 1 or por_pagina < 1 or por_pagina > 500:
            return jsonify({
                "error": "'pagina' debe ser mayor que 0 y 'por_pagina' debe estar entre 1 y 500."
            }), 400

    total = contar_facturas()
    offset = (pagina - 1) * por_pagina if pagina is not None else 0
    filas = obtener_resumenes(limit=por_pagina, offset=offset)
    respuesta = {
        "total": total,
        "documentos": [_resumen_documento_api(f) for f in filas]
    }
    if pagina is not None:
        respuesta["paginacion"] = {
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": (total + por_pagina - 1) // por_pagina
        }
    return jsonify(respuesta)


def api_v1_detalle_documento(documento_id):
    """Devuelve los datos normalizados y el texto OCR de un documento."""
    factura = obtener_por_id(documento_id)
    if not factura:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify(_detalle_documento_api(factura))


def api_descargar_json_factura(factura_id):
    """Descarga los datos extraídos de una factura como archivo JSON."""
    factura = obtener_por_id(factura_id)
    if not factura:
        return jsonify({"error": "No encontrada"}), 404

    return _respuesta_json_descargable(factura, _datos_json_factura, factura_id)


def api_v1_descargar_json_documento(documento_id):
    """Descarga el detalle normalizado v1 de un documento."""
    factura = obtener_por_id(documento_id)
    if not factura:
        return jsonify({"error": "Documento no encontrado"}), 404

    return _respuesta_json_descargable(
        factura,
        _detalle_documento_api,
        documento_id
    )


def _respuesta_json_descargable(factura, serializador, documento_id):
    datos = serializador(factura)
    nombre = secure_filename(os.path.splitext(factura["nombre_archivo"])[0])
    nombre_descarga = f"{nombre or f'factura-{documento_id}'}.json"
    contenido = BytesIO(
        json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
    )
    return send_file(
        contenido,
        mimetype="application/json",
        as_attachment=True,
        download_name=nombre_descarga
    )


def _datos_json_factura(factura):
    return {
        "ok": True,
        "archivo": factura["nombre_archivo"],
        "datos": {
            "tipo": factura["tipo_pdf"] or "",
            "proveedor": factura["proveedor"] or "",
            "nit_proveedor": factura["nit_proveedor"] or "",
            "total": factura["total"] or "No legible",
            "estado_transaccion": factura["estado_transaccion"] or "No legible",
            "fecha": factura["fecha"] or "No legible",
            "hora": factura["hora"] or "No legible",
            "referencia": factura["referencia"] or "No legible",
            "numero_autorizacion": factura["numero_autorizacion"] or "No legible",
            "punto_recaudo": factura["punto_recaudo"] or "No legible",
            "banco": factura["banco"] or "No legible"
        }
    }


def _descargar_json_lote(serializador):
    solicitud = request.get_json(silent=True)
    factura_ids = solicitud.get("factura_ids") if isinstance(solicitud, dict) else None
    if not isinstance(factura_ids, list) or not factura_ids:
        return jsonify({"error": "Selecciona al menos una factura para descargar."}), 400
    if any(
        not isinstance(factura_id, int) or isinstance(factura_id, bool) or factura_id < 1
        for factura_id in factura_ids
    ):
        return jsonify({"error": "La lista de facturas contiene identificadores no válidos."}), 400

    ids_vistos = set()
    ids_unicos = []
    for factura_id in factura_ids:
        if factura_id in ids_vistos:
            continue
        ids_vistos.add(factura_id)
        ids_unicos.append(factura_id)

    contenido = tempfile.TemporaryFile()
    nombres_usados = set()
    try:
        factura_faltante = None
        with zipfile.ZipFile(
            contenido,
            mode="w",
            compression=zipfile.ZIP_DEFLATED
        ) as archivo_zip:
            for inicio in range(0, len(ids_unicos), 500):
                lote_ids = ids_unicos[inicio:inicio + 500]
                facturas = {
                    factura["id"]: factura
                    for factura in obtener_por_ids(lote_ids)
                }
                for factura_id in lote_ids:
                    factura = facturas.get(factura_id)
                    if not factura:
                        factura_faltante = factura_id
                        break

                    base_nombre = secure_filename(
                        os.path.splitext(factura["nombre_archivo"])[0]
                    ) or f"factura-{factura_id}"
                    nombre_json = f"{base_nombre}.json"
                    if nombre_json.casefold() in nombres_usados:
                        nombre_json = f"{base_nombre}-{factura_id}.json"
                        consecutivo = 2
                        while nombre_json.casefold() in nombres_usados:
                            nombre_json = (
                                f"{base_nombre}-{factura_id}-{consecutivo}.json"
                            )
                            consecutivo += 1
                    nombres_usados.add(nombre_json.casefold())
                    ruta_json = f"Facturas JSON/{nombre_json}"
                    archivo_zip.writestr(
                        ruta_json,
                        json.dumps(
                            serializador(factura),
                            ensure_ascii=False,
                            indent=2
                        )
                    )
                if factura_faltante is not None:
                    break

        if factura_faltante is not None:
            contenido.close()
            return jsonify({
                "error": f"No se encontró la factura {factura_faltante}."
            }), 404
        contenido.seek(0)
        return send_file(
            contenido,
            mimetype="application/zip",
            as_attachment=True,
            download_name="Facturas JSON.zip"
        )
    except Exception:
        contenido.close()
        raise


def api_descargar_json_lote():
    """Descarga los JSON heredados de las facturas indicadas dentro de un ZIP."""
    return _descargar_json_lote(_datos_json_factura)


def api_v1_descargar_json_lote():
    """Descarga los JSON normalizados v1 dentro de una carpeta ZIP."""
    return _descargar_json_lote(_detalle_documento_api)


def api_borrar_historial():
    """DELETE /api/facturas → elimina todas las facturas guardadas."""
    eliminadas = borrar_todas()
    return jsonify({"ok": True, "eliminadas": eliminadas})


def registrar_rutas(app):

    app.add_url_rule(
        "/api/facturas/<int:factura_id>/miniatura",
        view_func=api_miniatura_factura,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>/previsualizar",
        view_func=api_previsualizar_factura,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>/original",
        view_func=api_abrir_documento_factura,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/previsualizar-pdf",
        view_func=api_previsualizar_pdf,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/previsualizar-pdf-completo",
        view_func=api_previsualizar_pdf_completo,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/procesar",
        view_func=api_procesar,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/procesar-lote",
        view_func=api_procesar_lote,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/facturas",
        view_func=api_listar,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/v1/documentos",
        view_func=api_v1_listar_documentos,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/v1/documentos/<int:documento_id>",
        view_func=api_v1_detalle_documento,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/v1/documentos/<int:documento_id>/json",
        view_func=api_v1_descargar_json_documento,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/v1/documentos/json/descargar-lote",
        view_func=api_v1_descargar_json_lote,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>",
        view_func=api_detalle,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/<int:factura_id>/json",
        view_func=api_descargar_json_factura,
        methods=["GET"]
    )

    app.add_url_rule(
        "/api/facturas/json/descargar-lote",
        view_func=api_descargar_json_lote,
        methods=["POST"]
    )

    app.add_url_rule(
        "/api/facturas",
        view_func=api_borrar_historial,
        methods=["DELETE"]
    )
