import unittest

from controllers.api_controller import _datos_json_factura
from extractors.regex_extractor import (
    completar_campos_no_legibles,
    extraer_con_regex
)


class ExtraerCamposFacturaTests(unittest.TestCase):
    def test_extracts_wompi_fields_and_english_month_date(self):
        texto = """
        TRANSACCION EXITOSA
        Monto: $1.327.978,00
        Fecha: MAY 22 2026 - 11:59:32
        Referencia: 100200101863
        Nro. Autorizacion: 654321
        Punto de recaudo: 019
        Corresponsal 190 Bancolombla
        """

        datos = extraer_con_regex(texto)

        self.assertEqual(datos["fecha"], "2026-05-22")
        self.assertEqual(datos["hora"], "11:59:32")
        self.assertEqual(datos["total"], "1.327.978,00")
        self.assertEqual(datos["estado_transaccion"], "TRANSACCION EXITOSA")
        self.assertEqual(datos["referencia"], "100200101863")
        self.assertEqual(datos["numero_autorizacion"], "654321")
        self.assertEqual(datos["punto_recaudo"], "019")
        self.assertEqual(datos["banco"], "BANCOLOMBIA")

    def test_extracts_bbva_transaction_and_payment_date(self):
        texto = """
        BBVA
        FECHA: 22/05/2026 HORA: 11:55:37
        PUNTO DE VENTA: 0395714946
        NUMERO TRANSACCION: 35561982
        VALOR PAGO: $1,950,010
        TIPO TRANSACCION RECAUDO
        """

        datos = extraer_con_regex(texto)

        self.assertEqual(datos["fecha"], "2026-05-22")
        self.assertEqual(datos["hora"], "11:55:37")
        self.assertEqual(datos["total"], "1,950,010")
        self.assertEqual(datos["referencia"], "35561982")
        self.assertEqual(datos["punto_recaudo"], "0395714946")
        self.assertEqual(datos["banco"], "BBVA")
        self.assertEqual(datos["estado_transaccion"], "")

    def test_parses_spanish_date_and_afternoon_time(self):
        datos = extraer_con_regex(
            "FECHA DEL PAGO: 22 DE MAYO DE 2026\n"
            "HORA: 12:05 P.M.\n"
            "TOTAL A PAGAR: $ 1.950.010,00"
        )

        self.assertEqual(datos["fecha"], "2026-05-22")
        self.assertEqual(datos["hora"], "12:05")
        self.assertEqual(datos["total"], "1.950.010,00")

    def test_handles_common_ocr_typos_and_bank_reference_labels(self):
        datos = extraer_con_regex(
            "RRN: 123456 Aprob. 9876\n"
            "PUNTO IME VENTA: 03957\n"
            "YALOR FAGO: $ 1.950.010"
        )

        self.assertEqual(datos["referencia"], "123456")
        self.assertEqual(datos["numero_autorizacion"], "9876")
        self.assertEqual(datos["punto_recaudo"], "03957")
        self.assertEqual(datos["total"], "1.950.010")

    def test_extracts_authorization_from_approval_number_label(self):
        datos = extraer_con_regex("NUMERO DE APROBACION: 654321")

        self.assertEqual(datos["numero_autorizacion"], "654321")

    def test_handles_rrn_misread_as_ren(self):
        datos = extraer_con_regex("REN: 123456 Aprob. 9876")

        self.assertEqual(datos["referencia"], "123456")
        self.assertEqual(datos["numero_autorizacion"], "9876")

    def test_ignores_due_date_and_item_count_as_total(self):
        datos = extraer_con_regex(
            "FECHA DE VENCIMIENTO: 25/05/2026\n"
            "FECHA DE PAGO: 22/05/2026\n"
            "TOTAL ITEMS: 3\n"
            "TOTAL COMPRA: $ 1.200,00"
        )

        self.assertEqual(datos["fecha"], "2026-05-22")
        self.assertEqual(datos["total"], "1.200,00")

    def test_marks_unidentified_required_fields_as_unreadable(self):
        datos = completar_campos_no_legibles(
            extraer_con_regex("Texto sin campos estructurados.")
        )

        for campo in (
            "fecha",
            "hora",
            "total",
            "estado_transaccion",
            "referencia",
            "numero_autorizacion",
            "punto_recaudo",
            "banco"
        ):
            with self.subTest(campo=campo):
                self.assertEqual(datos[campo], "No legible")

    def test_api_json_uses_unreadable_for_legacy_empty_fields(self):
        factura = {
            "nombre_archivo": "recibo.jpg",
            "tipo_pdf": "imagen",
            "proveedor": "",
            "nit_proveedor": "",
            "total": "",
            "estado_transaccion": "",
            "fecha": "",
            "hora": "",
            "referencia": "",
            "numero_autorizacion": "",
            "punto_recaudo": "",
            "banco": ""
        }

        datos = _datos_json_factura(factura)["datos"]

        for campo in (
            "fecha",
            "hora",
            "total",
            "estado_transaccion",
            "referencia",
            "numero_autorizacion",
            "punto_recaudo",
            "banco"
        ):
            with self.subTest(campo=campo):
                self.assertEqual(datos[campo], "No legible")


if __name__ == "__main__":
    unittest.main()
