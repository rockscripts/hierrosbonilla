from odoo import models, fields, api, tools, _

class account_invoice(models.Model):

    _inherit = 'account.tax'

    dian_tributo = fields.Selection([('01','Valor total de IVA'),('02','Valor total de impuesto al consumo'),('03','Valor total de ICA'),('04','Valor total de impuesto nacional al consumo'),('05','ReteIVA'),('06','ReteFuente'),('07','ReteICA'),('08','ReteCREE'),('22','Bolsas')], string='Dian Tributo', default='01')
   # _columns = {"dian_tributo":fields.Selection([('01','Valor total de IVA'),('02','Valor total de impuesto al consumo'),('03','Valor total de ICA'),('04','Valor total de impuesto nacional al consumo')], string='Dian Tributo', default='01')}