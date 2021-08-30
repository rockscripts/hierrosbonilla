# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from pprint import pprint
import importlib
import os.path, sys, shutil
import base64, json
from lxml import etree
from dianservice.dianservice import Service

class res_company(models.Model):  
        
    _inherit = 'res.company'

    dian_certificate = fields.Binary(string="Certificado",filename="dian_certificate_filename" ,filters='*.p12', type="p12")
    dian_certificate_filename = fields.Char(string="Certificado", invisible="1", default="Certicamara")
    dian_certificado_contrasena = fields.Char(string="Crt. Contraseña", default="")
    dian_tipo_persona = fields.Selection([('1','Jurídica'),('2','Natural')], string='Tipo Persona', default='2')
    dian_regimen = fields.Selection([('48','Impuesto sobre las ventas – IVA'),('49','No responsable de IVA')], string='Régimen', default='48')
    dian_tipo_documento = fields.Selection([('13','Cédula de ciudadanía'),('31','NIT'),('11','Registro civil'),('41','Pasaporte'),('12','Tarjeta de identidad'),('21','Tarjeta de extranjería'),('22','Cédula de extranjería'),('42','Documento de identificación extranjero'),('91','NUIP *'),('50','NIT otro país')], string='Tipo Documento', default='31')
    vat_dv = fields.Char(string="DV", default="")
    dian_matricula = fields.Char(name="dian_matricula", string="Matricula Mercantil", default='')
    dian_ciiu = fields.Char(name="dian_ciiu", string="CIIU(s)", default='', placeholder="6201")
    dian_municipio = fields.Selection(
        selection='_get_municipios', string="Municipio")    
    district_id = fields.Many2one('res.country.state', 'Distrito')
    dian_responsabilidades = fields.Selection(selection="_get_responsabilidades", string='Responsabilidad Físcal', default='R-99-PN')
    dian_es_autoretenedor = fields.Boolean(string='¿Es Autorretenedor?')
    
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
                                                  
    dian_emisor_nit = fields.Char(name="dian_emisor_nit", string="NIT Software", default='20603408111')
    dian_emisor_username = fields.Char(name="dian_emisor_username", string="Identificador Software", default='20603408111MODDATOS')
    dian_emisor_password = fields.Char(name="dian_emisor_password", string="PIN Software", default='moddatos')
    dian_api_mode = fields.Selection([('SANDBOX','SANDBOX'),('PRODUCTION','PRODUCTION')], string='Modo Servicio', default='SANDBOX')
    dian_request_type = fields.Selection([('automatic','Automatizada'),('validated','Documento Validado')], string='Tipo de Emisión', default='automatic')
    dian_certs = fields.Selection([('cert_1','Cert 1'),('cert_2','Cert 2')], string='Certificado', default='cert_1')
    dian_test_set_id = fields.Char(name="dian_test_set_id", string="Test Set ID", default='')

    # software
    dian_numero_resolucion = fields.Char(name="dian_numero_resolucion", string="Número Resolución")
    dian_fecha_inicio_resolucion = fields.Char(name="dian_fecha_inicio_resolucion", string="Fecha Inicio Resolución")
    dian_fecha_fin_resolucion = fields.Char(name="dian_fecha_fin_resolucion", string="Fecha Fin Resolución")
    dian_prefijo_resolucion_periodo = fields.Char(name="dian_prefijo_resolucion_periodo", string="Prefijo")
    dian_desde_resolucion_periodo = fields.Char(name="dian_desde_resolucion_periodo", string="Desde")
    dian_hasta_resolucion_periodo = fields.Char(name="dian_hasta_resolucion_periodo", string="Hasta")
    dian_emisor_clave_tecnica = fields.Char(name="dian_emisor_clave_tecnica", string="Clave Técnica")    
    dian_xml_client_path = fields.Char(string="NIT / Nombre usuario")

    _columns = {
                    "dian_regimen":fields.Selection([('48','Impuesto sobre las ventas – IVA'),('49','No responsable de IVA')], string='Régimen', default='48'),
                    "dian_tipo_documento":fields.Selection([('13','Cédula de ciudadanía'),('31','NIT'),('11','Registro civil'),('41','Pasaporte'),('12','Tarjeta de identidad'),('21','Tarjeta de extranjería'),('22','Cédula de extranjería'),('42','Documento de identificación extranjero'),('91','NUIP *'),('50','NIT otro país')], string='Tipo Documento', default='31')
               } 

    @api.model
    def get_current_id(self):
        return self.env.context.get('active_ids', [])

    @api.onchange('dian_certificate')
    def _upload_certificate_to_server(self):
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'
        if(self.dian_certificate_filename=="Certicamara"): # default; do nothing
            return str("")

        crtTarget = str(xmlPath+'/XMLcertificates/')+self.dian_xml_client_path+"/"+str(self.dian_certificate_filename)
        crtTargetDir = str(xmlPath+'/XMLcertificates/')+self.dian_xml_client_path
        try:
            
            if os.path.exists(crtTargetDir):
                path, dirs, files = next(os.walk(crtTargetDir))
                file_count = len(files)
                if(file_count>0):
                    shutil.rmtree(crtTargetDir)

            if not os.path.exists(crtTargetDir):
                os.system("sudo mkdir "+str(crtTargetDir))
                os.system("sudo chmod -R 0777 "+str(crtTargetDir))
                try:
                    original_umask = os.umask(0)
                    os.makedirs(str(crtTargetDir), 0o777)
                finally:
                    os.umask(original_umask)

            #with web api
            with open(crtTarget, "wb") as f:
                f.write(base64.b64decode(self.dian_certificate))
            #    DianService = Service()
            #    DianService.initDianAPI_certificado()
            #    DianService.setClientXMLPath(self.dian_xml_client_path)
            #    DianResponse = DianService.processCertification(crtTarget) 

        except Exception as e:
            # exc_traceback = sys.exc_info()
            raise Warning(str("ERROR | "+getattr(e, 'message', repr(e)))+" ON LINE "+str(format(sys.exc_info()[-1].tb_lineno)))
