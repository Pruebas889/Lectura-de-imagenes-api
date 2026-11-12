from contextlib import closing
import os
import sqlite3

from config.settings import DB_PATH 


def asegurar_carpeta_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def crear_tabla():
    """
    Crear la tabla 'facturas' en la base de datos si no existe todavia.
    """

    #sqlite3.connect() abre o crea si no existe en su defecto, el archivo .db
    # closing garantiza el cierre; el gestor de contexto de sqlite solo confirma transacciones.

    asegurar_carpeta_db()

    with closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")

        cursor = conn.cursor() #Escribe en la BD

        #Este bloque creara la tabla con sus columnas.
        # IF NOT EXISTS = "solo crea la tabla si no exitste aun"

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_archivo TEXT NOT NULL,
                tipo_pdf TEXT,
                texto_extraido TEXT,
                banco TEXT,
                total TEXT,
                fecha TEXT,
                proveedor TEXT,
                nit_proveedor TEXT,
                estado_transaccion TEXT,
                hora TEXT,
                referencia TEXT,
                numero_autorizacion TEXT,
                punto_recaudo TEXT,
                archivo_original TEXT,
                fecha_procesado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columnas = {
            fila[1]
            for fila in conn.execute("PRAGMA table_info(facturas)").fetchall()
        }
        if "archivo_original" not in columnas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN archivo_original TEXT")
        for columna in (
            "nit_proveedor",
            "estado_transaccion",
            "hora",
            "referencia",
            "numero_autorizacion",
            "punto_recaudo"
        ):
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE facturas ADD COLUMN {columna} TEXT")
        conn.commit() #Guarda los cambios en la BD
        print("Tabla'facturas lista.")

def guardar_factura(
    nombre_archivo,
    tipo_pdf,
    texto_extraido,
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
    Inserta una factura nuea en la base de datos.
    Recibe los datos ya procesados y los guarda.
    
    """
    asegurar_carpeta_db()

    with closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        #Los signos ? son marcadores de posicion para evitar inyecciones SQL. Los valores se pasan como tupla en el segundo argumento de execute().

        cursor.execute("""
            INSERT INTO facturas
            (
                nombre_archivo, tipo_pdf, texto_extraido, banco, total,
                fecha, proveedor, archivo_original, nit_proveedor,
                estado_transaccion, hora, referencia, numero_autorizacion,
                punto_recaudo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre_archivo, tipo_pdf, texto_extraido, banco, total,
            fecha, proveedor, archivo_original, nit_proveedor,
            estado_transaccion, hora, referencia, numero_autorizacion,
            punto_recaudo
        ))

        conn.commit()
        print(f"Guardado: {nombre_archivo}")
        return cursor.lastrowid


def obtener_todas():
    """
    Trae todas las facturas en la base de datos y retorna una lista de filas)
    """

    with closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")

        #row_factory hace que cada fila se pueda usar de diccionario
        #Asi puedes escribir fila["Banco"] en vez de fila [4]
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facturas ORDER BY fecha_procesado DESC")
        return cursor.fetchall() #trae todos los resultados
    

def obtener_por_id(factura_id):
    """
    Trae una factura por su ID y retorna un diccionario con sus datos.
    Si no encuentra la factura, retorna None.
    """

    with closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facturas WHERE id = ?", (factura_id,))
        return cursor.fetchone() #trae solo una fila


def borrar_todas():
    """Elimina todas las facturas y devuelve cuántos registros se borraron."""
    with closing(sqlite3.connect(DB_PATH, timeout=30)) as conn:
        cursor = conn.execute("DELETE FROM facturas")
        conn.commit()
        return cursor.rowcount
