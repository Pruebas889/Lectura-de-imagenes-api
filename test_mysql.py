from database.mysql_manager import guardar_factura

guardar_factura(
    nombre_archivo="prueba.jpg",
    tipo_pdf="imagen",
    texto_extraido="Esto es una prueba.",
    banco="BBVA",
    total="1000",
    fecha="2026-07-03",
    proveedor="Prueba"
)