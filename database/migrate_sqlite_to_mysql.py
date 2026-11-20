"""Copia las facturas de SQLite a una instancia MySQL/MariaDB vacía."""

import argparse
import sqlite3
from pathlib import Path

from config.settings import DB_PATH
from database import mysql_manager


COLUMNAS = (
    "id",
    "nombre_archivo",
    "tipo_pdf",
    "texto_extraido",
    "banco",
    "total",
    "fecha",
    "proveedor",
    "nit_proveedor",
    "estado_transaccion",
    "hora",
    "referencia",
    "numero_autorizacion",
    "punto_recaudo",
    "archivo_original",
    "fecha_procesado",
)

INSERTAR_FACTURA = """
    INSERT INTO facturas (
        id, nombre_archivo, tipo_pdf, texto_extraido, banco, total, fecha,
        proveedor, nit_proveedor, estado_transaccion, hora, referencia,
        numero_autorizacion, punto_recaudo, archivo_original, fecha_procesado
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
"""


def migrar(ruta_sqlite=DB_PATH, tamano_lote=500):
    """Migra todas las filas, preservando IDs, fechas y contenido OCR."""
    if tamano_lote < 1:
        raise ValueError("El tamaño del lote debe ser mayor que cero.")

    archivo_sqlite = Path(ruta_sqlite).resolve()
    if not archivo_sqlite.is_file():
        raise FileNotFoundError(f"No existe la base SQLite: {archivo_sqlite}")

    uri = archivo_sqlite.as_uri() + "?mode=ro"
    origen = sqlite3.connect(uri, uri=True)
    try:
        origen.row_factory = sqlite3.Row
        columnas_origen = {
            fila["name"] for fila in origen.execute("PRAGMA table_info(facturas)")
        }
        faltantes = set(COLUMNAS) - columnas_origen
        if faltantes:
            raise RuntimeError(
                "La tabla SQLite no contiene las columnas requeridas: "
                + ", ".join(sorted(faltantes))
            )

        mysql_manager.crear_tabla()
        existentes = mysql_manager.contar_facturas()
        if existentes:
            raise RuntimeError(
                f"La tabla MySQL ya contiene {existentes} factura(s). "
                "La migración requiere una tabla vacía para evitar duplicados "
                "o sobrescribir datos."
            )

        total_origen = origen.execute(
            "SELECT COUNT(*) FROM facturas"
        ).fetchone()[0]
        destino = mysql_manager.obtener_conexion()
        cursor_destino = None
        try:
            cursor_destino = destino.cursor()
            consulta = (
                "SELECT " + ", ".join(COLUMNAS) + " FROM facturas ORDER BY id"
            )
            filas = origen.execute(consulta)
            migradas = 0
            while lote := filas.fetchmany(tamano_lote):
                cursor_destino.executemany(
                    INSERTAR_FACTURA,
                    [tuple(fila[columna] for columna in COLUMNAS) for fila in lote],
                )
                migradas += len(lote)

            if migradas != total_origen:
                raise RuntimeError(
                    f"Migración incompleta: se leyeron {migradas} de "
                    f"{total_origen} facturas de SQLite."
                )
            cursor_destino.execute("SELECT COUNT(*) FROM facturas")
            total_destino = cursor_destino.fetchone()[0]
            if total_destino != total_origen:
                raise RuntimeError(
                    f"Verificación fallida: SQLite tiene {total_origen} "
                    f"facturas y MySQL tiene {total_destino}."
                )
            destino.commit()
            return migradas
        except Exception:
            destino.rollback()
            raise
        finally:
            if cursor_destino is not None:
                cursor_destino.close()
            destino.close()
    finally:
        origen.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Copia las facturas desde SQLite a una tabla vacía de MySQL/MariaDB. "
            "No modifica ni elimina la base SQLite."
        )
    )
    parser.add_argument(
        "--source",
        default=DB_PATH,
        help="Ruta a facturas.db (predeterminada: %(default)s)",
    )
    argumentos = parser.parse_args()
    cantidad = migrar(argumentos.source)
    print(f"Migración completada: {cantidad} factura(s) copiadas.")


if __name__ == "__main__":
    main()
