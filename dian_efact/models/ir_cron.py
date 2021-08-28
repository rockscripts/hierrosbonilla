from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.osv import osv

class ir_cron(models.Model):
    _inherit = 'ir.cron'

    dian_start_date = fields.Date(string="Desde la fecha", name="dian_start_date")