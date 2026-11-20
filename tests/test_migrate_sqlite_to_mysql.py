import pytest

from database import migrate_sqlite_to_mysql, sqlite_manager


class _CursorDestino:
    def __init__(self, filas):
        self.filas = filas
        self.consulta = None

    def executemany(self, _consulta, filas):
        self.filas.extend(filas)

    def execute(self, consulta):
        self.consulta = consulta

    def fetchone(self):
        assert self.consulta == "SELECT COUNT(*) FROM facturas"
        return (len(self.filas),)

    def close(self):
        pass


class _ConexionDestino:
    def __init__(self, filas):
        self.filas = filas
        self.confirmada = False

    def cursor(self):
        return _CursorDestino(self.filas)

    def commit(self):
        self.confirmada = True

    def rollback(self):
        self.filas.clear()

    def close(self):
        pass


def test_migrar_copia_todos_los_registros_en_lotes(
    monkeypatch, tmp_path
):
    ruta_sqlite = tmp_path / "facturas.db"
    monkeypatch.setattr(sqlite_manager, "DB_PATH", str(ruta_sqlite))
    sqlite_manager.crear_tabla()
    ids = [
        sqlite_manager.guardar_factura(
            nombre_archivo=f"comprobante-{indice}.png",
            tipo_pdf="imagen",
            texto_extraido=f"OCR {indice}",
            banco="Nequi"
        )
        for indice in range(3)
    ]

    filas_destino = []
    conexion_destino = _ConexionDestino(filas_destino)
    monkeypatch.setattr(
        migrate_sqlite_to_mysql.mysql_manager,
        "crear_tabla",
        lambda: None
    )
    monkeypatch.setattr(
        migrate_sqlite_to_mysql.mysql_manager,
        "contar_facturas",
        lambda: len(filas_destino) if conexion_destino.confirmada else 0
    )
    monkeypatch.setattr(
        migrate_sqlite_to_mysql.mysql_manager,
        "obtener_conexion",
        lambda: conexion_destino
    )

    cantidad = migrate_sqlite_to_mysql.migrar(ruta_sqlite, tamano_lote=2)

    assert cantidad == 3
    assert [fila[0] for fila in filas_destino] == ids
    assert [fila[3] for fila in filas_destino] == ["OCR 0", "OCR 1", "OCR 2"]
    assert conexion_destino.confirmada


def test_migrar_se_detiene_si_mysql_no_esta_vacio(monkeypatch, tmp_path):
    ruta_sqlite = tmp_path / "facturas.db"
    monkeypatch.setattr(sqlite_manager, "DB_PATH", str(ruta_sqlite))
    sqlite_manager.crear_tabla()
    monkeypatch.setattr(
        migrate_sqlite_to_mysql.mysql_manager,
        "crear_tabla",
        lambda: None
    )
    monkeypatch.setattr(
        migrate_sqlite_to_mysql.mysql_manager,
        "contar_facturas",
        lambda: 1
    )

    with pytest.raises(RuntimeError, match="tabla MySQL ya contiene 1"):
        migrate_sqlite_to_mysql.migrar(ruta_sqlite)


def test_migrar_rechaza_tamano_de_lote_no_positivo():
    with pytest.raises(ValueError, match="mayor que cero"):
        migrate_sqlite_to_mysql.migrar("no-se-usa.db", tamano_lote=0)
