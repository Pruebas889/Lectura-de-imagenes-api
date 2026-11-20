import mysql.connector

from config.settings import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE,
    MYSQL_USER,
    MYSQL_PASSWORD,
)


def obtener_conexion():
    """
    Crea una conexión a MariaDB/MySQL.
    """

    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DATABASE,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=False
    )


def crear_tabla():
    """
    Crea la tabla facturas si no existe.
    """

    conn = obtener_conexion()
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                nombre_archivo VARCHAR(255) NOT NULL,
                tipo_pdf VARCHAR(50),
                texto_extraido LONGTEXT,
                banco VARCHAR(255),
                total VARCHAR(100),
                fecha VARCHAR(50),
                proveedor VARCHAR(255),
                nit_proveedor VARCHAR(100),
                estado_transaccion VARCHAR(255),
                hora VARCHAR(50),
                referencia VARCHAR(255),
                numero_autorizacion VARCHAR(255),
                punto_recaudo VARCHAR(255),
                archivo_original VARCHAR(255),
                fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        columnas = {
            "texto_extraido": "LONGTEXT",
            "nit_proveedor": "VARCHAR(100)",
            "estado_transaccion": "VARCHAR(255)",
            "hora": "VARCHAR(50)",
            "referencia": "VARCHAR(255)",
            "numero_autorizacion": "VARCHAR(255)",
            "punto_recaudo": "VARCHAR(255)",
            "archivo_original": "VARCHAR(255)",
        }
        for columna, tipo in columnas.items():
            cursor.execute(f"SHOW COLUMNS FROM facturas LIKE '{columna}'")
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE facturas ADD COLUMN {columna} {tipo}")

        cursor.execute(
            "SHOW INDEX FROM facturas WHERE Key_name = %s",
            ("idx_facturas_fecha_id",)
        )
        if not cursor.fetchone():
            cursor.execute("""
                CREATE INDEX idx_facturas_fecha_id
                ON facturas (fecha_procesado, id)
            """)

        conn.commit()
        print("Tabla 'facturas' lista.")
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def guardar_factura(
    nombre_archivo,
    tipo_pdf,
    texto_extraido="",
    banco="",
    total="",
    fecha="",
    proveedor="",
    archivo_original="",
    nit_proveedor="",
    estado_transaccion="",
    hora="",
    referencia="",
    numero_autorizacion="",
    punto_recaudo=""
):
    """
    Guarda una factura en MySQL.
    """

    conn = obtener_conexion()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO facturas
            (
                nombre_archivo,
                tipo_pdf,
                texto_extraido,
                banco,
                total,
                fecha,
                proveedor,
                archivo_original,
                nit_proveedor,
                estado_transaccion,
                hora,
                referencia,
                numero_autorizacion,
                punto_recaudo
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            nombre_archivo,
            tipo_pdf,
            texto_extraido,
            banco,
            total,
            fecha,
            proveedor,
            archivo_original,
            nit_proveedor,
            estado_transaccion,
            hora,
            referencia,
            numero_autorizacion,
            punto_recaudo
        ))

        conn.commit()

        print(f"Guardado: {nombre_archivo}")
        return cursor.lastrowid

    finally:

        cursor.close()
        conn.close()


def obtener_todas():
    """
    Devuelve todas las facturas.
    """

    conn = obtener_conexion()

    try:

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM facturas
            ORDER BY fecha_procesado DESC
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


def obtener_resumenes(limit=None, offset=0):
    """Devuelve campos de listado, sin cargar los textos OCR."""
    conn = obtener_conexion()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        consulta = """
            SELECT id, nombre_archivo, tipo_pdf, banco, total, fecha,
                   proveedor, fecha_procesado
            FROM facturas
            ORDER BY fecha_procesado DESC, id DESC
        """
        parametros = ()
        if limit is not None:
            consulta += " LIMIT %s OFFSET %s"
            parametros = (limit, offset)
        cursor.execute(consulta, parametros)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def obtener_por_ids(factura_ids):
    """Obtiene varias facturas en bloques acotados."""
    filas_por_id = {}
    for inicio in range(0, len(factura_ids), 500):
        lote = factura_ids[inicio:inicio + 500]
        marcadores = ", ".join("%s" for _ in lote)
        conn = obtener_conexion()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT * FROM facturas WHERE id IN ({marcadores})",
                lote
            )
            filas_por_id.update((fila["id"], fila) for fila in cursor.fetchall())
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()
    return [
        filas_por_id[factura_id]
        for factura_id in factura_ids
        if factura_id in filas_por_id
    ]


def obtener_por_id(factura_id):
    """
    Devuelve una factura por ID.
    """

    conn = obtener_conexion()

    try:

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM facturas
            WHERE id = %s
        """, (factura_id,))

        return cursor.fetchone()

    finally:

        cursor.close()
        conn.close()


def borrar_todas():
    """Elimina todas las facturas y devuelve cuántos registros se borraron."""
    conn = obtener_conexion()

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM facturas")
        eliminadas = cursor.rowcount
        conn.commit()
        return eliminadas
    finally:
        cursor.close()
        conn.close()


def contar_facturas():
    """Devuelve el número de facturas guardadas."""
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM facturas")
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()