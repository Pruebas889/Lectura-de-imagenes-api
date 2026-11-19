import json
from io import BytesIO
import zipfile
from datetime import datetime

from flask import Flask

import controllers.api_controller as api_controller


def _cliente_api():
    app = Flask(__name__)
    api_controller.registrar_rutas(app)
    return app.test_client()


def _factura():
    return {
        "id": 7,
        "nombre_archivo": "comprobante.png",
        "tipo_pdf": "comprobante_transferencia",
        "texto_extraido": "Transferencia aprobada\nValor: 50000",
        "banco": "Nequi",
        "total": "50000",
        "fecha": "2026-04-19",
        "proveedor": "",
        "nit_proveedor": None,
        "estado_transaccion": "Aprobada",
        "hora": "10:10",
        "referencia": "ABC123",
        "numero_autorizacion": "",
        "punto_recaudo": None,
        "fecha_procesado": datetime(2026, 4, 19, 10, 11)
    }


def test_v1_lista_resumen_sin_texto_ocr(monkeypatch):
    factura_mysql = _factura()
    factura_sqlite = {
        **factura_mysql,
        "id": 8,
        "fecha_procesado": "2026-04-19 10:11:00"
    }
    monkeypatch.setattr(
        api_controller,
        "obtener_todas",
        lambda: [factura_mysql, factura_sqlite]
    )
    cliente = _cliente_api()

    respuesta = cliente.get("/api/v1/documentos")

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    cuerpo = respuesta.get_json()
    assert cuerpo["total"] == 2
    documento = next(item for item in cuerpo["documentos"] if item["id"] == 7)
    documento_sqlite = next(item for item in cuerpo["documentos"] if item["id"] == 8)
    assert documento["archivo"] == {
        "nombre": "comprobante.png",
        "original_url": "/api/facturas/7/original"
    }
    assert documento["documento"] == {
        "tipo": "comprobante_transferencia",
        "entidad": "Nequi"
    }
    assert documento["procesamiento"]["fecha"] == "2026-04-19T10:11:00"
    assert "texto_extraido" not in documento
    assert "datos" not in documento
    assert documento_sqlite["procesamiento"]["fecha"] == "2026-04-19T10:11:00"


def test_v1_detalle_incluye_datos_texto_y_nulos(monkeypatch):
    factura = _factura()
    monkeypatch.setattr(
        api_controller,
        "obtener_por_id",
        lambda documento_id: factura if documento_id == factura["id"] else None
    )
    cliente = _cliente_api()

    respuesta = cliente.get("/api/v1/documentos/7")

    assert respuesta.status_code == 200
    documento = respuesta.get_json()
    assert documento["datos"]["total"] == "50000"
    assert documento["datos"]["proveedor"] is None
    assert documento["datos"]["numero_autorizacion"] is None
    assert documento["otros_campos"] == {}
    assert documento["texto_extraido"] == factura["texto_extraido"]


def test_v1_detalle_inexistente_devuelve_404(monkeypatch):
    monkeypatch.setattr(api_controller, "obtener_por_id", lambda _documento_id: None)
    cliente = _cliente_api()

    respuesta = cliente.get("/api/v1/documentos/999")

    assert respuesta.status_code == 404
    assert respuesta.get_json() == {"error": "Documento no encontrado"}


def test_v1_descarga_json_usa_el_mismo_detalle(monkeypatch):
    factura = _factura()
    monkeypatch.setattr(
        api_controller,
        "obtener_por_id",
        lambda documento_id: factura if documento_id == factura["id"] else None
    )
    cliente = _cliente_api()

    respuesta = cliente.get("/api/v1/documentos/7/json")
    detalle = cliente.get("/api/v1/documentos/7").get_json()

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/json"
    assert "attachment" in respuesta.headers["Content-Disposition"]
    assert respuesta.get_json() == detalle


def test_v1_descarga_lote_incluye_el_detalle_normalizado(monkeypatch):
    factura = _factura()
    monkeypatch.setattr(
        api_controller,
        "obtener_por_id",
        lambda documento_id: factura if documento_id == factura["id"] else None
    )
    cliente = _cliente_api()

    respuesta = cliente.post(
        "/api/v1/documentos/json/descargar-lote",
        json={"factura_ids": [7]}
    )

    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/zip"
    with zipfile.ZipFile(BytesIO(respuesta.data)) as archivo_zip:
        nombres = archivo_zip.namelist()
        assert len(nombres) == 1
        datos_json = json.loads(archivo_zip.read(nombres[0]))
    assert datos_json == cliente.get("/api/v1/documentos/7").get_json()
