# -*- coding: utf-8 -*-
from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo import http
from pprint import pprint
import importlib
import os, json
from odoo.http import request
from lxml import etree
from lxml.builder import E
from collections import defaultdict
from odoo.exceptions import AccessDenied

from dianservice.dianservice import Service
import logging

_logger = logging.getLogger(__name__)

class Users(models.Model):
    
    _inherit = 'res.users'

    @api.multi
    def _is_system(self):
        self.ensure_one()
        return True

    company_has_parent = fields.Integer('flag Company ha parent', compute='_compute_company_has_parent')
    @api.depends('company_has_parent')
    def _compute_company_has_parent(self):
        query = "select parent_id from res_company where id = '" + str(self.company_id.id) + "'"

        request.cr.execute(query)
        res_company = request.cr.dictfetchone()

        if('parent_id' not in res_company):
            self.company_has_parent = int(0)
            return int(0)
        else:
            if(res_company['parent_id'] != None):
                self.company_has_parent = int(str(res_company['parent_id']))
                return int(str(res_company['parent_id']))
            else:
                self.company_has_parent = int(0)
                return int(0)