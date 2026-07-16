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

    try:

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (

                id INT AUTO_INCREMENT PRIMARY KEY,

                nombre_archivo VARCHAR(255) NOT NULL,

                tipo_pdf VARCHAR(50),


                banco VARCHAR(255),

                total VARCHAR(100),

                fecha VARCHAR(50),

                proveedor VARCHAR(255),

                fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
        """)

        conn.commit()

        print("Tabla 'facturas' lista.")

    finally:

        cursor.close()
        conn.close()


def guardar_factura(
    nombre_archivo,
    tipo_pdf,
    banco="",
    total="",
    fecha="",
    proveedor=""
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
                banco,
                total,
                fecha,
                proveedor
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            nombre_archivo,
            tipo_pdf,
            banco,
            total,
            fecha,
            proveedor
        ))

        conn.commit()

        print(f"Guardado: {nombre_archivo}")

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