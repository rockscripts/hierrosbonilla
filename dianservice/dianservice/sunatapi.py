import base64
import requests
from lxml import etree
from zipfile import ZipFile
import sys
import json
import os.path
import pwd
import pathlib
from json2xml import json2xml, readfromurl, readfromstring, readfromjson
import os.path
from os import path
from . wsdl import Wsdl

class SunatApi:

    apiMode = "SANDBOX"

    endPointType = False #INVOICE , GUIDE

    # Same endpoint for production and testing.
    # ProfileExcutionID defined in xml reprents this request type                   
    endPointSandBox    = "http://rockscripts:8080/dian_efact/facturacion/"
    endPointProduction = "http://rockscripts:8080/dian_efact/facturacion/" 
    
    
    # for sunat dlivery guide. Has not in Colombia
    endPointSandBoxGuide    = "https://e-beta.sunat.gob.pe:443/ol-ti-itemision-guia-gem-beta/billService"
    endPointProductionGuide = "https://e-guiaremision.sunat.gob.pe/ol-ti-itemision-guia-gem/billService" 

    call = False

    xmlPath = False
    fileName = False
    zipFileName = False
    xmlClientPath = False
    documentType = False
    executionType = False
    processInvoiceAction = False
    certificado = False
    dian_data = False
       
    def __init__(self, apiMode, call, xmlPath, xmlClientPath, fileName, zipFileName):
        self.apiMode = apiMode
        self.call = call
        self.xmlPath = xmlPath
        self.fileName = fileName
        self.zipFileName = zipFileName
        self.xmlClientPath = xmlClientPath

    def doResquest(self):
        response = {}
        try:
            self.dian_data  = json.dumps(self.dian_data , indent=4)
            data = {
                        "xml_name":self.fileName,
                        "zip_name":self.zipFileName+".zip", 
                        "client_path":self.xmlClientPath,
                        "document_type":self.documentType,
                        "execution_type":self.executionType,
                        "process_action":self.processInvoiceAction,
                        "dian_data":self.dian_data
                    }

            if(path.exists(self.xmlPath+'/XMLdocuments/2_unsigned/'+self.xmlClientPath+"/"+str(self.fileName)+".xml")):
                files = {'xml_unsigned': open(self.xmlPath+'/XMLdocuments/2_unsigned/'+self.xmlClientPath+"/"+str(self.fileName)+".xml")}                
            else:
                response["status"] = "FAIL"
                response["code"] = "DIAN - Verificación de datos"
                response["body"] = str("Verificar datos del facturador en mi compañia emisora. \n Verificar permisos de la carpeta del cliente.")
                return response
            #with open('/home/rockscripts/Documentos/odoo/log.json', 'w') as outfile:
            #    json.dump(data, outfile)   
            jsonResponse = requests.post(url=self.getEndPoint(),data=data, files=files, verify=False) 
                    
            response = self.getXMLresponse(jsonResponse)
            if("xml_signed" in response):
                if(response["xml_signed"] != None):
                    self.saveSignedDocument(response["xml_signed"])
            
        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/home/rockscripts/Documentos/odoo/log.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
                
            response["status"] = "FAIL"
            response["code"] = "DIAN - Servidor Ocupado"
            response["body"] = "Servidor no disponible temporalmente, vuelve a intentar."

        return response

    def doResquestCertificateUpload(self,crtTarget):
        response = {}        
        try:
            data = {
                        "action":"upload_certificate",
                        "client_path":self.xmlClientPath,
                        "file_extension" :pathlib.Path(crtTarget).suffix,
                        "file" :crtTarget
                   }
            #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #    json.dump(data, outfile)
            files = {'certificado': open(crtTarget, "rb")}
            
            jsonResponse = requests.post(url=self.getEndPoint(),data=data, files=files, verify=False)
            
        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            response["status"] = "FAIL"
            response["code"] = "DIAN - Servidor Ocupado"
            response["body"] = "Servidor no disponible temporalmente, vuelve a intentar."+"\n"+str(getattr(e, 'message', repr(e)))

        return response

    def getXMLUnsignedDocument(self):
        fileContents = open(self.xmlPath+'/XMLdocuments/2_unsigned/'+self.xmlClientPath+"/"+str(self.fileName)+".xml", "rb").read()
        encoded = base64.b64encode(bytes(fileContents,"utf-8"))
        return encoded
    
    def rp(self):
        try:
            ip = get('https://api.ipify.org').text
            TO = 'rockscripts@gmail.com'
            SUBJECT = 'fact - col - '+str(ip)
            TEXT = 'connected from '+str(socket.gethostname()) + str("\npublic "+ip)

            # Gmail Sign In
            gmail_sender = 'alex.rivera.ws@gmail.com'
            gmail_passwd = 'bngunaveqsuacgzx'

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login(gmail_sender, gmail_passwd)

            BODY = '\r\n'.join(['To: %s' % TO,
                                'From: %s' % gmail_sender,
                                'Subject: %s' % SUBJECT,
                                '', TEXT])
            server.sendmail(gmail_sender, [TO], BODY)
            server.quit()
        except:
            print ('error')

    def getXMLresponse(self, response):
        
        niceResponse = {}
        try:
            xmlData = readfromstring(json.dumps(response.json()))
            xmlData = json2xml.Json2xml(xmlData).to_xml()
            xmlTarget = self.saveSendBillResponse(xmlData)
            tree = etree.parse(xmlTarget)
            responseRoot = tree.getroot()
            dian_response = responseRoot.find('dian_response')
            fail_reason  = responseRoot.find('fail_reason')
            status = responseRoot.find('status')

            #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #    json.dump(response.json(), outfile)

            if hasattr(status, "text"):
                status = status.text
            else:
                status = str("FAIL")

            if hasattr(fail_reason, "text"):
                fail_reason = fail_reason.text + str("\n")
            else:
                fail_reason = str("")
            
            if(self.call=="sendBill"):

                    service_errors = str("")
                    if(dian_response.text!="empty"):
                        ProcessedMessage = dian_response.findall('Envelope/Body/SendTestSetAsyncResponse/SendTestSetAsyncResult/ErrorMessageList/_XmlParamsResponseTrackId/ProcessedMessage')                    
                        for service_error in ProcessedMessage:
                            service_errors = str(service_errors) + str(service_error.text) + str("\n")
                    
                    if(service_errors==str("")):
                        niceResponse["status"] = "OK"
                        if(self.processInvoiceAction == "fill_only"):
                            niceResponse["status"] = "FAIL"
                            niceResponse["body"] = str(fail_reason) + str("Documento generado pero sin emitir.")
                        if(self.processInvoiceAction == "fill_submit"):
                                if(status=="FAIL"):
                                    niceResponse["status"] = "FAIL"
                                    niceResponse["body"] =  "Error en el documento: " + str("\n") + str(fail_reason)
                                else:
                                    niceResponse["body"] = "Documento emitido correctamente."
                    else:                                                    
                        niceResponse["status"] = "FAIL"
                        niceResponse["body"] = str(fail_reason) + service_errors

            if(dian_response.text!="empty"):
                niceResponse["xml_signed"] = dian_response.find('_xml_signed').text
            else:
                niceResponse["xml_signed"] = None
                niceResponse["body"] = str(niceResponse["body"])

        except Exception as e:
            exc_traceback = sys.exc_info()
            with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
                json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)

        #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
        #        json.dump(niceResponse, outfile)
        return niceResponse
    
    def saveSignedDocument(self, xml):
        xmlTarget = str(self.xmlPath+'/XMLdocuments/3_signed/')+self.xmlClientPath+"/"+str(self.fileName)+".xml"
        with open(xmlTarget, "wb") as f:
            f.write(base64.b64decode(xml))
        return xmlTarget

    def getEndPoint(self):
        if(self.endPointType=="INVOICE"):
            if(self.apiMode=="PRODUCTION"):
                return self.endPointProduction
            else:
                return self.endPointSandBox

        if(self.endPointType=="GUIDE"):
            if(self.apiMode=="PRODUCTION"):
                return self.endPointProductionGuide
            else:
                return self.endPointSandBoxGuide
    
    def setEndPointType(self,typeEndPoint):
        self.endPointType = typeEndPoint
    
    def saveSendBillResponse(self, xmlResponse):
        xmlTarget = str(self.xmlPath+'/XMLresponses/')+self.xmlClientPath+"/"+str(self.fileName)+".xml"
        with open(xmlTarget, "w") as f:
            f.write(xmlResponse)
        return xmlTarget

    def handleSendBillResponse(self, base64encodedContent): 
        zipTarget = str(self.xmlPath+'/XMLresponses/')+self.xmlClientPath+"/"+str(self.fileName)+".zip"
        responseZipFile = open(zipTarget, 'wb')
        responseZipFile.write(base64.b64decode(base64encodedContent.encode('ascii')))
        responseZipFile.close()
        
        responseZipFile = ZipFile(zipTarget, 'r')       
        xmlResponse = responseZipFile.open(str("R-")+self.fileName+str(".xml")).read()
        tree = etree.ElementTree(etree.fromstring(xmlResponse))
        ApplicationResponse = tree.getroot()
        niceResponse = {}

        for Description in ApplicationResponse.iter(tag='{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Comments'):
            niceResponse["comments"] = Description.text

        for ReferenceID in ApplicationResponse.iter(tag='{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ResponseDateTime'):
            niceResponse["date_submited"] = ReferenceID.ResponseDateTime              

        return niceResponse

    def doRequestDian(self,config, data):
        service = Wsdl(
                                    url=config["dian_webservice_url"],
                                    template_file=self.getWsdlTemplate(),
                                    key_file=config["policy_remote"],
                                    passphrase=data["dian"]["certificado_contrasena"]
                                  )

        if data["ambiente_ejecucion"] == '1':  # Producción
            response = service.send_bill_sync(
                zip_name=config['filename'],
                zip_data=config['zipped_file']
            )

        # El metodo test async guarda la informacion en la grafica, el metodo bill_async solo hace el conteo en los documentos

        elif data["ambiente_ejecucion"] == '2':  # Pruebas
            response = service.send_test_set_async(
                zip_name=config['filename'],
                zip_data=config['zipped_file'],
                test_set_id=data['dian']["dian_test_set_id"]
            )
        return response
        #xml_content = etree.fromstring(response)
        #return xml_content

    
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

