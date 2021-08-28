from odoo import models, fields, api, tools, _
from odoo.http import request
import json

class website(models.Model):

    _inherit = 'website'

    def websites_for_company(self,website_id):
        query = "select company_id from website where id = '"+str(website_id)+"'"
        request.cr.execute(query)
        website = request.cr.dictfetchone()
        return  {
                    'company_id': website['company_id']
                }