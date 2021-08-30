from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import osv

class delivery_carrier(models.Model):
    _name = "delivery.carrier"
    _inherit = "delivery.carrier"

    nit = fields.Char('NIT', required=False, translate=True)