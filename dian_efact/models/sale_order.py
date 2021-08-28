from odoo import models, fields, api, tools, _

class sale_order(models.Model):

    _inherit = 'sale.order'
    journal_id = fields.Many2one('account.journal', 'Diario')