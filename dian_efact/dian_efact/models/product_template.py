from odoo import models, fields, api
import xlrd
import os, json
from odoo.http import request

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(
                            string="HS Code",
                            help="Standardized code for international shipping and goods declaration. At the moment, only used for the FedEx shipping provider.",
                         )

    service_to_purchase = fields.Boolean("Purchase Automatically", help="If ticked, each time you sell this product through a SO, a RfQ is automatically created to buy the product. Tip: don't forget to set a vendor on the product.")    
    sunat_product_code = fields.Char(string="Código Producto")
    dian_is_product_discount = fields.Boolean("¿Producto descuento?", help="Indica si el producto es tipo descuento global ")
    dian_discount_type = fields.Selection(selection='_get_discount_types', string="Tipo descuento", default='09-Descuento general')
    dian_brand_name = fields.Char(string="Marca")
    dian_item_model = fields.Char(string="Modelo")

    def _get_discount_types(self):
        discount_types = []
        discount_types.append((str("00")+str("-")+str("Descuento por impuesto asumido"), str("Descuento por impuesto asumido")))
        discount_types.append((str("01")+str("-")+str("Pague uno lleve otro"), str("Pague uno lleve otro")))
        discount_types.append((str("02")+str("-")+str("Descuentos contractulales"), str("Descuentos contractulales")))
        discount_types.append((str("03")+str("-")+str("Descuento por pronto pago"), str("Descuento por pronto pago")))
        discount_types.append((str("04")+str("-")+str("Envío gratis"), str("Envío gratis")))
        discount_types.append((str("05")+str("-")+str("Descuentos escpecíficos por inventarios"), str("Descuentos escpecíficos por inventarios")))
        discount_types.append((str("06")+str("-")+str("Descuento por monto de compras"), str("Descuento por monto de compras")))
        discount_types.append((str("07")+str("-")+str("Descuento de temporada"), str("Descuento de temporada")))
        discount_types.append((str("08")+str("-")+str("Descuento por actualización de productos / servicios"), str("Descuento por actualización de productos / servicios")))
        discount_types.append((str("09")+str("-")+str("Descuento general"), str("Descuento general")))
        discount_types.append((str("10")+str("-")+str("Descuento por volumen"), str("Descuento por volumen")))
        discount_types.append((str("11")+str("-")+str("Otro descuento"), str("Otro descuento")))
        return discount_types