# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from odoo import http
from pprint import pprint
import time
from datetime import datetime
import hmac
import hashlib
import requests
import json
import os
import random
from odoo.http import request
from decimal import Decimal
import qrcode
import base64
import os.path
import pwd
import sys
from lxml import etree
from io import BytesIO
from dianservice.dianservice import Service


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    api_message = fields.Text(name="api_message", string="Estado",
                              default='Documento contable sin emitir.', readonly=True)
    discrepance_code = fields.Text(
        name="discrepance_code", default='', readonly=True)
    discrepance_text = fields.Text(
        name="discrepance_text", string="Discrepancia", default="", readonly=True)

    qr_in_report = fields.Boolean('Ver QR en reporte', default=True)
    unsigned_document = fields.Binary(
        string="XML - no firmado", default=None, readonly=True, filename="unsigned.xml", filters='*.xml')
    unsigned_document_filename = fields.Char("Unsigned Filename")

    signed_document = fields.Binary(
        string="XML - Firmado", default=None, readonly=True, filename="unsigned.xml", filters='*.xml')
    signed_document_filename = fields.Char("Signed Filename")

    response_document = fields.Binary(
        string="XML - respuesta", default=None, readonly=True, filename="unsigned.xml", filters='*.xml')
    response_document_filename = fields.Char("Response Filename")
    qr_image = fields.Text(name="qr_image", default='')

    dian_request_status = fields.Text(
        name="dian_request_status", default='No Emitido')
    dian_request_type = fields.Text(
        name="dian_request_type", default='Automatizada')

    is_exportation = fields.Boolean('¿Exportación?')
    calculation_rate = fields.Char("Tasa de cambio")
    exporting_currency = fields.Selection(
        selection='_get_active_currencies', string="Divisa Objetivo", default='COP')

    amount_untaxed_invoice_signed = fields.Monetary(
        string='Untaxed Amount in Invoice Currency', currency_field='currency_id', readonly=True, compute='_compute_sign_taxes')
    amount_tax_signed = fields.Monetary(
        string='Tax in Invoice Currency', currency_field='currency_id', readonly=True, compute='_compute_sign_taxes')
    current_company_id = fields.Integer(
        compute='_current_company_id', store=False)

    dian_payment_means_id = fields.Selection(
        [('1','Contado'),('2','Cŕedito')], string="Tipo de operación", default="1") 

    dian_payment_means_code = fields.Selection(
        selection='_get_payment_means_code', string="Método del pago", default="10")
    dian_payment_id = fields.Char(
        name='dian_payment_id', string="Código del pago", placeholder="MTCN-7798268920")
    reference = fields.Char(name='reference', string="Ref. Pago",
                            placeholder="Usar en circular al registrar pago")
    
    dian_operation_type = fields.Selection(
        selection='_get_operation_types', string="Tipo de operación", default="10")

    qr_url = fields.Char(name='qr_url', string="CUFE", placeholder="cufe - alghoritm")

    _columns = {'api_message': fields.Text(
        'Estado'), 'discrepance': fields.Text('Discrepancia')}
    _defaults = {'api_message': 'Documento contable sin emitir.',
                 'diario': 'factura', 'discrepance': ''}

    @api.onchange('reference')
    def on_change_reference(self):
        self.dian_payment_id = self.reference
 
    
    @api.onchange('dian_operation_type')
    def on_change_is_exportation(self):
        if(self.dian_operation_type=="04"):
            self.is_exportation = True
            self.calculation_rate = "3870"
            #self.currency_id.name = "USD"
            self.exporting_currency = "COP"
        else:
            self.is_exportation = False
            self.calculation_rate = ""
            self.calculation_rate = "0.00028"
            #self.currency_id.name = "COP"
            self.exporting_currency = "USD"

    @api.multi
    def invoice_validate(self):

        urlPath = http.request.httprequest.full_path
        if 'payment/process' in urlPath:
            return super(account_invoice, self).invoice_validate()

        invoice_items = []

        for invoice in self:
            self.check_client_dirs(invoice.company_id.dian_xml_client_path)
            if invoice.partner_id.vat == "" or invoice.partner_id.vat == False:
                raise Warning(
                    _("Por favor, establecer el documento del receptor"))

        eDocumentType = self.journal_id.code
        index = 0
        dian_items = []
        totalVentaPedido = 0
        subTotalPedido = 0
        # impuestos
        tributos_globales = {}
        tributos = {}
        dian_request_type = "Automatizada"
        processInvoiceAction = "fill_only"

        if(eDocumentType == "BOLV" or eDocumentType == "POSV"):
            for invoice in self:
                self.qr_image =  self.generate_QR(str(invoice.number))
            return super(account_invoice, self).invoice_validate()

        if(eDocumentType == "NCR"):
            for invoice in self:
                dian_request_type = invoice.company_id.dian_request_type
                if(dian_request_type == "automatic"):
                    dian_request_type = "Automatizada"
                    processInvoiceAction = "fill_only"
                else:
                    dian_request_type = "Documento Validado"
                    processInvoiceAction = "fill_submit"

                items = invoice.invoice_line_ids
                global_discounts = []
                for item in items:
                    item_tributos = []
                    item_global_discount = []
                    item_discount = []
                    subTotalVenta = float((item.price_unit * item.quantity))
                    if(float(item.discount/100) > 0.0):
                        subTotalVenta = float(
                            subTotalVenta) - float(float(subTotalVenta) * float(item.discount/100))
                    totalVenta = subTotalVenta

                    # global discount >> point of sale config
                    if(bool(item.product_id.dian_is_product_discount) == True):
                        dian_discount_type = str(
                            item.product_id.dian_discount_type).split("-")
                        dian_discount_type_code = str(
                            dian_discount_type[0]).strip()
                        dian_discount_type_text = str(
                            dian_discount_type[1]).strip()

                        item_global_discount = {
                            "codigo": dian_discount_type_code,
                            "razon": dian_discount_type_text,
                            "porcentaje": self.get_global_discount_percent(item.product_id.id),
                            "monto": abs(item.price_subtotal)
                        }
                        global_discounts.append(item_global_discount)
                        continue
                    else:
                        pass

                    # line discount
                    if(float(item.discount) > float(0.0)):
                        item_discount = {
                            "codigo": str("08"),
                            "razon": str("Descuento por actualización de productos / servicios"),
                            "porcentaje": item.discount,
                            "monto": str(float(float((item.price_unit * item.quantity)) * float(item.discount/100)))
                        }

                    for tax in item.invoice_line_tax_ids:
                        impuesto = tax.amount/100
                        monto_afectacion_tributo = float(
                            (subTotalVenta * impuesto))

                        totalVenta += monto_afectacion_tributo

                        if(not invoice.company_id.dian_es_autoretenedor and (tax.dian_tributo == "05"  or tax.dian_tributo == "06"  or tax.dian_tributo == "07"  or tax.dian_tributo == "08")):
                            if(float(tax.amount)<0):                                
                                totalVenta -= monto_afectacion_tributo

                        item_tributo = {
                            "codigo": tax.dian_tributo,
                            "porcentaje": abs(float(tax.amount)),
                            "montoAfectacionTributo": abs(float(monto_afectacion_tributo)),
                            "total_venta": subTotalVenta
                        }
                        if(float(monto_afectacion_tributo) > 0):
                            item_tributos.append(item_tributo)

                    tributos_globales = self.add_global_tributes(
                        item_tributos, tributos_globales)

                    dian_item = {
                        'id': str(item.id),
                        'cantidad': str(item.quantity),
                        'descripcion': item.name,
                        'brand_name': item.product_id.dian_brand_name,
                        'model': item.product_id.dian_item_model,
                        'precioUnidad': item.price_unit,
                        'clasificacionProductoServicioCodigo': self.get_sunat_product_code_classification(item.product_id.id),
                        "subTotalVenta": subTotalVenta,
                        'totalVenta': totalVenta,
                        "tributos": item_tributos,
                        "descuento": item_discount
                    }
                    dian_items.append(dian_item)
                    totalVentaPedido += float(totalVenta)
                    subTotalPedido += float(subTotalVenta)
                # EOF FOR

                tributos_globales = self.completeGlobalTributes(
                    tributos_globales)

                currentDateTime = datetime.now()
                currentTime = currentDateTime.strftime("%H:%M:%S")
                # Debe ser informada la  hora en una zona horaria -5, que es la zona horaria oficial de Colombia.
                currentTimeCreated = str(currentTime)+str("-05:00")

                secuencia = str(invoice.number).split("-")
                secuencia_serie = secuencia[0]
                secuencia_consecutivo = secuencia[1]

                dian_ambiente = str("2")
                if (str(invoice.company_id.dian_api_mode) == "SANDBOX"):
                    dian_ambiente = str("2")
                else:
                    dian_ambiente = str("1")

                # Exportacion
                data_exp = {"exportation": {}}
                data_exp["exportation"]["es_exportacion"] = str("False")
                if(str(self.is_exportation) == str("True")):
                    data_exp["exportation"]["es_exportacion"] = str(
                        self.is_exportation)
                    data_exp["exportation"]["divisa_origen"] = str(
                        invoice.currency_id.name)
                    data_exp["exportation"]["divisa_origen_rate"] = str("1.00")

                    if(str(invoice.currency_id.name) != str("COP")):
                        data_exp["exportation"]["divisa_destino"] = str("COP")
                        self.exporting_currency = 'COP'
                    else:
                        data_exp["exportation"]["divisa_destino"] = str(
                            self.exporting_currency)

                    data_exp["exportation"]["divisa_destino_rate"] = str(
                        "1.00")
                    data_exp["exportation"]["calculo_rate"] = str(
                        self.calculation_rate)  # "0.00030"

                invoice_billing_reference = self.get_invoice_billing_reference(invoice.refund_invoice_id,invoice.company_id.dian_xml_client_path)

                dian_data = {
                    "serie": str("fc"),
                    "numero": str(secuencia_consecutivo),
                    "emisor": {
                        "tipo_documento": invoice.company_id.dian_tipo_documento,
                        "nro": invoice.company_id.vat,
                        "vat_dv": invoice.company_id.vat_dv,
                        "nombre": invoice.company_id.name,
                        "correo_electronico": invoice.company_id.email,
                        "telefono": invoice.company_id.phone,
                        "tipo_persona": invoice.company_id.dian_tipo_persona,
                        "regimen": invoice.company_id.dian_regimen,
                        "responsabilidad":invoice.company_id.dian_responsabilidades,
                        "matricula": invoice.company_id.dian_matricula,
                        "ciiu":invoice.company_id.dian_ciiu,
                        "direccion": invoice.company_id.street,
                        "municipio":invoice.company_id.district_id.name,
                        "municipio_code":invoice.company_id.district_id.code,
                        "ciudad": invoice.company_id.city,
                        "ciudad_sector": invoice.company_id.street2,
                        "departamento": invoice.company_id.state_id.name,
                        "codigoPostal": invoice.company_id.zip,
                        "codigoPais": invoice.company_id.country_id.code,
                        "nombrePais": invoice.company_id.country_id.name
                    },
                    "receptor": {
                        "tipo_documento": invoice.partner_id.dian_tipo_documento,
                        "nro": invoice.partner_id.vat,
                        "vat_dv": invoice.partner_id.vat_dv,
                        "nombre": invoice.partner_id.name,
                        "correo_electronico": invoice.partner_id.email,
                        "telefono": invoice.partner_id.phone if (invoice.partner_id.phone) else invoice.partner_id.mobile,
                        "tipo_persona": invoice.partner_id.dian_tipo_persona,
                        "regimen": invoice.partner_id.dian_regimen,
                        "responsabilidad":invoice.partner_id.dian_responsabilidades,
                        "direccion": invoice.partner_id.street,
                        "municipio":invoice.partner_id.district_id.name,
                        "municipio_code":invoice.partner_id.district_id.code,
                        "ciudad": invoice.partner_id.city,
                        "ciudad_sector": invoice.partner_id.street2,
                        "departamento": invoice.partner_id.state_id.name,
                        "codigoPostal": invoice.partner_id.zip,
                        "codigoPais": invoice.partner_id.country_id.code,
                        "nombrePais": invoice.partner_id.country_id.name
                    },
                    "notaDescripcion": invoice.name,
                    "notaDiscrepanciaCode": invoice.discrepance_code,
                    "documentoOrigen": invoice_billing_reference,
                    "fechaEmision": str(invoice.date_invoice).replace("/", "-", 3),
                    "fechaVencimiento": str(invoice.date_due).replace("/", "-", 3),
                    "horaEmision": currentTimeCreated,
                    "subTotalVenta": subTotalPedido,
                    "totalVentaGravada": totalVentaPedido,
                    "tipoMoneda": invoice.currency_id.name,
                    "items": dian_items,
                    "tributos": tributos_globales,
                    "exportacion": data_exp,
                    "descuentos": {
                        "globales": global_discounts
                    },
                    "pagos": {"payment_means_code": invoice.dian_payment_means_code, "payment_id": invoice.reference,"dian_payment_means_id":int(invoice.dian_payment_means_id),"payment_due_date":str(invoice.date_due).replace("/", "-", 3)},
                    "tipo_operacion":invoice.dian_operation_type,
                    "dian": {
                        "nit": invoice.company_id.dian_emisor_nit,
                        "identificador_software": invoice.company_id.dian_emisor_username,
                        "dian_test_set_id": invoice.company_id.dian_test_set_id,
                        "pin_software": invoice.company_id.dian_emisor_password,
                        "clave_tecnica": invoice.company_id.dian_emisor_clave_tecnica,
                        "nonce": base64.b64encode(str(random.random()).encode()).decode(),
                        "created": str(currentDateTime.year)+"-"+str(currentDateTime.month)+"-"+str(currentDateTime.day)+"T"+str(currentTime),
                        "certificado": invoice.company_id.dian_certificate_filename,
                        "certificado_contrasena": invoice.company_id.dian_certificado_contrasena,
                        "autorizacion": {
                            "codigo": invoice.company_id.dian_numero_resolucion,
                            "codigo_pais": "CO",
                            "fecha_inicio": invoice.company_id.dian_fecha_inicio_resolucion,
                            "fecha_fin": invoice.company_id.dian_fecha_fin_resolucion,
                            "prefijo": invoice.company_id.dian_prefijo_resolucion_periodo,
                            "desde": invoice.company_id.dian_desde_resolucion_periodo,
                            "hasta": invoice.company_id.dian_hasta_resolucion_periodo,
                        }
                    },
                    "ambiente_ejecucion": dian_ambiente,
                    "accion": processInvoiceAction,
                    "licencia": "081OHTGAVHJZ4GOZJGJV",
                                "client_path": invoice.company_id.dian_xml_client_path
                }
                
                
                self.validate_dian_data(dian_data)
                nombre_archivo_xml = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)
                nombre_archivo_zip = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)

                xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'

                DianService = Service()
                DianService.setXMLPath(xmlPath)
                DianService.fileXmlName = nombre_archivo_xml
                DianService.fileZipName = nombre_archivo_zip
                DianService.xmlClientPath = invoice.company_id.dian_xml_client_path
                DianService.initDianAPI(
                    invoice.company_id.dian_api_mode, "sendBill")
                DianService.sunatAPI.processInvoiceAction = processInvoiceAction
                DianService.sunatAPI.dian_data = dian_data["dian"]
                DianResponse = DianService.processCreditNote(dian_data)

                # save xml documents steps for reference in edocs
                # self.response_document = DianResponse["xml_response"]
                # self.response_document_filename = str("R_")+nombre_archivo_xml+str(".xml")

                self.signed_document = DianResponse["xml_signed"]
                self.signed_document_filename = nombre_archivo_xml+str(".xml")

                self.unsigned_document = DianResponse["xml_unsigned"]
                self.unsigned_document_filename = nombre_archivo_xml + \
                    str(".xml")

                # generate qr for invoices and tickets in pos
                self.qr_image = self.generate_QR(str(dian_data['serie']) + str(dian_data['numero']))
                
                self.qr_in_report = True
                self.dian_request_type = dian_request_type
                # raise Warning("GENERATED")
                if(DianResponse["status"] == "OK"):
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    self.dian_request_status = 'OK'
                    self.qr_url = DianResponse["track_id"]["qr_url"]
                    self.qr_image = self.generate_QR(self.qr_url)
                    return super(account_invoice, self).invoice_validate()
                else:
                    self.dian_request_status = 'FAIL'
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    return super(account_invoice, self).invoice_validate()

        elif(eDocumentType == "NDB"):
            for invoice in self:
                dian_request_type = invoice.company_id.dian_request_type
                if(dian_request_type == "automatic"):
                    dian_request_type = "Automatizada"
                    processInvoiceAction = "fill_only"
                else:
                    dian_request_type = "Documento Validado"
                    processInvoiceAction = "fill_submit"

                items = invoice.invoice_line_ids
                global_discounts = []
                for item in items:
                    item_tributos = []
                    item_global_discount = []
                    item_discount = []
                    subTotalVenta = float((item.price_unit * item.quantity))
                    if(float(item.discount/100) > 0.0):
                        subTotalVenta = float(
                            subTotalVenta) - float(float(subTotalVenta) * float(item.discount/100))
                    totalVenta = subTotalVenta

                    # global discount >> point of sale config
                    if(bool(item.product_id.dian_is_product_discount) == True):
                        dian_discount_type = str(
                            item.product_id.dian_discount_type).split("-")
                        dian_discount_type_code = str(
                            dian_discount_type[0]).strip()
                        dian_discount_type_text = str(
                            dian_discount_type[1]).strip()

                        item_global_discount = {
                            "codigo": dian_discount_type_code,
                            "razon": dian_discount_type_text,
                            "porcentaje": self.get_global_discount_percent(item.product_id.id),
                            "monto": abs(item.price_subtotal)
                        }
                        global_discounts.append(item_global_discount)
                        continue
                    else:
                        pass

                    # line discount
                    if(float(item.discount) > float(0.0)):
                        item_discount = {
                            "codigo": str("08"),
                            "razon": str("Descuento por actualización de productos / servicios"),
                            "porcentaje": item.discount,
                            "monto": str(float(float((item.price_unit * item.quantity)) * float(item.discount/100)))
                        }

                    for tax in item.invoice_line_tax_ids:
                        impuesto = tax.amount/100
                        monto_afectacion_tributo = float(
                            (subTotalVenta * impuesto))

                        totalVenta += monto_afectacion_tributo

                        if(not invoice.company_id.dian_es_autoretenedor and (tax.dian_tributo == "05"  or tax.dian_tributo == "06"  or tax.dian_tributo == "07"  or tax.dian_tributo == "08")):
                            if(float(tax.amount)<0):                                
                                totalVenta -= monto_afectacion_tributo

                        item_tributo = {
                            "codigo": tax.dian_tributo,
                            "porcentaje": abs(float(tax.amount)),
                            "montoAfectacionTributo": abs(float(monto_afectacion_tributo)),
                            "total_venta": subTotalVenta
                        }
                        if(float(monto_afectacion_tributo) > 0):
                            item_tributos.append(item_tributo)

                    tributos_globales = self.add_global_tributes(
                        item_tributos, tributos_globales)

                    dian_item = {
                        'id': str(item.id),
                        'cantidad': str(item.quantity),
                        'descripcion': item.name,
                        'brand_name': item.product_id.dian_brand_name,
                        'model': item.product_id.dian_item_model,
                        'precioUnidad': item.price_unit,
                        'clasificacionProductoServicioCodigo': self.get_sunat_product_code_classification(item.product_id.id),
                        "subTotalVenta": subTotalVenta,
                        'totalVenta': totalVenta,
                        "tributos": item_tributos,
                        "descuento": item_discount
                    }
                    dian_items.append(dian_item)
                    totalVentaPedido += float(totalVenta)
                    subTotalPedido += float(subTotalVenta)
                # EOF FOR

                tributos_globales = self.completeGlobalTributes(
                    tributos_globales)

                currentDateTime = datetime.now()
                currentTime = currentDateTime.strftime("%H:%M:%S")
                # Debe ser informada la  hora en una zona horaria -5, que es la zona horaria oficial de Colombia.
                currentTimeCreated = str(currentTime)+str("-05:00")

                secuencia = str(invoice.number).split("-")
                secuencia_serie = secuencia[0]
                secuencia_consecutivo = secuencia[1]

                dian_ambiente = str("2")
                if (str(invoice.company_id.dian_api_mode) == "SANDBOX"):
                    dian_ambiente = str("2")
                else:
                    dian_ambiente = str("1")

                # Exportacion
                data_exp = {"exportation": {}}
                data_exp["exportation"]["es_exportacion"] = str("False")
                if(str(self.is_exportation) == str("True")):
                    data_exp["exportation"]["es_exportacion"] = str(
                        self.is_exportation)
                    data_exp["exportation"]["divisa_origen"] = str(
                        invoice.currency_id.name)
                    data_exp["exportation"]["divisa_origen_rate"] = str("1.00")

                    if(str(invoice.currency_id.name) != str("COP")):
                        data_exp["exportation"]["divisa_destino"] = str("COP")
                        self.exporting_currency = 'COP'
                    else:
                        data_exp["exportation"]["divisa_destino"] = str(
                            self.exporting_currency)

                    data_exp["exportation"]["divisa_destino_rate"] = str(
                        "1.00")
                    data_exp["exportation"]["calculo_rate"] = str(
                        self.calculation_rate)  # "0.00030"

                invoice_billing_reference = self.get_invoice_billing_reference(invoice.refund_invoice_id,invoice.company_id.dian_xml_client_path)
                
                #f = open("/odoo_rockscripts/custom/addons/dian_efact/data.json",'a')
                #f.write(str(self))
                #f.close()
                #raise Warning(invoice.discrepance_text)

                dian_data = {
                    "serie": str("fd"),
                    "numero": str(secuencia_consecutivo),
                    "emisor": {
                        "tipo_documento": invoice.company_id.dian_tipo_documento,
                        "nro": invoice.company_id.vat,
                        "vat_dv": invoice.company_id.vat_dv,
                        "nombre": invoice.company_id.name,
                        "correo_electronico": invoice.company_id.email,
                        "telefono": invoice.company_id.phone,
                        "tipo_persona": invoice.company_id.dian_tipo_persona,
                        "regimen": invoice.company_id.dian_regimen,
                        "responsabilidad":invoice.company_id.dian_responsabilidades,
                        "matricula": invoice.company_id.dian_matricula,
                        "ciiu":invoice.company_id.dian_ciiu,
                        "direccion": invoice.company_id.street,
                        "municipio":invoice.company_id.district_id.name,
                        "municipio_code":invoice.company_id.district_id.code,
                        "ciudad": invoice.company_id.city,
                        "ciudad_sector": invoice.company_id.street2,
                        "departamento": invoice.company_id.state_id.name,
                        "codigoPostal": invoice.company_id.zip,
                        "codigoPais": invoice.company_id.country_id.code,
                        "nombrePais": invoice.company_id.country_id.name
                    },
                    "receptor": {
                        "tipo_documento": invoice.partner_id.dian_tipo_documento,
                        "nro": invoice.partner_id.vat,
                        "vat_dv": invoice.partner_id.vat_dv,
                        "nombre": invoice.partner_id.name,
                        "correo_electronico": invoice.partner_id.email,
                        "telefono": invoice.partner_id.phone if (invoice.partner_id.phone) else invoice.partner_id.mobile,
                        "tipo_persona": invoice.partner_id.dian_tipo_persona,
                        "regimen": invoice.partner_id.dian_regimen,
                        "responsabilidad":invoice.partner_id.dian_responsabilidades,
                        "direccion": invoice.partner_id.street,
                        "municipio":invoice.partner_id.district_id.name,
                        "municipio_code":invoice.partner_id.district_id.code,
                        "ciudad": invoice.partner_id.city,
                        "ciudad_sector": invoice.partner_id.street2,
                        "departamento": invoice.partner_id.state_id.name,
                        "codigoPostal": invoice.partner_id.zip,
                        "codigoPais": invoice.partner_id.country_id.code,
                        "nombrePais": invoice.partner_id.country_id.name
                    },
                    "notaDescripcion": invoice.name,
                    "notaDiscrepanciaCode": invoice.discrepance_code,
                    "documentoOrigen": invoice_billing_reference,
                    "fechaEmision": str(invoice.date_invoice).replace("/", "-", 3),
                    "fechaVencimiento": str(invoice.date_due).replace("/", "-", 3),
                    "horaEmision": currentTimeCreated,
                    "subTotalVenta": subTotalPedido,
                    "totalVentaGravada": totalVentaPedido,
                    "tipoMoneda": invoice.currency_id.name,
                    "items": dian_items,
                    "tributos": tributos_globales,
                    "exportacion": data_exp,
                    "descuentos": {
                        "globales": global_discounts
                    },
                    "pagos": {"payment_means_code": invoice.dian_payment_means_code, "payment_id": invoice.reference,"dian_payment_means_id":int(invoice.dian_payment_means_id),"payment_due_date":str(invoice.date_due).replace("/", "-", 3)},
                    "tipo_operacion":invoice.dian_operation_type,
                    "dian": {
                        "nit": invoice.company_id.dian_emisor_nit,
                        "identificador_software": invoice.company_id.dian_emisor_username,
                        "dian_test_set_id": invoice.company_id.dian_test_set_id,
                        "pin_software": invoice.company_id.dian_emisor_password,
                        "clave_tecnica": invoice.company_id.dian_emisor_clave_tecnica,
                        "nonce": base64.b64encode(str(random.random()).encode()).decode(),
                        "created": str(currentDateTime.year)+"-"+str(currentDateTime.month)+"-"+str(currentDateTime.day)+"T"+str(currentTime),
                        "certificado": invoice.company_id.dian_certificate_filename,
                        "certificado_contrasena": invoice.company_id.dian_certificado_contrasena,
                        "autorizacion": {
                            "codigo": invoice.company_id.dian_numero_resolucion,
                            "codigo_pais": "CO",
                            "fecha_inicio": invoice.company_id.dian_fecha_inicio_resolucion,
                            "fecha_fin": invoice.company_id.dian_fecha_fin_resolucion,
                            "prefijo": invoice.company_id.dian_prefijo_resolucion_periodo,
                            "desde": invoice.company_id.dian_desde_resolucion_periodo,
                            "hasta": invoice.company_id.dian_hasta_resolucion_periodo,
                        }
                    },
                    "ambiente_ejecucion": dian_ambiente,
                    "accion": processInvoiceAction,
                    "licencia": "081OHTGAVHJZ4GOZJGJV",
                                "client_path": invoice.company_id.dian_xml_client_path
                }
                
                #with open('/odoo_rockscripts/custom/addons/dian_efact/data.json', 'w') as outfile:
                #    json.dump(dian_data, outfile)
                self.validate_dian_data(dian_data)
                nombre_archivo_xml = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)
                nombre_archivo_zip = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)

                xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'

                DianService = Service()
                DianService.setXMLPath(xmlPath)
                DianService.fileXmlName = nombre_archivo_xml
                DianService.fileZipName = nombre_archivo_zip
                DianService.xmlClientPath = invoice.company_id.dian_xml_client_path
                DianService.initDianAPI(
                    invoice.company_id.dian_api_mode, "sendBill")
                DianService.sunatAPI.processInvoiceAction = processInvoiceAction
                DianService.sunatAPI.dian_data = dian_data["dian"]
                DianResponse = DianService.processDebitNote(dian_data)

                #with open('/odoo_rockscripts/custom/addons/dian_efact/data.json', 'w') as outfile:
                #    json.dump(dian_data, outfile)
                #raise Warning("g")
                # raise Warning(DianResponse["body"])
                # save xml documents steps for reference in edocs
                # self.response_document = DianResponse["xml_response"]
                # self.response_document_filename = str("R_")+nombre_archivo_xml+str(".xml")

                self.signed_document = DianResponse["xml_signed"]
                self.signed_document_filename = nombre_archivo_xml+str(".xml")

                self.unsigned_document = DianResponse["xml_unsigned"]
                self.unsigned_document_filename = nombre_archivo_xml + \
                    str(".xml")

                self.qr_image = self.generate_QR(str(dian_data['serie']) + str(dian_data['numero']))
                
                self.qr_in_report = True
                self.dian_request_type = dian_request_type
                # raise Warning("GENERATED")
                if(DianResponse["status"] == "OK"):
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    self.dian_request_status = 'OK'
                    self.qr_url = DianResponse["track_id"]["qr_url"]
                    self.qr_image = self.generate_QR(self.qr_url)
                    return super(account_invoice, self).invoice_validate()
                else:
                    self.dian_request_status = 'FAIL'
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    return super(account_invoice, self).invoice_validate()

        elif(eDocumentType == "BOL"):
            index = 0

        elif(eDocumentType == "FAC" or eDocumentType == "INV" or eDocumentType == "EFACT"):
            for invoice in self:
                dian_request_type = invoice.company_id.dian_request_type
                if(dian_request_type == "automatic"):
                    dian_request_type = "Automatizada"
                    processInvoiceAction = "fill_only"
                else:
                    dian_request_type = "Documento Validado"
                    processInvoiceAction = "fill_submit"

                items = invoice.invoice_line_ids
                global_discounts = []
                for item in items:

                    item_tributos = []
                    item_global_discount = []
                    item_discount = []
                    subTotalVenta = float((item.price_unit * item.quantity))
                    if(float(item.discount/100) > 0.0):
                        subTotalVenta = float(
                            subTotalVenta) - float(float(subTotalVenta) * float(item.discount/100))
                    totalVenta = subTotalVenta

                    # global discount >> point of sale config
                    if(bool(item.product_id.dian_is_product_discount) == True):
                        dian_discount_type = str(
                            item.product_id.dian_discount_type).split("-")
                        dian_discount_type_code = str(
                            dian_discount_type[0]).strip()
                        dian_discount_type_text = str(
                            dian_discount_type[1]).strip()

                        item_global_discount = {
                            "codigo": dian_discount_type_code,
                            "razon": dian_discount_type_text,
                            "porcentaje": self.get_global_discount_percent(item.product_id.id),
                            "monto": abs(item.price_subtotal)
                        }
                        global_discounts.append(item_global_discount)
                        continue
                    else:
                        pass

                    # line discount
                    if(float(item.discount) > float(0.0)):
                        item_discount = {
                            "codigo": str("08"),
                            "razon": str("Descuento por actualización de productos / servicios"),
                            "porcentaje": item.discount,
                            "monto": str(float(float((item.price_unit * item.quantity)) * float(item.discount/100)))
                        }

                    for tax in item.invoice_line_tax_ids:
                        impuesto = tax.amount/100
                        monto_afectacion_tributo = float(
                            (subTotalVenta * impuesto))

                        totalVenta += monto_afectacion_tributo

                        if(not invoice.company_id.dian_es_autoretenedor and (tax.dian_tributo == "05"  or tax.dian_tributo == "06"  or tax.dian_tributo == "07"  or tax.dian_tributo == "08")):
                            if(float(tax.amount)<0):                                
                                totalVenta -= monto_afectacion_tributo

                        item_tributo = {
                            "codigo": tax.dian_tributo,
                            "porcentaje": abs(float(tax.amount)),
                            "montoAfectacionTributo": abs(float(monto_afectacion_tributo)),
                            "total_venta": subTotalVenta
                        }
                        if(float(monto_afectacion_tributo) > 0):
                            item_tributos.append(item_tributo)


                    tributos_globales = self.add_global_tributes(
                        item_tributos, tributos_globales)

                    dian_item = {
                        'id': str(item.id),
                        'cantidad': str(item.quantity),
                        'descripcion': item.name,
                        'brand_name': item.product_id.dian_brand_name,
                        'model': item.product_id.dian_item_model,
                        'precioUnidad': item.price_unit,
                        'clasificacionProductoServicioCodigo': self.get_sunat_product_code_classification(item.product_id.id),
                        "subTotalVenta": subTotalVenta,
                        'totalVenta': totalVenta,
                        "tributos": item_tributos,
                        "descuento": item_discount
                    }
                    dian_items.append(dian_item)
                    totalVentaPedido += float(totalVenta)
                    subTotalPedido += float(subTotalVenta)
                # EOF FOR

                tributos_globales = self.completeGlobalTributes(
                    tributos_globales)

                currentDateTime = datetime.now()
                currentTime = currentDateTime.strftime("%H:%M:%S")
                # Debe ser informada la  hora en una zona horaria -5, que es la zona horaria oficial de Colombia.
                currentTimeCreated = str(currentTime)+str("-05:00")

                secuencia = str(invoice.number).split("-")
                secuencia_serie = secuencia[0]
                secuencia_consecutivo = secuencia[1]

                dian_ambiente = str("2")
                if (str(invoice.company_id.dian_api_mode) == "SANDBOX"):
                    dian_ambiente = str("2")
                else:
                    dian_ambiente = str("1")

                # Exportacion
                data_exp = {"exportation": {}}
                data_exp["exportation"]["es_exportacion"] = str("False")
                if(str(self.is_exportation) == str("True")):
                    data_exp["exportation"]["es_exportacion"] = str(
                        self.is_exportation)
                    data_exp["exportation"]["divisa_origen"] = str(
                        invoice.currency_id.name)
                    data_exp["exportation"]["divisa_origen_rate"] = str("1.00")

                    if(str(invoice.currency_id.name) != str("COP")):
                        data_exp["exportation"]["divisa_destino"] = str("COP")
                        self.exporting_currency = 'COP'
                    else:
                        data_exp["exportation"]["divisa_destino"] = str(
                            self.exporting_currency)

                    data_exp["exportation"]["divisa_destino_rate"] = str(
                        "1.00")
                    data_exp["exportation"]["calculo_rate"] = str(
                        self.calculation_rate)  # "0.00030"

                #p_dian_municipio = invoice.partner_id.dian_municipio
                #p_dian_municipio = p_dian_municipio.split("|")
                #p_municipio = p_dian_municipio[1]
                #p_municipio_code = p_dian_municipio[0]
