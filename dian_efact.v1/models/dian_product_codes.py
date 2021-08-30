from odoo import models, fields, api
import xlrd
import os, json
from odoo.http import request

class ProductCodes(models.Model):
    _name = 'dian.productcodes'

    segment_code = fields.Char(string='Código Segmento')
    segment_name = fields.Char(string='Nombre Segmento')

    family_code = fields.Char(string='Código Familia')
    family_name = fields.Char(string='Nombre Familia')

    clase_code = fields.Char(string='Código Clase')
    clase_name = fields.Char(string='Nombre Clase')

    product_code = fields.Char(string='Código Producto')
    product_name = fields.Char(string='Nombre Producto')