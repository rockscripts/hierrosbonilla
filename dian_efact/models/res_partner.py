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

class res_partner(models.Model):
    _inherit = 'res.partner'    
    
    dian_tipo_persona = fields.Selection([('1','Jurídica'),('2','Natural')], string='Tipo Persona', default='2')
    dian_regimen = fields.Selection([('48','Impuesto sobre las ventas – IVA'),('49','No responsable de IVA')], string='Régimen', default='49')
    dian_tipo_documento = fields.Selection([('13','Cédula de ciudadanía'),('31','NIT'),('11','Registro civil'),('41','Pasaporte'),('12','Tarjeta de identidad'),('21','Tarjeta de extranjería'),('22','Cédula de extranjería'),('42','Documento de identificación extranjero'),('91','NUIP *'),('50','NIT otro país')], string='Tipo Documento', default='31')
    dian_municipio = fields.Selection(
        selection='_get_municipios', string="Municipio")
    district_id = fields.Many2one('res.country.state', 'Distrito')
    dian_responsabilidades = fields.Selection(selection="_get_responsabilidades", string='Responsabilidad Físcal', default='O-49')
    
    dian_matricula = fields.Char(name="dian_matricula", string="Matricula Mercantil", default='')
    vat_dv = fields.Char(string="DV", default="")

    _columns = {
                    "dian_regimen":fields.Selection([('0','Ventas Régimen común'),('1','Persona Jurídica'),('2','Gran Contribuyente'),('3','Auto Retenedor')], string='Régimen', default='0'),
                    "dian_tipo_documento":fields.Selection([('13','Cédula de ciudadanía'),('31','NIT'),('11','Registro civil'),('41','Pasaporte'),('12','Tarjeta de identidad'),('21','Tarjeta de extranjería'),('22','Cédula de extranjería'),('42','Documento de identificación extranjero'),('91','NUIP *')], string='Tipo Documento', default='31')
               }
               
    @api.onchange("district_id")
    def district_id_changed(self):
        self.zip = self.district_id.code

    def _get_responsabilidades(self):
        XMLpath = os.path.dirname(os.path.abspath(__file__))+'/xml/XMLDian/'
        tree = etree.parse(XMLpath+"TipoResponsabilidad-2.1.xml")
        CodeList = tree.getroot()
        responsabilities_selection = []
        for SimpleCodeList in CodeList.iter("SimpleCodeList"):

            for Row in SimpleCodeList.iter("Row"):
                name = str("")
                code = str("")
                for Value in Row.iter("Value"):
                    if(Value.get("ColumnRef") == "code"):
                        for SimpleValue in Value.iter("SimpleValue"):
                            code = SimpleValue.text
                    if(Value.get("ColumnRef") == "name"):
                        for SimpleValue in Value.iter("SimpleValue"):
                            name = SimpleValue.text
                            
                responsabilities_selection.append((str(code), name))

        return sorted(responsabilities_selection) 

    def _get_municipios(self):
        XMLpath = os.path.dirname(os.path.abspath(__file__))+'/xml/XMLDian/'
        tree = etree.parse(XMLpath+"Municipio-2.1.xml")
        CodeList = tree.getroot()
        payment_districts_selection = []
        for SimpleCodeList in CodeList.iter("SimpleCodeList"):

            for Row in SimpleCodeList.iter("Row"):
                name = str("")
                code = str("")
                for Value in Row.iter("Value"):
                    if(Value.get("ColumnRef") == "code"):
                        for SimpleValue in Value.iter("SimpleValue"):
                            code = SimpleValue.text
                    if(Value.get("ColumnRef") == "name"):
                        for SimpleValue in Value.iter("SimpleValue"):
                            name = SimpleValue.text
                            
                payment_districts_selection.append((str(code)+str("|")+str(name), name))

        return sorted(payment_districts_selection)

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        if partner.get('image'):
            partner['image'] = partner['image'].split(',')[1]
        partner_id = partner.pop('id', False)
        if partner_id:  # Modifying existing partner
            self.browse(partner_id).write(partner)
        else:
            partner['lang'] = self.env.user.lang
            partner_id = self.create(partner).id

        if('dian_tipo_documento' in partner and int(partner['dian_tipo_documento'])>0):
            query = "update res_partner set  dian_tipo_documento= '"+str(partner['dian_tipo_documento'])+"' where id="+str(partner_id)
            request.cr.execute(query) 
            #self.browse(partner_id).write({"dian_tipo_documento":partner['dian_tipo_documento']})

        return partner_id

    def _populate_peruan_districts(self):
        XMLpath = os.path.dirname(os.path.abspath(__file__))+'/xml/XMLDian/peru/'
        tree = etree.parse(XMLpath+"Districtos-2016.xml")
        CodeList = tree.getroot()
        payment_districts_selection = []
        for database in CodeList.iter("database"):
            for table in database.iter("table"):
                _id = str("")
                _name = str("")
                for column in table.iter("column"):
                    if(column.get("name") == "id"):
                        _id = column.text
                    if(column.get("name") == "name"):
                        _name = column.text                       
                                                    
                payment_districts_selection.append((str(_id)+str("|")+str(_name), _name))

        return sorted(payment_districts_selection)
   
    @api.model
    def fix_eu_vat_number(self, country_id, vat):
        
        return vat