#
                #c_dian_municipio = invoice.company_id.dian_municipio
                #c_dian_municipio = c_dian_municipio.split("|")
                #c_municipio = c_dian_municipio[1]
                #c_municipio_code = c_dian_municipio[0]

                dian_data = {
                    "serie": str("fv"),
                    "numero": str(secuencia_consecutivo),
                    "emisor": {
                        "tipo_documento": invoice.company_id.dian_tipo_documento,
                        "nro": invoice.company_id.vat,
                        "vat_dv": invoice.company_id.vat_dv,
                        "nombre": invoice.company_id.name,
                        "correo_electronico": invoice.company_id.email,
                        "telefono": invoice.company_id.phone,
                        "tipo_persona": invoice.company_id.dian_tipo_persona,
                        "regimen": invoice.company_id.dian_regimen,
                        "responsabilidad":invoice.company_id.dian_responsabilidades,
                        "matricula": invoice.company_id.dian_matricula,
                        "ciiu":invoice.company_id.dian_ciiu,
                        "direccion": invoice.company_id.street,
                        "municipio":invoice.company_id.district_id.name,
                        "municipio_code":invoice.company_id.district_id.code,
                        "ciudad": invoice.company_id.city,
                        "ciudad_sector": invoice.company_id.street2,
                        "departamento": invoice.company_id.state_id.name,
                        "codigoPostal": invoice.company_id.zip,
                        "codigoPais": invoice.company_id.country_id.code,
                        "nombrePais": invoice.company_id.country_id.name
                    },
                    "receptor": {
                        "tipo_documento": invoice.partner_id.dian_tipo_documento,
                        "nro": invoice.partner_id.vat,
                        "vat_dv": invoice.partner_id.vat_dv,
                        "nombre": invoice.partner_id.name,
                        "correo_electronico": invoice.partner_id.email,
                        "telefono": invoice.partner_id.phone if (invoice.partner_id.phone) else invoice.partner_id.mobile,
                        "tipo_persona": invoice.partner_id.dian_tipo_persona,
                        "regimen": invoice.partner_id.dian_regimen,
                        "responsabilidad":invoice.partner_id.dian_responsabilidades,
                        "direccion": invoice.partner_id.street,
                        "municipio":invoice.partner_id.district_id.name,
                        "municipio_code":invoice.partner_id.district_id.code,
                        "ciudad": invoice.partner_id.city,
                        "ciudad_sector": invoice.partner_id.street2,
                        "departamento": invoice.partner_id.state_id.name,
                        "codigoPostal": invoice.partner_id.zip,
                        "codigoPais": invoice.partner_id.country_id.code,
                        "nombrePais": invoice.partner_id.country_id.name
                    },
                    "fechaEmision": str(invoice.date_invoice).replace("/", "-", 3),
                    "fechaVencimiento": str(invoice.date_due).replace("/", "-", 3),
                    "horaEmision": currentTimeCreated,
                    "subTotalVenta": subTotalPedido,
                    "totalVentaGravada": totalVentaPedido,
                    "tipoMoneda": invoice.currency_id.name,
                    "items": dian_items,
                    "tributos": tributos_globales,
                    "exportacion": data_exp,
                    "descuentos": {
                        "globales": global_discounts
                    },
                    "pagos": {"payment_means_code": invoice.dian_payment_means_code, "payment_id": invoice.reference,"dian_payment_means_id":int(invoice.dian_payment_means_id),"payment_due_date":str(invoice.date_due).replace("/", "-", 3)},
                    "tipo_operacion":invoice.dian_operation_type,
                    "dian": {
                        "nit": invoice.company_id.dian_emisor_nit,
                        "identificador_software": invoice.company_id.dian_emisor_username,
                        "dian_test_set_id": invoice.company_id.dian_test_set_id,
                        "pin_software": invoice.company_id.dian_emisor_password,
                        "clave_tecnica": invoice.company_id.dian_emisor_clave_tecnica,
                        "nonce": base64.b64encode(str(random.random()).encode()).decode(),
                        "created": str(currentDateTime.year)+"-"+str(currentDateTime.month)+"-"+str(currentDateTime.day)+"T"+str(currentTime),
                        "certificado": invoice.company_id.dian_certificate_filename,
                        "certificado_contrasena": invoice.company_id.dian_certificado_contrasena,
                        "autorizacion": {
                            "codigo": invoice.company_id.dian_numero_resolucion,
                            "codigo_pais": "CO",
                            "fecha_inicio": invoice.company_id.dian_fecha_inicio_resolucion,
                            "fecha_fin": invoice.company_id.dian_fecha_fin_resolucion,
                            "prefijo": invoice.company_id.dian_prefijo_resolucion_periodo,
                            "desde": invoice.company_id.dian_desde_resolucion_periodo,
                            "hasta": invoice.company_id.dian_hasta_resolucion_periodo,
                        }
                    },
                    "ambiente_ejecucion": dian_ambiente,
                    "accion": processInvoiceAction,
                    "licencia": "081OHTGAVHJZ4GOZJGJV",
                                "client_path": invoice.company_id.dian_xml_client_path
                }
                #with open('/odoo_rockscripts/custom/addons/dian_efact/log.json', 'w') as outfile:
                #    json.dump(dian_data, outfile)
                #raise Warning("in")

                self.validate_dian_data(dian_data)
                nombre_archivo_xml = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)
                nombre_archivo_zip = str(
                    secuencia_serie)+str(invoice.company_id.vat)+str(secuencia_consecutivo)

                xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'

                DianService = Service()
                DianService.setXMLPath(xmlPath)
                DianService.fileXmlName = nombre_archivo_xml
                DianService.fileZipName = nombre_archivo_zip
                DianService.xmlClientPath = invoice.company_id.dian_xml_client_path
                DianService.initDianAPI(
                    invoice.company_id.dian_api_mode, "sendBill")
                DianService.sunatAPI.processInvoiceAction = processInvoiceAction
                DianService.sunatAPI.dian_data = dian_data["dian"]
                DianResponse = DianService.processInvoice(dian_data)

                #raise Warning(DianResponse['body'])
                # save xml documents steps for reference in edocs
                # self.response_document = DianResponse["xml_response"]
                # self.response_document_filename = str("R_")+nombre_archivo_xml+str(".xml")

                self.signed_document = DianResponse["xml_signed"]
                self.signed_document_filename = nombre_archivo_xml+str(".xml")

                self.unsigned_document = DianResponse["xml_unsigned"]
                self.unsigned_document_filename = nombre_archivo_xml + \
                    str(".xml")
                
                self.qr_image = self.generate_QR(str(dian_data['serie']) + str(dian_data['numero']))
                
                self.qr_in_report = True
                self.dian_request_type = dian_request_type
                # raise Warning("GENERATED")
                if(DianResponse["status"] == "OK"):
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    self.dian_request_status = 'OK'
                    self.qr_url = DianResponse["track_id"]["qr_url"]
                    self.qr_image = self.generate_QR(self.qr_url)
                    return super(account_invoice, self).invoice_validate()
                else:
                    self.dian_request_status = 'FAIL'
                    self.api_message = "ESTADO: " + \
                        str(DianResponse["status"])+"\n" + \
                        "DESCRIPCIÓN: "+str(DianResponse["body"])
                    #raise Warning(self.api_message)
                    return super(account_invoice, self).invoice_validate()
        else:
            for invoice in self:
                self.generate_QR(str(invoice.number))
            return super(account_invoice, self).invoice_validate()

    def validate_dian_data(self, dian_data):
        # validate sender and receiver contact
        errors = str("")
        # SENDER
        
        if(not dian_data["emisor"]["tipo_documento"]):
            errors = str(errors) + str("- Tipo de documento del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["nro"]):
            errors = str(errors) + str("- Número físcal del emisor.") + str("\n")
        
        if('nro' in dian_data["emisor"]):
            if(dian_data["emisor"]["tipo_documento"]=="31"):
                if(not dian_data["emisor"]["vat_dv"]):
                    errors = str(errors) + str("- El DV del número fiscal del emisor no esta establecido.") + str("\n")

        if(not dian_data["emisor"]["nombre"]):
            errors = str(errors) + str("- Nombre del emisor.") + str("\n")

        if(not dian_data["emisor"]["correo_electronico"]):
            errors = str(errors) + str("- Correo electrónico del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["telefono"]):
            errors = str(errors) + str("- Teléfono del emisor.") + str("\n")

        if(not dian_data["emisor"]["matricula"]):
            errors = str(errors) + str("- Matricula mercantil del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["ciiu"]):
            errors = str(errors) + str("- CIIU actividades del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["nombrePais"]):
            errors = str(errors) + str("- País del emisor.") + str("\n")

        if(not dian_data["emisor"]["departamento"]):
            errors = str(errors) + str("- Departamento del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["municipio"]):
            errors = str(errors) + str("- Municipio del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["direccion"]):
            errors = str(errors) + str("- Dirección del emisor.") + str("\n")
        
        if(not dian_data["emisor"]["codigoPostal"]):
            errors = str(errors) + str("- Código postal del emisor.") + str("\n")        

        #RECEIVER
        if(not dian_data["receptor"]["tipo_documento"]):
            errors = str(errors) + str("- Tipo de documento del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["nro"]):
            errors = str(errors) + str("- Número físcal del receptor.") + str("\n")
        
        if('nro' in dian_data["receptor"]):
            if(dian_data["receptor"]["tipo_documento"]=="31"):
                if(not dian_data["receptor"]["vat_dv"]):
                    errors = str(errors) + str("- El DV del número fiscal del receptor no esta establecido.") + str("\n")
        
        #with open('/odoo_rockscripts/custom/addons/dian_efact/data.json', 'w') as outfile:
        #    json.dump(dian_data, outfile)
        #raise Warning(dian_data)

        if(not dian_data["receptor"]["nombre"]):
            errors = str(errors) + str("- Nombre del receptor.") + str("\n")

        if(not dian_data["receptor"]["correo_electronico"]):
            errors = str(errors) + str("- Correo electrónico del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["telefono"]):
            errors = str(errors) + str("- Teléfono del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["nombrePais"]):
            errors = str(errors) + str("- País del receptor.") + str("\n")

        if(not dian_data["receptor"]["departamento"]):
            errors = str(errors) + str("- Departamento del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["municipio"]):
            errors = str(errors) + str("- Municipio del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["direccion"]):
            errors = str(errors) + str("- Dirección del receptor.") + str("\n")
        
        if(not dian_data["receptor"]["codigoPostal"]):
            errors = str(errors) + str("- Código postal del receptor.") + str("\n") 
        

        if(not dian_data["pagos"]["payment_id"]):
            errors = str(errors) + str("- Referencia del pago.") + str("\n")


        #DIAN SOFTWARE
        if(not dian_data["dian"]["nit"]):
            errors = str(errors) + str("- El NIT del software emisor no se establecio.") + str("\n")
        
        if(not dian_data["dian"]["identificador_software"]):
            errors = str(errors) + str("- El Identificador del software emisor no se establecio.") + str("\n")
        
        if(dian_data["ambiente_ejecucion"]=="2"):
            if(not dian_data["dian"]["dian_test_set_id"]):
                errors = str(errors) + str("- El set de pruebas del software emisor no se establecio.") + str("\n")
        
        if(not dian_data["dian"]["pin_software"]):
            errors = str(errors) + str("- El pin del software emisor no se establecio.") + str("\n")
        
        if(not dian_data["dian"]["clave_tecnica"]):
            errors = str(errors) + str("- La clave técnica del software emisor no se establecio.") + str("\n")
        
        if(not dian_data["dian"]["certificado"]):
            errors = str(errors) + str("- El certificado no del software emisor no se establecio.") + str("\n")

        if(not dian_data["dian"]["certificado_contrasena"]):
            errors = str(errors) + str("- el certificado del software no tiene contraseña establecida.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["codigo"]):
            errors = str(errors) + str("- La resolución del software no esta establecida.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["fecha_inicio"]):
            errors = str(errors) + str("- La Fecha inicio de la resolución del software no esta establecida.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["fecha_fin"]):
            errors = str(errors) + str("- La Fecha fin de la resolución del software no esta establecida.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["prefijo"]):
            errors = str(errors) + str("- El prefijo del software no esta establecido.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["desde"]):
            errors = str(errors) + str("- El rango de la numeración prefijo INICIO del software no esta establecido.") + str("\n")
        
        if(not dian_data["dian"]["autorizacion"]["hasta"]):
            errors = str(errors) + str("- El rango de la numeración del prefijo HASTA del software no esta establecido.") + str("\n")

        if(errors != ""):
            errors = str("Completar los siguientes campos: ") + str("\n") + errors
            raise Warning(errors)

    @api.onchange('currency_id')
    def selectExportDivisa(self):
        if(self.currency_id == "USD"):
            self.exporting_currency == "COP"
        if(self.currency_id != "USD"):
            self.exporting_currency == "USD"

    def _get_active_currencies(self):
        query = "select name, symbol from res_currency where active = TRUE"
        request.cr.execute(query)
        currencies = request.cr.dictfetchall()
        currencies_selection = []
        for currency in currencies:
            currencies_selection.append((currency['name'], str(
                currency['symbol'])+str(" ")+str(currency['name'])))
        return currencies_selection

    def _get_payment_means_code(self):
        XMLpath = os.path.dirname(os.path.abspath(__file__))+'/xml/XMLDian/'
        tree = etree.parse(XMLpath+"MediosPago-2.1.xml")
        CodeList = tree.getroot()
        payment_means_codes_selection = []
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
                payment_means_codes_selection.append((code, name))

        return payment_means_codes_selection

    def _get_operation_types(self):
        XMLpath = os.path.dirname(os.path.abspath(__file__))+'/xml/XMLDian/'
        tree = etree.parse(XMLpath+"TiposOperacion.xml")
        CodeList = tree.getroot()
        payment_operation_types_selection = []
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
                payment_operation_types_selection.append((code, name))

        return payment_operation_types_selection

    def exist_main_tribute(self, tributos, tributo):
        if(tributos.__len__() > 0):
            found = False
            for tributo_code in tributos:
                if(str(tributo_code) == tributo["codigo"]):
                    found = True
        else:
            found = False
        return found

    def exist_child_tribute(self, tributos, tributo):
        if(tributos.__len__() > 0):
            found = False

            for tributo_code in tributos:
                if(str(tributo_code) == tributo["codigo"]):
                    for tributo_item_percent_differenced in tributos[str(tributo_code)]:
                        if(tributo_item_percent_differenced["porcentaje"] == tributo["porcentaje"]):
                            found = True
        else:
            found = False
        return found

    def add_global_tributes(self, item_tributos, tributos_globales):
        if(item_tributos.__len__() > 0):

            for item_tributo in item_tributos:
                tributo_global_nuevo = {
                    "codigo": item_tributo["codigo"],
                    "total_venta": item_tributo["total_venta"],
                    "porcentaje": item_tributo["porcentaje"],
                    "sumatoria": item_tributo["montoAfectacionTributo"]
                }

                if(self.exist_main_tribute(tributos_globales, item_tributo) == False):
                    tributos_globales.update({str(item_tributo["codigo"]): []})
                    tributos_globales[str(item_tributo["codigo"])].append(
                        tributo_global_nuevo)

                else:
                    position_child_tribute = self.exist_child_tribute(
                        tributos_globales, item_tributo)
                    if(position_child_tribute == False):
                        tributos_globales[str(item_tributo["codigo"])].append(
                            tributo_global_nuevo)
                    else:
                        for tributo_item_percent_differenced in tributos_globales[str(item_tributo["codigo"])]:
                            if(tributo_item_percent_differenced["porcentaje"] == item_tributo["porcentaje"]):
                                tributo_global_update = {
                                    "total_venta": (float(tributo_item_percent_differenced["total_venta"])+float(item_tributo["total_venta"])),
                                    "sumatoria": (float(tributo_item_percent_differenced["sumatoria"])+float(item_tributo["montoAfectacionTributo"]))
                                }

                                tributo_item_percent_differenced.update(
                                    tributo_global_update)

        return tributos_globales

    def get_sunat_product_code_classification(self, item_id):
        return str("")
        query = "select sunat_product_code from product_template where id = " + \
            str(item_id)
        request.cr.execute(query)
        product = request.cr.dictfetchone()
        sunat_product_code_parts = str(
            product["sunat_product_code"]).split(" -- ")
        return sunat_product_code_parts[0]

    def get_global_discount_percent(self, item_id):
        query = "select discount_pc from pos_config where discount_product_id = " + \
            str(item_id)
        request.cr.execute(query)
        pos_config = request.cr.dictfetchone()
        return pos_config["discount_pc"]

    def _compute_sign_taxes(self):
        for invoice in self:
            sign = invoice.type in ['in_refund', 'out_refund'] and -1 or 1
            invoice.amount_untaxed_invoice_signed = invoice.amount_untaxed * sign
            invoice.amount_tax_signed = invoice.amount_tax * sign

    def check_client_dirs(self, xmlClientPath):
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'

        try:
            if not os.path.exists(xmlPath+'/XMLdocuments/2_unsigned/'+xmlClientPath):
                os.makedirs(xmlPath+'/XMLdocuments/2_unsigned/' +
                            xmlClientPath, mode=0o777)
            if not os.path.exists(xmlPath+'/XMLdocuments/3_signed/'+xmlClientPath):
                os.makedirs(xmlPath+'/XMLdocuments/3_signed/' +
                            xmlClientPath, mode=0o777)
            if not os.path.exists(xmlPath+'/XMLdocuments/4_compressed/'+xmlClientPath):
                os.makedirs(xmlPath+'/XMLdocuments/4_compressed/' +
                            xmlClientPath, mode=0o777)
            if not os.path.exists(xmlPath+'/XMLresponses/'+xmlClientPath):
                os.makedirs(xmlPath+'/XMLresponses/'+xmlClientPath, mode=0o777)
            if not os.path.exists(xmlPath+'/XMLcertificates/'+xmlClientPath):
                os.makedirs(xmlPath+'/XMLcertificates/' +
                            xmlClientPath, mode=0o777)
            # os.system("sudo su")
            print('pre sudo')
            os.system("sudo chmod -R 0777 "+xmlPath)
            print('pos sudo')
            if(os.stat(xmlPath+'/XMLdocuments/2_unsigned/'+xmlClientPath).st_mode != 16895 or
               os.stat(xmlPath+'/XMLdocuments/3_signed/'+xmlClientPath).st_mode != 16895 or
               os.stat(xmlPath+'/XMLdocuments/4_compressed/'+xmlClientPath).st_mode != 16895):
                raise Warning(
                    "[XMLdocuments] - No hay suficiente permisos de escritura para la compañia actual. Por favor contacte con el administrador del sistema")

        except Exception as e:
            exc_traceback = sys.exc_info()
            raise Warning("ERROR \ "+getattr(e, 'message', repr(e)) +
                          " ON LINE "+format(sys.exc_info()[-1].tb_lineno))
            # with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #     json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)

    @api.depends('state', 'journal_id', 'date_invoice')
    def _get_sequence_prefix(self):
        """ computes the prefix of the number that will be assigned to the first invoice/bill/refund of a journal, in order to
        let the user manually change it.
        """
        # if not self.env.user._is_system():
        #    for invoice in self:
        #        invoice.sequence_number_next_prefix = False
        #        invoice.sequence_number_next = ''
        #    return
        for invoice in self:
            journal_sequence, domain = invoice._get_seq_number_next_stuff()
            if (invoice.state == 'draft') and not self.search(domain, limit=1):
                prefix, dummy = journal_sequence.with_context(ir_sequence_date=invoice.date_invoice,
                                                              ir_sequence_date_range=invoice.date_invoice)._get_prefix_suffix()
                invoice.sequence_number_next_prefix = prefix
            else:
                invoice.sequence_number_next_prefix = False

    @api.depends('current_company_id')
    def _current_company_id(self):
        uid = http.request.env.context.get('uid')
        query = "select company_id from res_users where id = '" + \
            str(uid) + "'"
        request.cr.execute(query)
        res_users = request.cr.dictfetchone()
        for record in self:
            if(int(record.company_id) != int(res_users['company_id'])):
                self.update({'current_company_id': 0})
                record.current_company_id = int(0)
            else:
                self.update({'current_company_id': res_users['company_id']})
                record.current_company_id = int(res_users['company_id'])

            self = self.env['dian.edocs'].search(
                [('company_id', '=', res_users['company_id'])])

    def completeGlobalTributes(self, tributos_globales):

        if("01" not in tributos_globales):
            item_tributo = [{
                "codigo": "01",
                "total_venta": 0.00,
                "porcentaje": 19.00,
                "sumatoria": 0.00
            }]
            tributos_globales['01'] = item_tributo

        if("04" not in tributos_globales):
            item_tributo = [{
                "codigo": "04",
                "total_venta": 0.00,
                "porcentaje": 0.00,
                "sumatoria": 0.00
            }]
            tributos_globales['04'] = item_tributo

        if("03" not in tributos_globales):
            item_tributo = [{
                "codigo": "03",
                "total_venta": 0.00,
                "porcentaje": 0.00,
                "sumatoria": 0.00
            }]
            tributos_globales['03'] = item_tributo
        return tributos_globales

    def get_invoice_billing_reference(self, refund_invoice_id, dian_xml_client_path):
        
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'
        xmlUnsigned = str(xmlPath+"/XMLdocuments/3_signed/"+dian_xml_client_path+'/')+str(refund_invoice_id.signed_document_filename) # an xml file

        tree = etree.parse(xmlUnsigned)
        MainNode = tree.getroot()
        UUID = MainNode.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"+"UUID")
        uuid = UUID.text

        IssueDate = MainNode.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"+"IssueDate")
        issue_date = IssueDate.text

        ID = MainNode.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"+"ID")
        _id = ID.text

        invoice_billing_reference = {"_id":_id,"number_sequence":refund_invoice_id.number,"uuid":uuid,"issue_date":issue_date}
        return invoice_billing_reference

    def generate_QR(self, data):
        qr = qrcode.QRCode (
                                version=1,
                                error_correction=qrcode.constants.ERROR_CORRECT_L,
                                box_size=20,
                                border=4,
                            )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        return base64.b64encode(temp.getvalue())
    
    def _generate_email_ubl_attachment(self):
        self.ensure_one()
        attachments = self.env['ir.attachment']
        if self.type not in ('out_invoice', 'out_refund'):
            return attachments
        if self.state not in ('open', 'paid'):
            return attachments                

        ubl_filename = self.signed_document_filename        
        xml_signed = self.get_ubl_signed_document()
        if(xml_signed):
           
            return self.env['ir.attachment'].with_context({}).create({
                'name': ubl_filename,
                'res_model': str(self._name),
                'res_id': self.id,
                'datas': xml_signed,
                'datas_fname': ubl_filename,
                'type': 'binary',
            })
        else:
            return None

    def get_ubl_signed_document(self):
        xmlPath = os.path.dirname(os.path.abspath(__file__))+'/xml'
        try:
            secuencia = str(self.number).split("-")
            secuencia_serie = secuencia[0]
            secuencia_consecutivo = secuencia[1]
            nombre_archivo_xml = str(secuencia_serie)+str(self.company_id.vat)+str(secuencia_consecutivo)            
            fileContents = open(xmlPath+'/XMLdocuments/3_signed/'+ self.company_id.dian_xml_client_path + str("/") + str(nombre_archivo_xml)+".xml", "rb").read()
            encoded = base64.b64encode(fileContents)
            return encoded
        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/odoo_dian_v12/custom/addons/dian_efact/log.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) + xmlPath+'/XMLdocuments/3_signed/'+ self.company_id.dian_emisor_nit + str("/") + self.company_id.dian_xml_client_path + str("/") + str(nombre_archivo_xml)+".xml", outfile)
            return None
        return None

    def restablecer_documento(self):
        if(self.dian_request_status==str("OK")):
            raise Warning('El documento no puede ser regenerado porque ya ha sido aceptado esta correcto. Se permite las acción de crear una rectificativa sobre este documento.')        

        response = self.can_create_notes()
        if(response["found"]==True):
            raise Warning('El documento no puede ser regenerado porque tiene nota de crédito.')

        self.state = "draft"
        self.dian_request_status = "No Emitido"
        self.api_message = "Documento contable sin emitir."
        #self.discrepance_code = ""
        #self.discrepance_text = ""
        self.unsigned_document = None
        self.unsigned_document_filename = ''
        self.signed_document = None
        self.signed_document_filename = ''
        self.response_document = None
        self.response_document_filename = ''
        self.qr_image = None
    
    def can_create_notes(self):
        query = "select id, number from account_invoice where origin = '"+str(self.id)+"' and discrepance_code='2'"
        request.cr.execute(query)
        refund_invoice = request.cr.dictfetchone()
        if(refund_invoice):
            refund_invoice["found"] = True
        else:
            refund_invoice = {}
            refund_invoice["found"] = False
        return refund_invoice
