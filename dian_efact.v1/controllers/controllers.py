# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import Warning
import os
import base64
import random
import json
import sys
import xlrd
import os.path, sys, shutil
import base64, json
from lxml import etree
from datetime import datetime
from odoo.http import request
from dianservice.dianservice import Service

class dianefact(http.Controller):


    @http.route('/dianefact/update_context/', methods=['POST'], type='json')
    def update_context(self, **kw):
        uid = http.request.env.context.get('uid')
        query = "select company_id from res_users where id = '" + str(uid) + "'"
        request.cr.execute(query)
        res_users = request.cr.dictfetchone()
        context = request.env.context.copy()
        context.update({'c_c_id': res_users['company_id']})
        request.env.context = context
        return request.env.context
    
    @http.route('/dianefact/update_vat_dv/', methods=['POST'], type='json', auth="public")
    def update_vat_dv(self, **kw):
        dv_ = kw.get('vat_dv')
        id_ = kw.get('id')
        model_ = kw.get('model')
        if(model_ =='account_invoice'):
            model_ = 'res_partner'  
        if(dv_==0):
            dv_ = 1 
        query = "update "+str(model_)+" set vat_dv = '"+str(dv_)+"' where id = '"+str(id_).replace(".","")+"'"
        request.cr.execute(query)
        return query

    # don't let create notes over an invoice if a credit note exists with discrepance code equals 2 = Anulacion de la factura
    @http.route('/dianefact/can_create_notes/', methods=['POST'], type='json', auth="public", website=True)
    def can_create_notes(self, **kw):
        invoice_number = kw.get('invoice_number')
        query = "select id, number from account_invoice where type = 'out_refund' and origin = '"+str(invoice_number)+"' and discrepance_code='2'"
        request.cr.execute(query)
        refund_invoice = request.cr.dictfetchone()
        if(refund_invoice):
            refund_invoice["found"] = True
        else:
            refund_invoice = {}
            refund_invoice["found"] = False
        return refund_invoice

    @http.route('/dianefact/get_nit/', methods=['POST'], type='json', auth="public", website=True)
    def get_nit(self, **kw):
        nit = kw.get('nit')
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'
        xmlPath = xmlPath.replace("controllers", "models")
        response = {}
        if(nit!=""):
            DianService = Service()
            DianService.setXMLPath(xmlPath)
        try:
            response = DianService.consultNIT(nit)
            if not response:
                return { 
                            'nit':nit,
                            'status' :  "El NIT no fue encontrado en registros de la DIAN"
                       }
            else:
                if('error' not in response):
                    return {
                                'status' :  "OK",
                                'nit':nit,
                                'denominacion' : response['denominacion'],
                                'dian_matricula' : response["matricula"]
                            }
                else:
                    return  {
                                'nit':  nit,
                                'status' :  "El NIT no fue encontrado en registros de la DIAN"
                            }
        except Exception as e:
            exc_traceback = sys.exc_info()
            # with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            return {'status' :  "FAIL"}

    @http.route('/dianefact/get_invoice_qr/', methods=['POST'], type='json', auth="public", website=True)
    def get_invoice_qr(self, **kw):
        orderReference = kw.get('orderReference')

        query = "select invoice_id from pos_order where pos_reference = '"+str(orderReference)+"'"
        request.cr.execute(query)    
        pos_sale = request.cr.fetchone()
        invoice_id = pos_sale[0]

        query = "select qr_image from account_invoice where id = "+str(invoice_id)
        request.cr.execute(query)    
        account_invoice = request.cr.fetchone()
        qr_image = account_invoice[0]
        return qr_image
    
    @http.route('/dianefact/get_pos_reference/', methods=['POST'], type='json', auth="public", website=True)
    def get_pos_reference(self, **kw):
        pos_session_id = kw.get('pos_session_id')
        query = "select pos_reference from pos_order where session_id = '"+str(pos_session_id)+"' order by id desc"
        
        request.cr.execute(query)    
        pos_sale = request.cr.dictfetchone()
        return pos_sale['pos_reference']

    @http.route('/dianefact/get_invoice_ordered/', methods=['POST'], type='json', auth="public", website=True)
    def get_invoice_ordered(self, **kw):
        orderReference = kw.get('orderReference')

        query = "select invoice_id from pos_order where pos_reference = '"+str(orderReference)+"'"
        request.cr.execute(query)    
        pos_sale = request.cr.dictfetchone()
        response = False
        if(pos_sale):
            invoice_id = pos_sale['invoice_id']

            query = "select qr_image, number, journal_id, qr_url from account_invoice where id = "+str(invoice_id)
            request.cr.execute(query)    
            account_invoice = request.cr.dictfetchone()

            query = "select name, code from account_journal where id = "+str(account_invoice['journal_id'])
            request.cr.execute(query)    
            account_journal = request.cr.dictfetchone()

            response = {"inv_id":invoice_id, "number":account_invoice['number'],"qr_image":account_invoice['qr_image'],"journal_name":account_journal['name'],"journal_code":account_journal['code'],"cufe":account_invoice['qr_url']}
        
        return response

    @http.route('/dianefact/get_invoice_ticket_journal/', methods=['POST'], type='json', auth="public", website=True)
    def get_invoice_ticket_journal(self, **kw):
        response = {}
        uid = http.request.env.context.get('uid')

        query = "select id, name, code from account_journal where code in ('INV','FAC','BOL','BOLV','POSV')"
        request.cr.execute(query)    
        journals = request.cr.dictfetchall()
        response["journals"] = journals
        query = "select pos_config.id, pos_config.invoice_journal_id from pos_config inner join pos_session on pos_config.id = pos_session.config_id and  pos_session.user_id = "+str(uid)+" and state = 'opened'"
        #query = "select pos_config.id, pos_config.invoice_journal_id from pos_config inner pos_config.id = pos_session.config_id and join pos_session on pos_session.user_id = "+str(uid)+" and state = 'opened'"
        request.cr.execute(query)    
        pos_config = request.cr.dictfetchone()
        response["pos_config"] = pos_config
        response["query"] = query
                
        return response

    @http.route('/dianefact/update_current_pos_conf/', methods=['POST'], type='json', auth="public", website=True)
    def update_current_pos_conf(self, **kw):

        posID = kw.get('posID')
        journalID = kw.get('journalID')
        response = {}

        query = "update pos_config set invoice_journal_id = " + str(journalID) + " where id = " + str(posID)
        request.cr.execute(query) 
                
        return True

    @http.route('/dianefact/populate_representants_list/', methods=['POST'], type='json', auth="public", website=True)
    def populate_representants_list(self, **kw):        
        query = "select * from res_representants"
        request.cr.execute(query) 
        representants = request.cr.dictfetchall() 
        return representants

    @http.route('/dianefact/save_representants/', methods=['POST'], type='json', auth="public", website=True)
    def save_representants(self, **kw):
        
        id_representant = kw.get('id_representant')
        id_company = kw.get('id_company')
        doc_type = kw.get('doc_type')
        doc_number = kw.get('doc_number')
        name = kw.get('name')
        position = kw.get('position')
        address = kw.get('address')

        currentDateTime = datetime.now()
        date_added = currentDateTime#currentDateTime.strftime("%H:%M:%S")

        if(int(id_representant)==0):
            params = {}
            params ["search_type"] = "check_exist"
            params ["id_company"] = id_company
            params ["doc_number"] = doc_number
            params ["doc_type"] = doc_type
            representant = self.get_representant(params)
            if(representant):
                return False
            else:
                query = "insert into res_representants (id_company, doc_type, doc_number, name, position, address, date_added) values ('"+str(doc_type)+"', '"+str(doc_type)+"', '"+str(doc_number)+"', '"+str(name)+"', '"+str(position)+"', '"+str(address)+"', '"+str(date_added)+"')"
        else:
            query = "update res_representants set doc_type='"+str(doc_type)+"', doc_number='"+str(doc_number)+"', name='"+str(name)+"', position='"+str(position)+"', address='"+str(address)+"' where id='"+str(id_representant)+"'"

        request.cr.execute(query)
        return True

    @http.route('/dianefact/get_representant/', methods=['POST'], type='json', auth="public", website=True)
    def get_representant(self,data):
        if (data["search_type"]=="check_exist"):
            query = "select * from res_representants where id_company='"+str(data["id_company"])+"' and doc_number = '"+str(data["doc_number"])+"' and doc_type = '"+str(data["doc_type"])+"'"
        else:
            query = "select * from res_representants where id = "+int(data["id_representant"])
        request.cr.execute(query)
        representant = request.cr.dictfetchone()
        return representant

    @http.route('/dianefact/remove_representant/', methods=['POST'], type='json', auth="public", website=True)
    def remove_representant(self, **kw):  
        id_representant = kw.get('id_representant')    
        query = "delete from res_representants where id="+str(id_representant)
        request.cr.execute(query)
        return True

    @http.route('/dianefact/edocs_submit_invoice/', methods=['POST'], type='json', auth="public", website=True)
    def edocs_submit_invoice(self, **kw):
        invoice_id = kw.get('invoice_id') 
        
        query = "select number, company_id, unsigned_document, signed_document, response_document from account_invoice where id = "+str(invoice_id)
        request.cr.execute(query)
        invoice_fields = request.cr.dictfetchone()
        query = "select res_partner.vat, res_company.dian_emisor_nit, res_company.dian_test_set_id, res_company.dian_emisor_username, res_company.dian_emisor_password, res_company.dian_emisor_clave_tecnica, res_company.dian_certificate_filename, res_company.dian_certificado_contrasena, res_company.dian_numero_resolucion, res_company.dian_fecha_inicio_resolucion, res_company.dian_fecha_fin_resolucion,  res_company.dian_prefijo_resolucion_periodo,  res_company.dian_desde_resolucion_periodo,  res_company.dian_hasta_resolucion_periodo, res_company.dian_api_mode, res_company.dian_xml_client_path from res_company left join res_partner on res_partner.company_id = res_company.id where res_company.id = "+str(invoice_fields['company_id'])+" and res_partner.is_company = TRUE"
        request.cr.execute(query)
        company_fields = request.cr.dictfetchone()
        
        secuencia = str(invoice_fields["number"]).split("-")
        secuencia_serie = secuencia[0]
        secuencia_consecutivo = secuencia[1]
        
        if(secuencia_serie=="fd0"):
            document_type = str("debitNote")
        if(secuencia_serie=="fc0"):
            document_type = str("creditNote")
        if(secuencia_serie=="fv0"):
            document_type = str("invoice")
        nombre_archivo_xml = str(secuencia_serie)+str(company_fields["dian_emisor_nit"])+str(secuencia_consecutivo)
        nombre_archivo_zip = str("z0")+str(company_fields["dian_emisor_nit"])+str(secuencia_consecutivo)
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
            
            
            if(DianResponse["status"] == "OK"):
                # save xml documents steps for reference in edocs
                response_document_filename = nombre_archivo_xml+str(".xml")
                api_message = "ESTADO: "+str(DianResponse["status"])+"\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])
                query = "update account_invoice set dian_request_status = 'OK', api_message = '"+str(api_message)+"', dian_request_type = 'Manual e-Docs' where id = "+str(invoice_id)
                request.cr.execute(query)
                response = {
                            "dian_request_status":str("OK"),
                            "api_message":str(DianResponse["body"])
                       }
                return response
            else:
                if("Documento enviado previamente" in str(DianResponse["body"])):
                    DianResponse["status"] = "OK"
                    api_message = "ESTADO: OK\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])
                else:
                    DianResponse["status"] = "FAIL"
                    api_message = "ESTADO: "+str(DianResponse["status"])+"\n"+"DESCRIPCIÓN: "+str(DianResponse["body"])

                query = "update account_invoice set dian_request_status = '"+str(DianResponse["status"])+"', api_message = '"+str(api_message)+"', dian_request_type = 'Manual e-Docs' where id = "+str(invoice_id)
                request.cr.execute(query)
                response = {
                                "dian_request_status":DianResponse["status"],
                                "api_message":api_message
                        }
                return response
        except Exception as e:
            exc_traceback = sys.exc_info() 
            # with open('/home/rockscripts/Documents/data1.json', 'w') as outfile:
            #     json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            query = "update account_invoice set dian_request_status = 'FAIL', api_message = '"+str("Verificar datos del facturador en mi compañia emisora.")+"', dian_request_type = 'Manual e-Docs' where id = "+str(invoice_id)
            request.cr.execute(query)
            response = {
                            "dian_request_status":str("FAIL"),
                            "api_message":str("ESTADO: Verificar datos del facturador en mi compañia emisora.")
                       }
            return response

        


    @http.route('/dianefact/get_partner/', methods=['POST'], type='json', auth="public", website=True)
    def get_partner(self, **kw):
        partner_id = kw.get('partner_id') 
        partner = None
        if(int(partner_id)>0):
            query = "select * from res_partner where id = "+str(partner_id)
            request.cr.execute(query)
            partner = request.cr.dictfetchone()
            return partner

    @http.route('/dianefact/get_segments/', methods=['POST'], type='json', auth="public", website=True)
    def get_segments(self, **kw):
        segments_selection = [] 
        if(self.check_model_table('dian_productcodes')):
            if(self.check_data_table('dian_productcodes')):       
                query = "select segment_code, segment_name from dian_productcodes group by segment_code, segment_name order by segment_code asc"                
                request.cr.execute(query)
                segments = request.cr.dictfetchall()
                for segment in segments: 
                    segments_selection.append((segment['segment_code'], segment['segment_name']))
            else:
                self.install_product_codes_data()
        else:
            self.install_product_codes_data()
        return segments_selection

    @http.route('/dianefact/get_families/', methods=['POST'], type='json', auth="public", website=True)
    def get_families(self, **kw):
        families_selection = []
        segment_code = kw.get('segment_code')         
        query = "select family_code, family_name from dian_productcodes where segment_code = '"+str(segment_code)+"' group by family_code, family_name order by family_code asc"                
        request.cr.execute(query)
        families = request.cr.dictfetchall()
        for family in families: 
            families_selection.append((family['family_code'], family['family_name']))
        return families_selection
    
    @http.route('/dianefact/get_clases/', methods=['POST'], type='json', auth="public", website=True)
    def get_clases(self, **kw):
        classes_selection = []
        family_code = kw.get('family_code')         
        query = "select clase_code, clase_name from dian_productcodes where family_code = '"+str(family_code)+"' group by clase_code, clase_name order by clase_code asc"                
        request.cr.execute(query)
        classes = request.cr.dictfetchall()
        for family in classes: 
            classes_selection.append((family['clase_code'], family['clase_name']))
        return classes_selection
    
    @http.route('/dianefact/get_products/', methods=['POST'], type='json', auth="public", website=True)
    def get_products(self, **kw):
        products_selection = []
        class_code = kw.get('class_code')         
        query = "select product_code, product_name from dian_productcodes where clase_code = '"+str(class_code)+"' group by product_code, product_name order by product_code asc"                
        request.cr.execute(query)
        products = request.cr.dictfetchall()
        for product in products: 
            products_selection.append((product['product_code'], product['product_name']))
        return products_selection

    def install_product_codes_data(self):
        product_codes = self.get_tribute_entity_product_code()
        for product_code in product_codes:            
            query = "insert into dian_productcodes (segment_code, segment_name, family_code, family_name, clase_code, clase_name, product_code, product_name) values ('"+str(product_code[0])+"','"+str(product_code[1]).replace("'","`")+"','"+str(product_code[2])+"','"+str(product_code[3]).replace("'","\'")+"','"+str(product_code[4])+"','"+str(product_code[5]).replace("'","`")+"','"+str(product_code[6])+"','"+str(product_code[7]).replace("'","`")+"')"                        
            request.cr.execute(query)

    def get_tribute_entity_product_code(self):
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/data/product_codes.xls'
        loc = (xmlPath) 
        
        wb = xlrd.open_workbook(loc) 
        sheet = wb.sheet_by_index(0) 
        
        # For row 0 and column 0 
        sheet.cell_value(5, 0)
        row_cells = [] 
        for j in range(sheet.nrows):
            if(j>3):
                row_cell = [] 
                for i in range(sheet.ncols): 
                    # 0 - segment cod
                    # 1 - segment name
                    # 2 - family cod
                    # 3 - family name
                    # 4 - clase cod
                    # 5 - clase name
                    # 6 - product cod
                    # 7 - product name
                    if(i==0 or i == 2 or i == 4 or i == 6):
                        row_cell.append(int(sheet.cell_value(j, i)))
                    else:
                        row_cell.append(str(sheet.cell_value(j, i)))
                row_cells.append(row_cell)

        return (row_cells)

    def check_model_table(self, tablename):
        request.cr.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(tablename.replace('\'', '\'\'')))
        if request.cr.fetchone()[0] == 1:
            return True
        return False
    
    def check_data_table(self, tablename):
        request.cr.execute("""
            SELECT COUNT(*)
            FROM {0}
            """.format(tablename.replace('\'', '\'\'')))
        if request.cr.fetchone()[0] > 0:
            return True
        return False

    
    @http.route('/dianefact/populate_location/', methods=['POST'], type='json', auth="public", website=True)
    def populate_location(self, **kw):
        country_id = kw.get('country_id') 
        state_id = kw.get('state_id') 
        district_id = kw.get('district_id') 
        country_code = "CO"
        response = {"country_id":country_id,"countries":None,"states":None, "districts":None}

        if(int(country_id)==0):
            query = "select id, name, code from res_country order by name DESC"
            #return query
            request.cr.execute(query)
            countries = request.cr.dictfetchall()
            response["countries"] = countries
            
            # default: Colombia
            query = "select id from res_country where code='CO'" 
            #return query
            request.cr.execute(query)
            country = request.cr.dictfetchone()
            country_id = country['id']
            response["country_id"] = country_id
        else:
            query = "select id, name, code from res_country order by name DESC"
            #return query
            request.cr.execute(query)
            countries = request.cr.dictfetchall()
            response["countries"] = countries

        if(int(country_id)>0):
            query = "select id, name, code from res_country where id = " + str(country_id)
            request.cr.execute(query)
            country = request.cr.dictfetchone()
            if(country['code']=="CO"):
                query = "select id, name, code from res_country_state where length(code) = 3 and country_id = "+str(country_id) + " order by name desc"
            else:
                query = "select id, name, code from res_country_state where country_id = "+str(country_id) + " order by name desc"
            #return query
            request.cr.execute(query)
            country_states = request.cr.dictfetchall()
            response["states"] = country_states
        
        if(int(state_id)>0):
            query = "select id, name, code from res_country where id = " + str(country_id)
            request.cr.execute(query)
            country = request.cr.dictfetchone()

            query = "select id, name, code from res_country_state where id = " + str(state_id)
            request.cr.execute(query)
            state = request.cr.dictfetchone()
            if(country['code']=="CO"):
                query = "select id, name, code from res_country_state where length(code) = 5 and country_id = " + str(country_id) + " order by name desc"
            elif(country['code']=="PE"):
                query = "select id, name, code from res_country_state where length(code) = 6 and country_id = " + str(country_id) + " and code like '" + str(state['code'])+ "%'"
            else:
                query = "select id, name, code from res_country_state where country_id = " + str(country_id) + " and code like '" + str(state['code'])+ "%'"
            

            request.cr.execute(query)
            province_districts = request.cr.dictfetchall()
            response["districts"] = province_districts

        #with open('/odoo_rockscripts/custom/addons/edocs_print_format/data.json', 'w') as outfile:
        #    json.dump(response, outfile)
        return response