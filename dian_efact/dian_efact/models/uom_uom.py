from odoo import api, fields, models, _

class Uom(models.Model):
    
    _inherit = 'uom.uom'

    dian_unit_code = fields.Char("Dian / Unidad de medida", name="dian_unit_code", default='')   