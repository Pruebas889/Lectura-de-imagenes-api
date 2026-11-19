import os
import sys
from flask import Flask, jsonify, render_template, request


def _configurar_stdout_utf8():
    """Evita fallos en Windows cuando el terminal no soporta ciertos caracteres Unicode."""
    stream = sys.stdout
    original_write = stream.write

    def safe_write(data):
        try:
            return original_write(data)
        except UnicodeEncodeError:
            encoding = getattr(stream, "encoding", None) or "utf-8"
            text = data.encode(encoding, errors="replace").decode(encoding, errors="replace")
            return original_write(text)

    stream.write = safe_write

    if hasattr(sys.stderr, "write"):
        err_stream = sys.stderr
        err_original = err_stream.write

        def safe_err_write(data):
            try:
                return err_original(data)
            except UnicodeEncodeError:
                encoding = getattr(err_stream, "encoding", None) or "utf-8"
                text = data.encode(encoding, errors="replace").decode(encoding, errors="replace")
                return err_original(text)

        err_stream.write = safe_err_write


_configurar_stdout_utf8()

from database.db_manager import crear_tabla, obtener_todas, obtener_por_id
from controllers.api_controller import registrar_rutas
from config.settings import MAX_UPLOAD_BYTES

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

crear_tabla()

registrar_rutas(app)


@app.after_request
def evitar_cache_historial_facturas(response):
    if (
        request.path == "/individual"
        or request.path.startswith("/factura/")
        or request.path == "/api/facturas"
        or request.path == "/api/v1/documentos"
        or request.path.startswith("/api/v1/documentos/")
        or request.path == "/cargue-masivo"
        or request.path == "/historial"
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(413)
def archivo_demasiado_grande(_error):
    return jsonify({
        "error": "La solicitud supera el tamaño máximo configurado para las cargas."
    }), 413


@app.route("/")
def index():
    return render_template("modo_carga.html")


@app.route("/individual")
def cargue_individual():
    return render_template("index.html")


@app.route("/cargue-masivo")
def cargue_masivo():
    return render_template("cargue_masivo.html")


@app.route("/historial")
def historial():
    return render_template(
        "historial.html",
        facturas=obtener_todas()
    )


@app.route("/factura/<int:factura_id>")
def detalle_factura(factura_id):

    factura = obtener_por_id(factura_id)

    if not factura:
        return "Factura no encontrada", 404

    return render_template(
        "index.html",
        factura_seleccionada=factura
    )

if __name__ == "__main__":

    print("API corriendo en:        http://127.0.0.1:5000")
    print("Endpoint para subir:     POST /api/procesar")
    print("Endpoint para listar:    GET  /api/facturas")

    app.run(
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )