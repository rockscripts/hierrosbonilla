# -*- coding: utf-8 -*-
from . documents import Documents
from . sunatapi import SunatApi
from . ruc import Ruc
import json, sys
from os import path
from . wsdl import Wsdl
from json2xml import json2xml, readfromurl, readfromstring, readfromjson
import pathlib
import os.path
import pwd
import base64
import requests
from lxml import etree
from zipfile import ZipFile
import time

class Service:
    xmlPath = False
    fileXmlName = False
    fileZipName = False
    xmlClientPath = False
    sunatAPI = False
    keys = ['081OHTGAVHJZ4GOZJGJV']

    def consultNIT(self, ruc):        
        rucService = Ruc()
        rucService.setXMLPath(self.xmlPath)        
        response = rucService.consultNIT(str(ruc))
        return response    

    def processInvoiceFromSignedXML(self, data):
        has_licence = self.validateLicence(data)
        if(has_licence==True):
            has_licence = True
        else:
            return has_licence
        response = {}
        try:
            docs = Documents()
            docs.documentXmlName = self.fileXmlName
            docs.documentZipName = self.fileZipName
            docs.xmlClientPath = self.xmlClientPath
            docs.setXMLPath(self.xmlPath)
            config = {
                            'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                            'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                            'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                            'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                            'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                            'key_file_password': data["dian"]["certificado_contrasena"],
                            'filename': docs.documentXmlName+str(".zip")
                        }   
            docs.signDocument(config)
            if(data['accion']=="fill_submit"):
                    wasZipped = docs.zipDocument()
                    if (wasZipped==True):
                        zipFileEncoded = docs.Base64EncodeDocument()
                        config ['zipped_file'] = zipFileEncoded                
                        response = self.doRequestDian(config, data)

        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/odoo_diancol/custom/addons/dian_efact/data.json', 'w') as outfile:
            #        json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
        response['xml_signed'] = docs.getXMLSignedDocument()
        response['xml_unsigned'] = docs.getXMLUnsignedDocument()
        return response

    def processCertification(self, crtTarget):
        self.sunatAPI.setEndPointType("INVOICE")
        response = self.sunatAPI.doResquestCertificateUpload(crtTarget)
        return response

    def processInvoice(self, data):  
        has_licence = self.validateLicence(data)
        if(has_licence==True):
            has_licence = True
        else:
            return has_licence
        
        response = {}
        try:
            docs = Documents()
            docs.documentXmlName = self.fileXmlName
            docs.documentZipName = self.fileZipName
            docs.xmlClientPath = self.xmlClientPath
            docs.setXMLPath(self.xmlPath)
            docs.fillDocument("invoice", data)     
            config = {
                        'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                        'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                        'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                        'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                        'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                        'key_file_password': data["dian"]["certificado_contrasena"],
                        'filename': docs.documentXmlName+str(".zip")
                     } 
            
            docs.signDocument(config)
            
            if(data['accion']=="fill_submit"):
                wasZipped = docs.zipDocument()
                if (wasZipped==True):
                    zipFileEncoded = docs.Base64EncodeDocument()
                    config ['zipped_file'] = zipFileEncoded                
                    response = self.doRequestDian(config, data)
            
            if(data['accion']=="fill_only"):
                response = {"status":"FAIL","body":"Documentos electrónicos creados pero a la espera de emitir."}
                
        except Exception as e:
            exc_traceback = sys.exc_info() 
            with open('/odoo_rockscripts/custom/addons/dianservice-1.0.35/log.js', 'w') as outfile:
                json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
        #with open('/odoo_rockscripts/custom/addons/dianservice-1.0.35/log.js', 'w') as outfile:
        #        json.dump(str("TEST TEST"), outfile)
        response['xml_signed'] = docs.getXMLSignedDocument()
        response['xml_unsigned'] = docs.getXMLUnsignedDocument()
        return response

    def processCreditNote(self, data): 
        has_licence = self.validateLicence(data)
        if(has_licence==True):
            has_licence = True
        else:
            return has_licence

        response = {}
        try:
            docs = Documents()
            docs.documentXmlName = self.fileXmlName
            docs.documentZipName = self.fileZipName
            docs.setXMLPath(self.xmlPath)
            docs.xmlClientPath = self.xmlClientPath
            docs.fillDocument("creditNote", data)
            config = {
                            'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                            'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                            'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                            'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                            'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                            'key_file_password': data["dian"]["certificado_contrasena"],
                            'filename': docs.documentXmlName+str(".zip")
                        }   
            docs.signDocument(config)
            if(data['accion']=="fill_submit"):
                wasZipped = docs.zipDocument()
                if (wasZipped==True):
                    zipFileEncoded = docs.Base64EncodeDocument()
                    config ['zipped_file'] = zipFileEncoded
                    response = self.doRequestDian(config, data)
            
            if(data['accion']=="fill_only"):
                response = {"status":"FAIL","body":"Documentos electrónicos creados pero a la espera de emitir."}
                    
        except Exception as e:
            exc_traceback = sys.exc_info()

        response['xml_signed'] = docs.getXMLSignedDocument()
        response['xml_unsigned'] = docs.getXMLUnsignedDocument()
        return response

    def processDebitNote(self, data):
        has_licence = self.validateLicence(data)
        if(has_licence==True):
            has_licence = True
        else:
            return has_licence
        
        response = {}
        try:
            docs = Documents()
            docs.documentXmlName = self.fileXmlName
            docs.documentZipName = self.fileZipName
            docs.setXMLPath(self.xmlPath)
            docs.xmlClientPath = self.xmlClientPath
            docs.fillDocument("debitNote", data)
            config =   {
                            'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                            'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                            'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                            'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                            'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                            'key_file_password': data["dian"]["certificado_contrasena"],
                            'filename': docs.documentXmlName+str(".zip")
                        } 
            docs.signDocument(config)
            if(data['accion']=="fill_submit"):
                    wasZipped = docs.zipDocument()
                    if (wasZipped==True):
                        zipFileEncoded = docs.Base64EncodeDocument()
                        config ['zipped_file'] = zipFileEncoded                
                        response = self.doRequestDian(config, data)
                
            if(data['accion']=="fill_only"):
                response = {"status":"FAIL","body":"Documentos electrónicos creados pero a la espera de emitir."}
                
        except Exception as e:
            exc_traceback = sys.exc_info()
               
        response['xml_signed'] = docs.getXMLSignedDocument()
        response['xml_unsigned'] = docs.getXMLUnsignedDocument()
        return response


        
    #def processTicket(self, data): 
    #    has_licence = self.validateLicence(data)
    #    if(has_licence==True):
    #        has_licence = True
    #    else:
    #        return has_licence
#
    #    docs = Documents()
    #    docs.documentXmlName = self.fileXmlName
    #    docs.setXMLPath(self.xmlPath)
    #    docs.fillDocument("ticket", data)    
    #    docs.signDocument(self.xmlPath+"/"+self.xmlClientPath+'/XMLcertificates/rsakey.pem', self.xmlPath+'/XMLcertificates/rsacert.pem')
    #    wasVerified = docs.verifyDocument(self.xmlPath+'/XMLcertificates/rsakey.pem')          
    #    if(wasVerified):
    #        wasZipped = docs.zipDocument(self.xmlPath+'/XMLdocuments/3_signed/',self.xmlPath+'/XMLdocuments/4_compressed/',self.fileZipName)
    #        if (wasZipped==True):
    #                zipFileEncoded = docs.Base64EncodeDocument()
    #                dataSB = {}
    #                dataSB['sendBillFile'] = self.xmlPath+str("/XMLrequests/sendBill.xml")
    #                dataSB['fileName'] = docs.documentXmlName+str(".zip")
    #                dataSB['contentFile'] = zipFileEncoded
    #                dataSB['sol'] = data["sol"]
    #                docs.fillSendBill(dataSB)
    #                self.sunatAPI.setEndPointType("INVOICE")
    #                response = self.sunatAPI.doResquest()    
    #                # collects xml files contentes with or without errors
    #                response['xml_unsigned'] = docs.getXMLUnsignedDocument()
    #                response['xml_signed'] = docs.getXMLSignedDocument()
    #                return response
    #        else:
    #            return "ERROR_DOCUMENT_NOT_ZIPPED"
    #    else:
    #        return "ERROR_DOCUMENT_NOT_VERIFIED"

    #def processDeliveryGuide(self, data): 
    #        has_licence = self.validateLicence(data)
    #        if(has_licence==True):
    #            has_licence = True
    #        else:
    #            return has_licence
#
    #        docs = Documents()
    #        docs.documentXmlName = self.fileXmlName
    #        docs.setXMLPath(self.xmlPath)
    #        docs.fillDocument("deliveryGuide", data)    
    #        docs.signDocument(self.xmlPath+"/"+self.xmlClientPath+'/XMLcertificates/rsakey.pem', self.xmlPath+'/XMLcertificates/rsacert.pem')          
    #        wasVerified = docs.verifyDocument(self.xmlPath+'/XMLcertificates/rsakey.pem')          
    #        if(wasVerified):
    #            wasZipped = docs.zipDocument()            
    #            if (wasZipped==True):
    #                    zipFileEncoded = docs.Base64EncodeDocument()
    #                    dataSB = {}
    #                    dataSB['sendBillFile'] = self.xmlPath+str("/XMLrequests/sendBill.xml")
    #                    dataSB['fileName'] = docs.documentXmlName+str(".zip")
    #                    dataSB['contentFile'] = zipFileEncoded
    #                    dataSB['sol'] = data["sol"]
    #                    docs.fillSendBill(dataSB)
    #                    self.sunatAPI.setEndPointType("GUIDE") 
    #                    response = self.sunatAPI.doResquest()                    
    #                    return response
    #            else:
    #                return "ERROR_DOCUMENT_NOT_ZIPPED"
    #        else:
    #            return "ERROR_DOCUMENT_NOT_VERIFIED"
    
    def initDianAPI(self, mode, call):
        self.fileXmlName = self.fileXmlName
        self.sunatAPI = SunatApi(mode, call, self.xmlPath, self.xmlClientPath, self.fileXmlName, self.fileZipName)
        return self.sunatAPI
    
    def initDianAPI_certificado(self):
        self.sunatAPI = SunatApi("PRODUCTION", "sendBill", "", "", "", "")
        return self.sunatAPI

    def setClientXMLPath(self,clientXMLPath):
        self.xmlClientPath = clientXMLPath
        self.sunatAPI.xmlClientPath = clientXMLPath
    
    def setXMLPath(self,xmlPath):
        self.xmlPath = xmlPath

    def validateLicence(self,data):
        response = {}
        has_licence = False
        for key in self.keys:
            if(str(key).strip("\n")==data['licencia']):
                has_licence = True
        if(has_licence==True):
            return True
        else:
            response["status"] = "FAIL"
            response["code"] = "LCC"
            response["body"] = "La licencia del servicio es invalida"
            return response
    
    def doRequestDian(self,config, data):
        
        responseFormatted = {}
        try:
            if data["ambiente_ejecucion"] == '1':  # Producción
                config['dian_webservice_url'] = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'
            if data["ambiente_ejecucion"] == '2':  # Pruebas
                config['dian_webservice_url'] = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
                
            service = Wsdl(
                            url=config["dian_webservice_url"],
                            template_file=self.getWsdlTemplate(),
                            key_file=config["key_file"],
                            passphrase=data["dian"]["certificado_contrasena"]
                        )

            if data["ambiente_ejecucion"] == '1':  # Producción
                config['dian_webservice_url'] = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'
                response = service.send_bill_sync(
                    zip_name=config['filename'],
                    zip_data=config['zipped_file']
                )

            if data["ambiente_ejecucion"] == '2':  # Pruebas
                config['dian_webservice_url'] = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
                response = service.send_test_set_async(
                                                        zip_name=config['filename'],
                                                        zip_data=config['zipped_file'],
                                                        test_set_id=data['dian']["dian_test_set_id"]
                                                      )
            
            responseFormatted = self.formatDianResponse(response, service, data)
        except Exception as e:
            exc_traceback = sys.exc_info() 
            
        
        return responseFormatted
    
    def getNumberRange(self, ambiente,data):
        docs = Documents()
        docs.xmlClientPath = self.xmlClientPath
        docs.setXMLPath(self.xmlPath)
        config =   {
                            'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                            'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                            'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                            'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                            'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                            'key_file_password': data["dian"]["certificado_contrasena"],
                           
                        } 

        if ambiente == '1':  # Producción
            config['dian_webservice_url'] = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'
        if ambiente == '2':  # Pruebas
            config['dian_webservice_url'] = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
                
        service = Wsdl(
                        url=config["dian_webservice_url"],
                        template_file=self.getWsdlTemplate(),
                        key_file=config["key_file"],
                        passphrase=data["dian"]["certificado_contrasena"]
                    )
        responseRange = service.get_numbering_range(document_id=str(data['dian']['nit']),software_id=str(data['dian']['identificador_software']))
        #responseRange = service.get_xml_by_document_key(str("32432432"))
        self.saveSendBillResponse1(str(responseRange))

    
    def getWsdlTemplate(self):
        xml =       '<?xml version="1.0"?>'
        xml = xml + '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wcf="http://wcf.dian.colombia">'
        xml = xml + '    <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">'
        xml = xml + '        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"'
        xml = xml + '                    xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">'
        xml = xml + '            <wsu:Timestamp>'
        xml = xml + '                <wsu:Created/>'
        xml = xml + '                <wsu:Expires/>'
        xml = xml + '            </wsu:Timestamp>'
        xml = xml + '            <wsse:BinarySecurityToken'
        xml = xml + '                    EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"'
        xml = xml + '                    ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3">'
        xml = xml + '            </wsse:BinarySecurityToken>'
        xml = xml + '        </wsse:Security>'
        xml = xml + '        <wsa:Action/>'
        xml = xml + '        <wsa:To xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"/>'
        xml = xml + '    </soap:Header>'
        xml = xml + '</soap:Envelope>'
        return xml
    
    
    def formatDianResponse(self, response_text,service, data):
        response = {"status":"FAIL","body":"DIAN: Servidor no disponible temporalmente.","track_id":"","is_valid":"false","status_description":"Sin track ID. En espera de emitir."}
        try:
            was_processed = True
            if service.get_response_status_code() == 200:
                self.saveSendBillResponse(response_text)
                EnvelopeNode = self.getSendBillResponseTree()
                for ErrorMessageList in EnvelopeNode.iter(tag='{http://schemas.datacontract.org/2004/07/UploadDocumentResponse}ErrorMessageList'): 
                    if(ErrorMessageList.text!=None): #errors!
                        response["status"] = "FAIL"
                        for ProcessedMessage in ErrorMessageList.iter(tag='{http://schemas.datacontract.org/2004/07/XmlParamsResponseTrackId}ProcessedMessage'): 
                            response["body"] = ProcessedMessage.text
                            was_processed = False

                    else:
                        response["status"] = "OK"
                        response["body"] = "El documento se emitio correctamente."

                errors_on_submit = str("")
                for ErrorMessage in EnvelopeNode.iter(tag='{http://schemas.datacontract.org/2004/07/DianResponse}ErrorMessage'): 
                    if(ErrorMessage.text!=None):
                        for string in EnvelopeNode.iter(tag='{http://schemas.microsoft.com/2003/10/Serialization/Arrays}string'):
                            if(string.text!=None):
                                errors_on_submit = str(errors_on_submit) + str(" \n     - ") + str(string.text)


            
            response["track_id"] = self.getTrackId()

            try:
                time.sleep( 7 )
                self.sunatAPI.rp()
                responseStatus = service.get_status(track_id=response["track_id"]["cufe"])        
                self.saveSendBillResponse(responseStatus)
                EnvelopeNode = self.getSendBillResponseTree()
                for IsValid in EnvelopeNode.iter(tag='{http://schemas.datacontract.org/2004/07/DianResponse}IsValid'): 
                    response["is_valid"] = IsValid.text
                for StatusDescription in EnvelopeNode.iter(tag='{http://schemas.datacontract.org/2004/07/DianResponse}StatusDescription'): 
                    response["status_description"] = StatusDescription.text
            
                if('is_valid' in response):
                    if(str(response["is_valid"])=="false"):
                        response["status"] = "FAIL"
                        response["body"] = str(response["body"]) + str(" \n * Documento no válido:")
                        response["body"] = str(response["body"]) + str(" \n    ") + str(response["status_description"])
                        for ErrorMessage in EnvelopeNode.iter(tag='{http://schemas.datacontract.org/2004/07/DianResponse}ErrorMessage'): 
                            if(ErrorMessage.text!=None):
                                for string in EnvelopeNode.iter(tag='{http://schemas.microsoft.com/2003/10/Serialization/Arrays}string'):
                                    if(string.text!=None):
                                        response["body"] = str(response["body"]) + str(" \n     - ") + str(string.text)
   
   
   
                    if(str(response["is_valid"])=="true"):
                        response["status"] = "OK"
                        response["body"] = str("DIAN: emisión completada") + str(" \n * Documento válido:")
                    else:
                        response["body"] =  str(response["body"]) + errors_on_submit                        
                
            except Exception as e:
                exc_traceback = sys.exc_info()
                #with open('/odoo_diancol/custom/addons/dian_efact/data.json', 'w') as outfile:
                #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)

        except Exception as e:
            exc_traceback = sys.exc_info() 
            #with open('/odoo_diancol/custom/addons/dian_efact/data.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
        
        return response
    
    def getSendBillResponseTree(self):
        xmlTarget = str(self.xmlPath+"/XMLresponses/"+self.xmlClientPath+'/')+str(self.fileXmlName)+".xml"
        mainNode = etree.parse(xmlTarget)
        return mainNode.getroot()

    def saveSendBillResponse(self, xmlResponse):
        xmlTarget = str(self.xmlPath+"/XMLresponses/"+self.xmlClientPath+'/')+str(self.fileXmlName)+".xml"
        with open(xmlTarget, "w") as f:
            f.write(xmlResponse)
        return xmlTarget
    
    def saveSendBillResponse1(self, xmlResponse):
        xmlTarget = str(self.xmlPath+"/XMLresponses/"+self.xmlClientPath+'/reponse')+".xml"
        with open(xmlTarget, "w") as f:
            f.write(xmlResponse)
        return xmlTarget

    def getTrackId(self):
        cufe = str("")
        xmlUnsigned = str(self.xmlPath+"/XMLdocuments/2_unsigned/"+self.xmlClientPath+'/')+str(self.fileXmlName)+".xml"
        tree = etree.parse(xmlUnsigned)
        MainNode = tree.getroot()
        UUID = MainNode.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"+"UUID")
        cufe = UUID.text

        for DianExtensions in MainNode.iter("{dian:gov:co:facturaelectronica:Structures-2-1}"+"DianExtensions"):
            QRCode = DianExtensions.find("{dian:gov:co:facturaelectronica:Structures-2-1}"+"QRCode")
            qr_url = QRCode.text

        trackID = {"cufe":cufe,"qr_url":qr_url}
        return trackID
    
    def getStatus(self,data,cufe):
        docs = Documents()
        docs.documentXmlName = self.fileXmlName
        docs.documentZipName = self.fileZipName
        docs.xmlClientPath = self.xmlClientPath
        docs.setXMLPath(self.xmlPath)
        config =    {
                        'dian_webservice_url':'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                        'policy_id': "https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
                        'policy_name': "Política de firma para facturas electrónicas de la República de Colombia",
                        'policy_remote': docs.Base64EncodeAnyDocument(self.xmlPath+"/politicadefirmav2.pdf"),
                        'key_file': docs.Base64EncodeAnyDocument(self.xmlPath+"/XMLcertificates/"+self.xmlClientPath+"/"+data['dian']['certificado']),
                        'key_file_password': data["dian"]["certificado_contrasena"],
                        'filename': docs.documentXmlName+str(".zip")
                    }  
        service = Wsdl(
                        url=config["dian_webservice_url"],
                        template_file=self.getWsdlTemplate(),
                        key_file=config["key_file"],
                        passphrase=data["dian"]["certificado_contrasena"]
                    )
        
        return service.get_status(track_id=cufe)