# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import Warning
from odoo.http import request
from odoo import http
import os
import base64
import random
import json
import sys
from datetime import datetime
from dianservice.dianservice import Service

class DianEdocs(models.Model):
    _name = 'dian.edocs'
    _description = "Comprobantes eléctronicos"
    _table = 'account_invoice'
    _sql = "select * from account_invoice"
    _auto = False

    number = fields.Char(string='Documento', readonly=True)
    date_invoice = fields.Date(string='Creado en', readonly=True)
    create_date = fields.Char(string='Creado en', readonly=True)
    qr_image = fields.Text(name="qr_image", default='')

    unsigned_document = fields.Binary(string="XML - No firmado", default=None, readonly=True, filename="unsigned_document_filename" ,filters='*.xml', type="xml")
    unsigned_document_filename = fields.Char(string="Unsigned Filename", invisible="1", default="unsigned.xml")

    signed_document = fields.Binary(string="XML - Firmado", default=None, readonly=True, filename="signed_document_filename" ,filters='*.xml', type="xml")
    signed_document_filename = fields.Char(string="Signed Filename", invisible="1", default="signed.xml")

    response_document = fields.Binary(string="XML - Respuesta", default=None, readonly=True, filename="response_document_filename",filters='*.xml', type="xml")
    response_document_filename = fields.Char(string="Response Filename", invisible="1", default="response.xml")

    api_message = fields.Text(name="api_message", string="Estado", default='Documento contable sin emitir.', readonly=True)

    dian_request_status = fields.Text(string="Estado Emisión", name="dian_request_status", default='No Emitido')
    dian_request_type = fields.Text(string="Método", name="dian_request_type", default='Automatizada')

    company_id = fields.Integer(name="company_id")
    partner_id = fields.Integer(name="partner_id")
    current_company_id = fields.Integer(compute='_current_company_id', store=False)

    qr_url = fields.Char(string="QR URL")

    _columns =  {
                    'current_company_id': fields.Integer( compute='_current_company_id', store=False),
                }

    @api.multi
    def load_action_window(self):
        uid = http.request.env.context.get('uid')
        query = "select company_id from res_users where id = '" + str(uid) + "'"
        request.cr.execute(query)
        res_users = request.cr.dictfetchone()
        action_id = self.env.ref('dian_efact.action_dian_edocs_book')
        views = [
                    (self.env.ref('dian_efact.sunat_edocs_tree_view').id, 'tree'),
                    (self.env.ref('dian_efact.form_dian_edocs').id, 'form')
                ]
        action_open =  {
                            'name': action_id.name,
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.invoice',
                            'view_mode': 'kanban,tree,form',
                            'view_type': 'form',
                            'views':views,
                            'search_view_id':self.env.ref('dian_efact.view_edocs_filter').id,
                            'domain': [['company_id','=',res_users['company_id']]],
                            'target': 'inline'
                        }
        return action_open
  
    #Automated task for submit failed or unsubmited invoices 
    def edocs_submit_invoices(self, **kw):
        query = "select nextcall, dian_start_date from ir_cron where cron_name = '"+str("dian_edocs")+"'"
        request.cr.execute(query)
        cron_job_edocs = request.cr.dictfetchone()
        nextcall_datetime = str(cron_job_edocs["nextcall"]).split(" ")
        invoice_date_limit = nextcall_datetime[0]

        query = "select id, number, company_id, unsigned_document, signed_document, response_document from account_invoice where date_invoice <= '"+str(invoice_date_limit)+"' and date_invoice >= '"+str(cron_job_edocs["dian_start_date"])+"' and (dian_request_status = '"+str("FAIL")+"' or dian_request_status = '"+str("No Emitido")+"' or dian_request_status = '"+str("not_requested")+"')"
        
        request.cr.execute(query)
        invoices_unsubmited = request.cr.dictfetchall()
        for invoice_unsubmited in invoices_unsubmited:                   
            query = "select res_partner.vat, res_company.dian_emisor_nit, res_company.dian_test_set_id, res_company.dian_emisor_username, res_company.dian_emisor_password, res_company.dian_emisor_clave_tecnica, res_company.dian_certificate_filename, res_company.dian_certificado_contrasena, res_company.dian_numero_resolucion, res_company.dian_fecha_inicio_resolucion, res_company.dian_fecha_fin_resolucion,  res_company.dian_prefijo_resolucion_periodo,  res_company.dian_desde_resolucion_periodo,  res_company.dian_hasta_resolucion_periodo, res_company.dian_api_mode, res_company.dian_xml_client_path from res_company left join res_partner on res_partner.company_id = res_company.id where res_company.id = "+str(invoice_unsubmited['company_id'])+" and res_partner.is_company = TRUE"
            request.cr.execute(query)
            company_fields = request.cr.dictfetchone()        

            secuencia = str(invoice_unsubmited["number"]).split("-")
            secuencia_serie = secuencia[0]
            secuencia_consecutivo = secuencia[1]

            document_type = str("invoice")
            if(secuencia_serie=="fd0"):
                document_type = str("debitNote")
            else:
                document_type = str("creditNote")

            nombre_archivo_xml = str(secuencia_serie)+str(company_fields["vat"])+str(secuencia_consecutivo)
            nombre_archivo_zip = str("z0")+str(company_fields["vat"])+str(secuencia_consecutivo)

            dian_ambiente = str("2")
            if (str(company_fields["dian_api_mode"])=="SANDBOX"):
                dian_ambiente = str("2")
            else:
                dian_ambiente = str("1")

            currentDateTime = datetime.now()
            currentTime = currentDateTime.strftime("%H:%M:%S")

            dian_data = {
                        "secuencia_consecutivo":secuencia_consecutivo,
                        "tipo_documento":document_type,
                        "ambiente_ejecucion":dian_ambiente,
                        "dian": {
                                    "nit":str(company_fields["dian_emisor_nit"]),
                                    "identificador_software":str(company_fields["dian_emisor_username"]),
                                    "dian_test_set_id":str(company_fields["dian_test_set_id"]),
                                    "pin_software":str(company_fields["dian_emisor_password"]),
                                    "clave_tecnica":str(company_fields["dian_emisor_clave_tecnica"]),
                                    "nonce":base64.b64encode(str(random.random()).encode()).decode(),
                                    "created":str(currentDateTime.year)+"-"+str(currentDateTime.month)+"-"+str(currentDateTime.day)+"T"+str(currentTime),
                                    "certificado":company_fields["dian_certificate_filename"],
                                    "certificado_contrasena":str(company_fields["dian_certificado_contrasena"]),
                                    "autorizacion":{
                                                        "codigo":str(company_fields["dian_numero_resolucion"]),
                                                        "codigo_pais":"CO",
                                                        "fecha_inicio":str(company_fields["dian_fecha_inicio_resolucion"]),
                                                        "fecha_fin":str(company_fields["dian_fecha_fin_resolucion"]),
                                                        "prefijo":str(company_fields["dian_prefijo_resolucion_periodo"]),
                                                        "desde":str(company_fields["dian_desde_resolucion_periodo"]),
                                                        "hasta":str(company_fields["dian_hasta_resolucion_periodo"]),
                                                    }
                                },
                        "xml":  {
                                    #"signed":base64.b64decode((invoice_fields["signed_document"]))
                                },
                        "licencia": "081OHTGAVHJZ4GOZJGJV",
                        "accion":str("fill_submit")
                    }
            try: 
                xmlPath = str(os.path.dirname(os.path.abspath(__file__))).replace("controllers","models")+'/xml'
                DianService = Service()
                DianService.setXMLPath(xmlPath)
                DianService.fileXmlName = nombre_archivo_xml
                DianService.fileZipName = nombre_archivo_zip
                DianService.xmlClientPath = company_fields["dian_xml_client_path"]
                DianService.initDianAPI(company_fields["dian_api_mode"], "sendBill")
                DianService.sunatAPI.processInvoiceAction = str("fill_submit")
                DianService.sunatAPI.dian_data = dian_data["dian"]

                
                DianResponse = DianService.processInvoiceFromSignedXML(dian_data)
                
                
                #with open('/odoo_dian_v12/custom/addons/dian_efact/log.json', 'w') as outfile:
                #    json.dump(str(DianResponse["status"])+str(DianResponse["body"]), outfile)
                if(DianResponse["status"] == "OK"):
                    # save xml documents steps for reference in edocs
                    response_document_filename = nombre_archivo_xml+str(".xml")
                    api_message = "ESTADO: "+str(DianResponse["status"])+"\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])
                    query = "update account_invoice set dian_request_status = 'OK', api_message = '"+str(api_message)+"', dian_request_type = 'Automatizada' where id = "+str(invoice_unsubmited["id"])
                    request.cr.execute(query)
                    response = {
                                "dian_request_status":str("OK"),
                                "api_message":str(DianResponse["body"])
                        }
                    #return response
                else:
                    if("Documento enviado previamente" in str(DianResponse["body"])):
                        DianResponse["status"] = "OK"
                        api_message = "ESTADO: OK\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])
                    else:
                        DianResponse["status"] = "FAIL"
                        api_message = "ESTADO: "+str(DianResponse["status"])+"\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])

                    query = "update account_invoice set dian_request_status = '"+str(DianResponse["status"])+"', api_message = '"+str(api_message)+"', dian_request_type = 'Automatizada' where id = "+str(invoice_unsubmited["id"])
                    request.cr.execute(query)
                    response = {
                                    "dian_request_status":DianResponse["status"],
                                    "api_message":api_message
                            }
                    #return response
                #with open('/odoo_dian_v12/custom/addons/dian_efact/log.json', 'w') as outfile:
                #    json.dump(query, outfile)
            except Exception as e:
                exc_traceback = sys.exc_info() 
                #with open('/odoo_dian_v12/custom/addons/dian_efact/log.json', 'w') as outfile:
                #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
                query = "update account_invoice set dian_request_status = 'FAIL', api_message = '"+str("Verificar datos del facturador en mi compañia emisora.")+"', dian_request_type = 'Automatizada' where id = "+str(invoice_unsubmited["id"])
                request.cr.execute(query)
                response = {
                                "dian_request_status":str("FAIL"),
                                "api_message":str("ESTADO: Verificar datos del facturador en mi compañia emisora.")
                        }
            #return response


    @api.depends('current_company_id')
    def _current_company_id(self):
        uid = http.request.env.context.get('uid')
        query = "select company_id from res_users where id = '" + str(uid) + "'"
        request.cr.execute(query)
        res_users = request.cr.dictfetchone()
        for record in self:
            if(int(record.company_id) != int(res_users['company_id'])):
                self.update({'current_company_id' : 0})
                record.current_company_id = int(0)
            else:
                self.update({'current_company_id' : res_users['company_id']})
                record.current_company_id = int(res_users['company_id'])

            self = self.env['dian.edocs'].search([('company_id', '=', res_users['company_id'])])



