from odoo import models, fields, api, tools, _
from odoo.http import request
import json

class website_page(models.Model):

    _inherit = 'website.page'

    is_for_current_company = fields.Boolean('Multicompany', compute='_is_for_current_company')
    #@api.depends('is_for_current_company')
    #def _is_for_current_company(self): 
    #    query = "select id, company_id from res_users where id = '" + str(request.uid) + "'"
    #    request.cr.execute(query)
    #    res_company = request.cr.dictfetchone()
    #    
    #    query = "select company_id from website where id any (" + str(self.ids) + ") "
    #    with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
    #        json.dump(query, outfile)
#
    #    request.cr.execute(query)
    #    res_user = request.cr.dictfetchone()
#
    #    if('company_id' not in res_company or 'company_id' not in res_user):
    #        self.is_for_current_company = False
    #        return False
    #    else:
    #        if(int(res_company['company_id']) == int(res_user['company_id'])):
    #            self.is_for_current_company = True
    #            return True
    #        else:
    #            self.is_for_current_company = False
    #            return False