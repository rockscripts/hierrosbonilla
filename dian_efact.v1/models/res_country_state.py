# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo import http
from pprint import pprint
import importlib
import os, json
from odoo.http import request
from lxml import etree
from dianservice.dianservice import Service
import logging

_logger = logging.getLogger(__name__)

class res_country_state(models.Model):
    _inherit = 'res.country.state'    
    
    sector_type = fields.Selection([("state","Estado"),("district","Districto")], default="state")
