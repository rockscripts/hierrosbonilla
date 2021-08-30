import base64
from zipfile import ZipFile
from lxml import etree
import os
#from . certificate import XMLSigner
#from . certificate import XMLVerifier
from . signature import DIANXMLSigner
from . invoices import Invoices
from . tickets import Tickets
from . creditnote import Creditnote
from . debitnote import Debitnote
from . guide import Guide
import hashlib
import json, sys
from random import randint

class Documents:

    xmlPath = False

    documentXmlName = False
    documentZipName = False
    xmlClientPath = False

    def fillDocument(self, whichDocument, data):

        fileFilled = False
        if(whichDocument=="invoice"):
           invoice = Invoices()
           fileFilled = invoice.fillDocument(self.xmlPath, self.xmlClientPath, self.documentXmlName, data)

        if(whichDocument=="ticket"):
           ticket = Tickets()
           fileFilled = ticket.fillDocument(self.xmlPath, self.xmlClientPath,self.documentXmlName, data)
        
        if(whichDocument=="creditNote"):
           creditNote = Creditnote()
           fileFilled = creditNote.fillDocument(self.xmlPath, self.xmlClientPath,self.documentXmlName, data)

        if(whichDocument=="debitNote"):
           debitNote = Debitnote()
           fileFilled = debitNote.fillDocument(self.xmlPath, self.xmlClientPath,self.documentXmlName, data)

        if(whichDocument=="deliveryGuide"):
           deliveryGuide = Guide()
           fileFilled = deliveryGuide.fillDocument(self.xmlPath, self.xmlClientPath,self.documentXmlName, data)

        return fileFilled

    def signDocument(self, config):
        try:
            signed_xml = DIANXMLSigner().sign(self.getXMLUnsignedDocument(), config)  
            signed_path = self.xmlPath+"/XMLdocuments/3_signed/"+self.xmlClientPath+"/"+self.documentXmlName+".xml"         
            self.saveSignedDocument(signed_path, signed_xml)
            #tree = etree.parse(signed_path)
            #signed_xml_formatted = etree.tostring(tree.getroot(), pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes")
            #self.saveSignedDocument(signed_path, signed_xml_formatted)
            return True
        except Exception as e:
            exc_traceback = sys.exc_info() 
            #with open('/odoo_rockscripts/custom/addons/dianservice-1.0.35/log.js', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            return False

    def saveSignedDocument(self, newDocument, XMLcontents):
        f = open(newDocument, "wb")
        f.write(XMLcontents)
        f.close()

    #def verifyDocument(self, key):
    #    verified = XMLVerifier().verify(self.xmlPath+"/XMLdocuments/3_signed/"+self.xmlClientPath+"/"+self.documentXmlName+".xml", key_data=key)
    #    return verified

    def zipDocument(self):
        try:           
            xmlSource = str(self.xmlPath+"/XMLdocuments/3_signed/"+self.xmlClientPath+'/')+str(self.documentXmlName)+str(".xml")
            zipTarget = str(self.xmlPath+"/XMLdocuments/4_compressed/"+self.xmlClientPath+'/')+str(self.documentZipName)+".zip"            
            ZipFile(zipTarget, 'w').write(xmlSource,self.documentXmlName+str(".xml"))
            return True
        except Exception as e:
            exc_traceback = sys.exc_info() 
            #with open('/odoo_diancol/custom/addons/dian_efact/data.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            return False


    def Base64EncodeDocument(self):
        fileContents = open(self.xmlPath+'/XMLdocuments/4_compressed/'+self.xmlClientPath+"/"+str(self.documentZipName)+".zip", "rb").read()
        encoded = base64.b64encode(fileContents)
        return encoded

    def Base64EncodeAnyDocument(self,path):
        fileContents = open(path, "rb").read()
        encoded = base64.b64encode(fileContents)
        return encoded
    
    def getXMLUnsignedDocument(self):
        try:           
            fileContents = open(self.xmlPath+'/XMLdocuments/2_unsigned/'+self.xmlClientPath+"/"+str(self.documentXmlName)+".xml", "rb").read()
            encoded = base64.b64encode(fileContents)
            return encoded
        except Exception as e:
            exc_traceback = sys.exc_info() 
            #with open('/dd/dianservice/data.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            return False
        
        #tree = etree.parse(self.xmlPath+'/XMLdocuments/2_unsigned/'+str(self.documentXmlName)+".xml")
        #XMLFileContents = etree.tostring(tree.getroot(), pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes")        
        #return str(XMLFileContents)

    def getXMLSignedDocument(self):
        fileContents = open(self.xmlPath+'/XMLdocuments/3_signed/'+self.xmlClientPath+"/"+str(self.documentXmlName)+".xml", "rb").read()
        encoded = base64.b64encode(fileContents)
        return encoded

    def setXMLPath(self,xmlPath):
        self.xmlPath = xmlPath
    
    def resetDocumentProcess(self):
        self.documentXmlName = False
        self.xmlPath = False
    
    def fillSendBill(self, data):
        tree = etree.parse(data['sendBillFile'])
        EnvelopeNode = tree.getroot()
        dian = data['dian']

        # for item in EnvelopeNode.iter(self.getSendBillNameSpace("rep")+'NIT'):
        #     item.text = dian['nit']
# 
        # for item in EnvelopeNode.iter(self.getSendBillNameSpace("rep")+'InvoiceNumber'):
        #     item.text = data['InvoiceNumber']
# 
        # for item in EnvelopeNode.iter(self.getSendBillNameSpace("rep")+'IssueDate'):
        #     item.text = dian['created']      
        for item in EnvelopeNode.iter(self.getSendBillNameSpace("wcf")+'fileName'):
            item.text = data['fileName']

        for item in EnvelopeNode.iter(self.getSendBillNameSpace("wcf")+'contentFile'):
            item.text = data['Document']

        #security 
        #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
        #    json.dump(dian, outfile)

        for Username in EnvelopeNode.iter(self.getSendBillNameSpace("wsse")+"Username"):
            Username.text = dian["identificador_software"]

        for Password in EnvelopeNode.iter(self.getSendBillNameSpace("wsse")+"Password"):            
            Password.text = hashlib.new('sha256', str("1112768143").encode('utf-8')).hexdigest()
            # str(hashlib.sha384(str(str(dian["identificador_software"]) + str(dian["pin_software"]) + data['InvoiceNumber']).encode('utf-8')).hexdigest()) 

        for Nonce in EnvelopeNode.iter(self.getSendBillNameSpace("wsse")+"Nonce"):
            Nonce.text = dian["nonce"]

        for Created in EnvelopeNode.iter(self.getSendBillNameSpace("wsu")+"Created"):
            Created.text = dian["created"]

        tree.write(data['sendBillFile'])

    def getSendBillNameSpace(self, namespace):
        if(namespace=="wsse"):
           return "{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}"

        if(namespace=="wsu"):
           return "{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}"

        if(namespace=="rep"):
           return "{http://www.dian.gov.co/servicios/facturaelectronica/ReportarFactura}"

        if(namespace=="soapenv"):
           return "{http://schemas.xmlsoap.org/soap/envelope/}"

        if(namespace=="wcf"):
           return "{http://wcf.dian.colombia}"