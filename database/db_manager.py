from config.settings import DB_ENGINE

if DB_ENGINE == "mysql":
    from database.mysql_manager import (
        crear_tabla,
        guardar_factura,
        obtener_todas,
        obtener_resumenes,
        obtener_por_ids,
        obtener_por_id,
        contar_facturas,
        borrar_todas
    )
elif DB_ENGINE == "sqlite":
    from database.sqlite_manager import (
        crear_tabla,
        guardar_factura,
        obtener_todas,
        obtener_resumenes,
        obtener_por_ids,
        obtener_por_id,
        contar_facturas,
        borrar_todas
    )
else:
    raise ValueError(
        f"Motor de base de datos no soportado: {DB_ENGINE!r}. "
        "Usa 'sqlite' o 'mysql'."
    )