#@api.model
    #def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #    def get_view_id(xid, name):
    #        try:
    #            return self.env.ref('dian.' + xid)
    #        except ValueError:
    #            view = self.env['ir.ui.view'].search([('name', '=', name)], limit=1)
    #            if not view:
    #                return False
    #            return view.id
    #    
    #    context = self._context
    #    uid = http.request.env.context.get('uid')
    #    query = "select company_id from res_users where id = '" + str(uid) + "'"
    #    request.cr.execute(query)
    #    res_users = request.cr.dictfetchone()
    #    self = self.with_context(c_c_id=int(res_users['company_id']))
    #    context = request.env.context.copy()
    #    context.update({'c_c_id': res_users['company_id']})
    #    request.env.context = context
    #    with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
    #        json.dump(self._context, outfile)
#
    #    if context.get('active_model') == 'dian.edocs':
    #        if not view_type:
    #            view_id = get_view_id('edocs.tree.view', 'dian.edocs.tree.view')
    #            view_type = 'tree'
    #        elif view_type == 'form':
    #                view_id = get_view_id('form_dian_edocs', 'Comprobantes eléctronicos').id
    #    
    #    return super(DianEdocs, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        
    #def __str__(self, object_display):
    #    return  str(object_display.__class__) + '\n'+ '\n'.join(('{} = {}'.format(item, object_display.__dict__[item]) for item in object_display.__dict__))


    #@api.model_cr
    #def init(self):
    #    tools.drop_view_if_exists(self._cr, 'edocs')
    #    self._cr.execute(
    #                     """
    #                        CREATE OR REPLACE VIEW edocs AS 
    #                        ( 
    #                          SELECT number as number, 
    #                                 create_date as create_date,   
    #                                 unsigned_document as unsigned_document,
    #                                 signed_document as signed_document, 
    #                                 response_document as response_document,
    #                                 qr_image as qr_image,
    #                                 api_message as api_message,
    #                                 dian_request_type as dian_request_type,
    #                                 company_id as company_id,
    #                                 current_company_id as current_company_id,
    #                                 partner_id as partner_id
    #                          FROM account_invoice
    #                          ORDER BY number DESC
    #                        )
    #                     """
    #                    )