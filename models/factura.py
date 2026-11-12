# aqui se puede definir la forma de los datos

class Factura:
    """
    Representa una factura con todos sus campos siendo como una ficha de datos.
    """
    def __init__(self, nombre_archivo, tipo_pdf, texto_extraido,
                banco="", total="", fecha="", proveedor="",
                advertencia_cuota_groq=False, nit_proveedor="",
                estado_transaccion="", hora="", referencia="",
                numero_autorizacion="", punto_recaudo="", id=None):
        
        self.id = id
        self.nombre_archivo = nombre_archivo
        self.tipo_pdf = tipo_pdf
        self.texto_extraido = texto_extraido
        self.banco = banco
        self.total = total
        self.fecha = fecha
        self.proveedor = proveedor
        self.advertencia_cuota_groq = advertencia_cuota_groq
        self.nit_proveedor = nit_proveedor
        self.estado_transaccion = estado_transaccion
        self.hora = hora
        self.referencia = referencia
        self.numero_autorizacion = numero_autorizacion
        self.punto_recaudo = punto_recaudo

    def __repr__(self):
        
        #__repr define como se imprime el obeto en consola
        #util para debug
        return f"<Factura({self.nombre_archivo}, {self.tipo_pdf}, {self.banco}, {self.total}, {self.fecha}, {self.proveedor})>"
