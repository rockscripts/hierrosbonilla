from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import osv

class ir_sequence(models.Model):
    _inherit = 'ir.sequence'

