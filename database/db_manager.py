from config.settings import DB_ENGINE

if DB_ENGINE.lower() == "mysql":

    from database.mysql_manager import (
        crear_tabla,
        guardar_factura,
        obtener_todas,
        obtener_por_id
    )

else:

    from database.sqlite_manager import (
        crear_tabla,
        guardar_factura,
        obtener_todas,
        obtener_por_id
    )