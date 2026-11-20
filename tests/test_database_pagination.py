import sqlite3

from database import sqlite_manager


def test_sqlite_resumen_paginado_omite_ocr(monkeypatch, tmp_path):
    database_path = tmp_path / "facturas.db"
    monkeypatch.setattr(sqlite_manager, "DB_PATH", str(database_path))
    sqlite_manager.crear_tabla()

    for indice in range(3):
        sqlite_manager.guardar_factura(
            nombre_archivo=f"comprobante-{indice}.png",
            tipo_pdf="imagen",
            texto_extraido=f"OCR completo {indice}",
            proveedor=f"Proveedor {indice}"
        )

    primera_pagina = sqlite_manager.obtener_resumenes(limit=2, offset=0)
    segunda_pagina = sqlite_manager.obtener_resumenes(limit=2, offset=2)

    assert sqlite_manager.contar_facturas() == 3
    assert len(primera_pagina) == 2
    assert [fila["id"] for fila in primera_pagina] == [3, 2]
    assert [fila["id"] for fila in segunda_pagina] == [1]
    assert "texto_extraido" not in primera_pagina[0].keys()


def test_sqlite_busca_ids_en_bloques_de_hasta_500(monkeypatch, tmp_path):
    database_path = tmp_path / "facturas.db"
    monkeypatch.setattr(sqlite_manager, "DB_PATH", str(database_path))
    sqlite_manager.crear_tabla()

    with sqlite3.connect(database_path) as conn:
        conn.executemany(
            "INSERT INTO facturas (nombre_archivo) VALUES (?)",
            [(f"comprobante-{indice}.png",) for indice in range(1001)]
        )

    ids = list(range(1001, 0, -1))
    facturas = sqlite_manager.obtener_por_ids(ids)

    assert [factura["id"] for factura in facturas] == ids
