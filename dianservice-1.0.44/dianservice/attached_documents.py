from lxml import etree
import json
import sys
from xml.dom import minidom
import hashlib
from datetime import datetime
from datetime import date

class AttachedDocuments:

    def fillDocument(self, XMLpath, xmlClientPath, fileName,  data, data_app_response):

        tree = etree.parse(
            str(XMLpath)+"/XMLdocuments/1_unfilled/UNFILLED-attached-document.xml")
        XMLFileContents = etree.tostring(tree.getroot(
        ), pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")

        treeSignedDocumentAttachment = etree.parse(str(XMLpath)+"/XMLdocuments/3_signed/"+xmlClientPath+"/"+fileName+".xml")
        xml_signedDocument = minidom.parseString(etree.tostring(treeSignedDocumentAttachment.getroot(),pretty_print=True,method="xml")).toprettyxml(indent="   ", newl='', encoding="utf-8")
        xml_signedDocument = str(xml_signedDocument.decode("utf-8"))
        #xml_signedDocument = str(xml_signedDocument).replace("&lt;","<")
        #xml_signedDocument = str(xml_signedDocument).replace("&gt;",">")

        xmlDocStatus = str(str(XMLpath)+"/XMLresponses/"+xmlClientPath+'/')+ str('get_status') + str("_") + str(fileName)+".xml"
        treeAppResponse = etree.parse(xmlDocStatus)
        xml_appResponse = minidom.parseString(etree.tostring(treeAppResponse.getroot(),pretty_print=True,method="xml")).toprettyxml(indent="   ", newl='', encoding="utf-8")
        xml_appResponse = str(xml_appResponse.decode("utf-8"))
        #xml_appResponse = str(xml_appResponse).replace("&lt;","<")
        #xml_appResponse = str(xml_appResponse).replace("&gt;",">")
        
        try:
            # fill xml with data
            data = json.dumps(data, indent=4)
            data = json.loads(data)
            AtacchedDocumentNode = tree.getroot()

            sequence = str(data['numero'])[4:]
            documentID = str(data["dian"]["autorizacion"]["prefijo"])+sequence
            CUFE_parts = self.createCUFE(data)

            

            for InvoiceSource in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"InvoiceSource"):
                IdentificationCode = InvoiceSource.find(
                    self.getNameSpace("cbc")+"IdentificationCode")
                IdentificationCode.text = data["dian"]["autorizacion"]["codigo_pais"]

            for InvoiceControl in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"InvoiceControl"):
                InvoiceAuthorization = InvoiceControl.find(
                    self.getNameSpace("sts")+"InvoiceAuthorization")
                InvoiceAuthorization.text = data["dian"]["autorizacion"]["codigo"]

            for AuthorizationPeriod in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"AuthorizationPeriod"):
                StartDate = AuthorizationPeriod.find(
                    self.getNameSpace("cbc")+"StartDate")
                StartDate.text = data["dian"]["autorizacion"]["fecha_inicio"]
                EndDate = AuthorizationPeriod.find(
                    self.getNameSpace("cbc")+"EndDate")
                EndDate.text = data["dian"]["autorizacion"]["fecha_fin"]

            for AuthorizedInvoices in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"AuthorizedInvoices"):
                Prefix = AuthorizedInvoices.find(
                    self.getNameSpace("sts")+"Prefix")
                Prefix.text = data["dian"]["autorizacion"]["prefijo"]
                From = AuthorizedInvoices.find(
                    self.getNameSpace("sts")+"From")
                From.text = data["dian"]["autorizacion"]["desde"]
                To = AuthorizedInvoices.find(self.getNameSpace("sts")+"To")
                To.text = data["dian"]["autorizacion"]["hasta"]

            for SoftwareProvider in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"SoftwareProvider"):
                ProviderID = SoftwareProvider.find(
                    self.getNameSpace("sts")+"ProviderID")
                ProviderID.text = data["dian"]["nit"]
                ProviderID.set("schemeName", data["emisor"]["tipo_documento"])
                if(int(data["emisor"]["tipo_documento"]) == 31):
                    if(data["dian"]["nit"] == "800197268"):
                        ProviderID.set("schemeID", str("4"))
                    else:
                        ProviderID.set("schemeID", str(data["emisor"]["vat_dv"]))

                SoftwareID = SoftwareProvider.find(
                    self.getNameSpace("sts")+"SoftwareID")
                SoftwareID.text = data["dian"]["identificador_software"]

            for DianExtensions in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"DianExtensions"):
                SoftwareSecurityCode = DianExtensions.find(
                    self.getNameSpace("sts")+"SoftwareSecurityCode")
                SoftwareSecurityCode.text = str(hashlib.sha384(str(str(data["dian"]["identificador_software"]) + str(
                    data["dian"]["pin_software"]) + documentID).encode('utf-8')).hexdigest())

            for DianExtensions in AtacchedDocumentNode.iter(self.getNameSpace("sts")+"DianExtensions"):
                QRCode = DianExtensions.find(
                    self.getNameSpace("sts")+"QRCode")
                if(str(data["ambiente_ejecucion"])=="1"):
                    QRCode.text = str(
                        "https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey="+str(CUFE_parts["sha384"]))
                if(str(data["ambiente_ejecucion"])=="2"):
                    QRCode.text = str(
                        "https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey="+str(CUFE_parts["sha384"]))


            
            # ProfileExecutionID
            ProfileExecutionID = AtacchedDocumentNode.find(
                self.getNameSpace("cbc")+"ProfileExecutionID")
            ProfileExecutionID.text = str(data["ambiente_ejecucion"])            

            # DOCUMENT ID
            AP_DocumentReference = data_app_response['DocumentReference']
            _ID = AP_DocumentReference.find(self.getNameSpace("cbc")+"ID") 
            ID = AtacchedDocumentNode.find(self.getNameSpace("cbc")+"ID")
            ID.text = str(_ID.text)           

            # ISSUE DATE & TIME
            today = date.today()
            now = datetime.now()

            IssueDate = AtacchedDocumentNode.find(
                self.getNameSpace("cbc")+"IssueDate")             
            
            IssueDate.text = today.strftime("%Y-%m-%d")
            
            IssueTime = AtacchedDocumentNode.find(
                self.getNameSpace("cbc")+"IssueTime")
            
            IssueTime.text = str(now.strftime("%H:%M:%S")) + str('-05:00')

            SenderParty = AtacchedDocumentNode.find(self.getNameSpace("cac")+"SenderParty")
            AP_SenderParty = data_app_response['SenderParty']
            SenderParty.append(AP_SenderParty)

            ReceiverParty = AtacchedDocumentNode.find(self.getNameSpace("cac")+"ReceiverParty")
            AP_ReceiverParty = data_app_response['ReceiverParty']
            ReceiverParty.append(AP_ReceiverParty)

            Attachment = AtacchedDocumentNode.find(self.getNameSpace("cac")+"Attachment")
            ExternalReference = etree.Element(self.getNameSpace("cac")+"ExternalReference")
            MimeCode = etree.Element(self.getNameSpace("cbc")+"MimeCode")
            MimeCode.text = str('text/xml')
            ExternalReference.append(MimeCode)
            EncodingCode = etree.Element(self.getNameSpace("cbc")+"EncodingCode")
            EncodingCode.text = str('UTF-8')
            ExternalReference.append(EncodingCode)            
            Description = etree.Element(self.getNameSpace("cbc")+"Description")
            Description.text =  etree.CDATA(str(xml_signedDocument))
            ExternalReference.append(Description)
            Attachment.append(ExternalReference)

            ParentDocumentLineReference = etree.Element(self.getNameSpace("cac")+"ParentDocumentLineReference")

            LineID = etree.Element(self.getNameSpace("cbc")+"LineID")
            LineID.text = str('1')
            ParentDocumentLineReference.append(LineID)

            DocumentReference = etree.Element(self.getNameSpace("cac")+"DocumentReference")

            AP_DocumentReference = data_app_response['DocumentReference']
            _ID = AP_DocumentReference.find(self.getNameSpace("cbc")+"ID")           

            ID = etree.Element(self.getNameSpace("cbc")+"ID")
            ID.text = str(_ID.text)
            DocumentReference.append(ID)

            AP_track_id = data_app_response['track_id']
            UUID = etree.Element(self.getNameSpace("cbc")+"UUID")
            UUID.text = str(AP_track_id['cufe'])
            UUID.set("schemeName", AP_track_id['cufe_scheme'])
            DocumentReference.append(UUID)

            AP_IssueDate = data_app_response['IssueDate']
            IssueDate = etree.Element(self.getNameSpace("cbc")+"IssueDate")
            IssueDate.text = str(AP_IssueDate.text)
            DocumentReference.append(IssueDate)

            DocumentType = etree.Element(self.getNameSpace("cbc")+"DocumentType")
            DocumentType.text = str("ApplicationResponse")
            DocumentReference.append(DocumentType)

            AP_DocumentReference = data_app_response['DocumentReference']
            _ID = AP_DocumentReference.find(self.getNameSpace("cbc")+"ID")  

            ParentDocumentID = etree.Element(self.getNameSpace("cbc")+"ParentDocumentID")
            ParentDocumentID.text = str(_ID.text)
            DocumentReference.append(ParentDocumentID)        

            Attachment = AtacchedDocumentNode.find(self.getNameSpace("cac")+"Attachment")
            ExternalReference = etree.Element(self.getNameSpace("cac")+"ExternalReference")
            MimeCode = etree.Element(self.getNameSpace("cbc")+"MimeCode")
            MimeCode.text = str('text/xml')
            ExternalReference.append(MimeCode)
            EncodingCode = etree.Element(self.getNameSpace("cbc")+"EncodingCode")
            EncodingCode.text = str('UTF-8')
            ExternalReference.append(EncodingCode)            
            Description = etree.Element(self.getNameSpace("cbc")+"Description")
            Description.text = etree.CDATA(str(xml_appResponse))
            ExternalReference.append(Description)
            Attachment.append(ExternalReference)
            
            DocumentReference.append(Attachment)

            AP_Response = data_app_response['Response']
            ResponseCode = AP_Response.find(self.getNameSpace("cbc")+"ResponseCode")
            Description = AP_Response.find(self.getNameSpace("cbc")+"Description")

            ResultOfVerification = etree.Element(self.getNameSpace("cac")+"ResultOfVerification")

            ValidatorID = etree.Element(self.getNameSpace("cbc")+"ValidatorID")
            ValidatorID.text = str(Description.text)
            ResultOfVerification.append(ValidatorID)

            ValidationResultCode = etree.Element(self.getNameSpace("cbc")+"ValidationResultCode")
            ValidationResultCode.text = str(ResponseCode.text)
            ResultOfVerification.append(ValidationResultCode)

            AP_IssueDate = data_app_response['IssueDate']            
            ValidationDate = etree.Element(self.getNameSpace("cbc")+"ValidationDate")
            ValidationDate.text = str(AP_IssueDate.text)
            ResultOfVerification.append(ValidationDate)

            AP_IssueTime = data_app_response['IssueTime']
            ValidationTime = etree.Element(self.getNameSpace("cbc")+"ValidationTime")
            ValidationTime.text = str(AP_IssueTime.text)
            ResultOfVerification.append(ValidationTime)

            DocumentReference.append(ResultOfVerification)
            
            ParentDocumentLineReference.append(DocumentReference)

            AtacchedDocumentNode.append(ParentDocumentLineReference)
            
            

        except Exception as e:
            exc_traceback = sys.exc_info()
            print(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno))
            #with open('/odoo_jc/custom/addons/dian_efact/dianservice/log.js', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
        
        xml_signedDocument = minidom.parseString(etree.tostring(tree.getroot(),pretty_print=True,method="xml")).toprettyxml(indent="   ", newl='', encoding="utf-8")
        tree.write(XMLpath+"/XMLdocuments/2_unsigned/"+xmlClientPath+"/"+fileName+"_attached_document.xml")
        return XMLpath+"/XMLdocuments/2_unsigned/"+xmlClientPath+"/"+fileName+"_attached_document.xml"

    def getGlobalTaxAmount(self, tributos):
        sumatoria = float(0.0)
        for tributo_name in tributos:
            tributo = tributos[str(tributo_name)]
            for item in tributo:
                if(item['codigo'] != "05" and item['codigo'] != "06" and item['codigo'] != "07" and  item['codigo'] != "08"):
                    sumatoria += float(item["sumatoria"])
        return str(sumatoria)

    def getGlobalTaxableAmount(self, items):
        total = 0.0
        for item in items:
            total = float(total) + float(item["subTotalVenta"])
        return str(total)

    def getGlobalTaxInclusiveAmount(self, line_extension, tributos):
        global_tax_amount = self.getGlobalTaxAmount(tributos)
        return float(line_extension) + float(global_tax_amount)

    def getItemsDiscountTotal(self, items):
        total = 0.0
        for item in items:
            descuento_linea = item["descuento"]
            if('monto' in descuento_linea):
                total = float(total) + float(descuento_linea['monto'])
        return total

    def getGlobalLineExtensionAmount(self, items):
        total = 0.0
        for item in items:
            total = float(total) + float(item["subTotalVenta"])
        return total

    def getNameSpace(self, namespace):
        if(namespace == "sac"):
            return "{urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1}"
        if(namespace == "cbc"):
            return "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
        if(namespace == "ext"):
            return "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}"
        if(namespace == "cac"):
            return "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"
        if(namespace == "sts"):
            return "{dian:gov:co:facturaelectronica:Structures-2-1}"

    def priceToLetter(self, numero):
        indicador = [("", ""), ("MIL", "MIL"), ("MILLON", "MILLONES"),
                     ("MIL", "MIL"), ("BILLON", "BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero)*100))
        # print 'decimal : ',decimal
        contador = 0
        numero_letras = ""
        while entero > 0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.priceToLetterInternal(a, 1).strip()
            else:
                en_letras = self.priceToLetterInternal(a, 0).strip()
            if a == 0:
                numero_letras = en_letras+" "+numero_letras
            elif a == 1:
                if contador in (1, 3):
                    numero_letras = indicador[contador][0]+" "+numero_letras
                else:
                    numero_letras = en_letras+" " + \
                        indicador[contador][0]+" "+numero_letras
            else:
                numero_letras = en_letras+" " + \
                    indicador[contador][1]+" "+numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)
        numero_letras = numero_letras
        return numero_letras

    def priceToLetterInternal(self, numero, sw):
        lista_centana = ["", ("CIEN", "CIENTO"), "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
                         "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
        lista_decena = ["", ("DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"),
                        ("VEINTE", "VEINTI"), ("TREINTA",
                                               "TREINTA Y "), ("CUARENTA", "CUARENTA Y "),
                        ("CINCUENTA", "CINCUENTA Y "), ("SESENTA", "SESENTA Y "),
                        ("SETENTA", "SETENTA Y "), ("OCHENTA", "OCHENTA Y "),
                        ("NOVENTA", "NOVENTA Y ")
                        ]
        lista_unidad = ["", ("UN", "UNO"), "DOS", "TRES",
                        "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
        centena = int(numero / 100)
        decena = int((numero - (centena * 100))/10)
        unidad = int(numero - (centena * 100 + decena * 10))
        # print "centena: ",centena, "decena: ",decena,'unidad: ',unidad

        texto_centena = ""
        texto_decena = ""
        texto_unidad = ""

        # Validad las centenas
        texto_centena = lista_centana[centena]
        if centena == 1:
            if (decena + unidad) != 0:
                texto_centena = texto_centena[1]
            else:
                texto_centena = texto_centena[0]

        # Valida las decenas
        texto_decena = lista_decena[decena]
        if decena == 1:
            texto_decena = texto_decena[unidad]
        elif decena > 1:
            if unidad != 0:
                texto_decena = texto_decena[1]
            else:
                texto_decena = texto_decena[0]
        # Validar las unidades
        # print "texto_unidad: ",texto_unidad
        if decena != 1:
            texto_unidad = lista_unidad[unidad]
            if unidad == 1:
                texto_unidad = texto_unidad[sw]

        return "%s %s %s" % (texto_centena, texto_decena, texto_unidad)

    def prettyXMLSave(self, pathFile):
        tree = etree.parse(str(pathFile).strip())
        xmlstr = minidom.parseString(etree.tostring(
            tree.getroot())).toprettyxml(indent="   ")
        with open(pathFile, "w") as f:
            f.write(xmlstr)

    def createCUFE(self, data):
        CUFE_array = []
        sequence = str(data['numero'])[4:]
        NumFac = str(data["dian"]["autorizacion"]["prefijo"])+str(sequence)
        CUFE_array.append({"num_fact": NumFac})

        # str(self.dateCUFE(data["fechaEmision"],str(data["horaEmision"]).replace(str("-05:00"),"")))
        FecFac = str(data["fechaEmision"])
        CUFE_array.append({"fec_fac": FecFac})

        # str(self.dateCUFE(data["fechaEmision"],str(data["horaEmision"]).replace(str("-05:00"),"")))
        HorFac = str(data["horaEmision"])
        CUFE_array.append({"hor_fac": HorFac})

        ValFac = format(data["subTotalVenta"], '.2f')
        CUFE_array.append({"val_fac": ValFac})

        tributes_CUFE = self.tributesCUFE(data)
        tributos_string = tributes_CUFE["string"]
        CUFE_array.append({"tributes_array": tributes_CUFE["array"]})

        ValImp = format(self.get_total_venta_gravada(data["subTotalVenta"],data['tributos'],data['descuentos']), '.2f')
        CUFE_array.append({"val_imp": ValImp})

        NitOFE = str(data["emisor"]["nro"])
        CUFE_array.append({"nit_ofe": NitOFE})

        # TipAdq = str(data["receptor"]["tipo_documento"])
        # CUFE_array.append({"tip_adq":TipAdq})

        NumAdq = str(data["receptor"]["nro"])
        CUFE_array.append({"num_adq": NumAdq})

        ClTec = str(data["dian"]["clave_tecnica"])
        CUFE_array.append({"cl_tec": ClTec})

        TipoAmbiente = str(data["ambiente_ejecucion"])
        CUFE_array.append({"tipo_ambiente": TipoAmbiente})

        CUFE_string = NumFac + FecFac + HorFac + ValFac + \
            tributos_string + ValImp + NitOFE + NumAdq + ClTec + TipoAmbiente
        # $cufeSha384=$numeroFactura.$fechaFactura.$horaFactura.$valorFactura.$codImp.$valImp.$codImp2.$valImp2.$codImp3.$valImp3.$valTotalFactura.$nitFactuardor.$numAdquiriente.$claveTecnica.$tipoAmbiente;
        CUFE_sha384 = hashlib.sha384(
            str(CUFE_string).encode('utf-8')).hexdigest()
        CUFE_parts = {
                      "string": CUFE_string,
                      "sha384": CUFE_sha384, 
                      "array": CUFE_array,
                      "tributes_CUFE":tributes_CUFE,
                     }
        return CUFE_parts

    def dateCUFE(self, IssueDate, IssueTime):
        IssueDate = str(IssueDate).replace("-", "")
        IssueTime = str(IssueTime).replace(":", "")
        return IssueDate + IssueTime

    def tributesCUFE(self, data):
        # Global tax information
        tributes_string = str("")
        tributes_array = []
        tributos = data['tributos']
        for tributo_name in tributos:
            tributo = tributos[str(tributo_name)]
            for tributo_item_percent_differenced in tributo:
                ID = tributo_item_percent_differenced['codigo']
                # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                if(str(ID) != '05' and str(ID) != '06' and str(ID) != '07' and str(ID) != '08' and str(ID) != '22'):
                    TaxAmount = format(
                        tributo_item_percent_differenced['sumatoria'], '.2f')
                    tributes_string = str(tributes_string) + \
                        str(ID) + str(TaxAmount)
                    tributes_array.append({"id": ID, "amount": TaxAmount})
        tributes_result = {"string": tributes_string, "array": tributes_array}
        return tributes_result

    def getCUFE_Note(self, CUFE_array):
            # with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #   json.dump(CUFE_array, outfile)

        cufe_formatted = str("")
        cufe_formatted = str(cufe_formatted) + str("NumFac") + \
            str(" : ") + str(CUFE_array[0]["num_fact"]) + "\n"
        cufe_formatted = str(cufe_formatted) + str("FecFac") + \
            str(" : ") + str(CUFE_array[1]["fec_fac"]) + "\n"
        cufe_formatted = str(cufe_formatted) + str("HorFac") + \
            str(" : ") + str(CUFE_array[2]["hor_fac"]) + "\n"
        ValFac = format(float(CUFE_array[3]["val_fac"]), '.2f')
        cufe_formatted = str(cufe_formatted) + \
            str("ValFac") + str(" : ") + str(ValFac) + "\n"

        tributes_array = CUFE_array[4]["tributes_array"]

        index = 1
        for item in tributes_array:
            cufe_formatted = str(
                cufe_formatted) + str("CodImp"+str(index)) + str(" : ") + str(item["id"]) + "\n"
            ValImpAmount = format(float(item["amount"]), '.2f')
            cufe_formatted = str(cufe_formatted) + str("ValImp" +
                                                       str(index)) + str(" : ") + str(ValImpAmount) + "\n"
            index = index + 1

        val_imp = format(float(CUFE_array[5]["val_imp"]), '.2f')
        cufe_formatted = str(cufe_formatted) + \
            str("ValTotFac") + str(" : ") + str(val_imp) + "\n"
        cufe_formatted = str(cufe_formatted) + str("NitOFE") + \
            str(" : ") + str(CUFE_array[6]["nit_ofe"]) + "\n"

        cufe_formatted = str(cufe_formatted) + str("NumAdq") + \
            str(" : ") + str(CUFE_array[7]["num_adq"]) + "\n"
        cufe_formatted = str(cufe_formatted) + str("ClTec") + \
            str(" : ") + str(CUFE_array[8]["cl_tec"]) + "\n"
        cufe_formatted = str(cufe_formatted) + str("TipAmbiente") + \
            str(" : ") + str(CUFE_array[9]["tipo_ambiente"]) + "\n"
        return cufe_formatted

    def getTributName(self, codigo):
        if(codigo == "01"):
            return "IVA"
        if(codigo == "02"):
            return "IC"
        if(codigo == "03"):
            return "ICA"
        if(codigo == "04"):
            return "INC"
        if(codigo == "05"):
            return "ReteIVA"
        if(codigo == "20"):
            return "FtoHorticultura"
        if(codigo == "21"):
            return "Timbre"
        if(codigo == "22"):
            return "Bolsas"
        if(codigo == "23"):
            return "INCarbono"
        if(codigo == "24"):
            return "INCombustibles"
        if(codigo == "25"):
            return "Sobretasa Combustibles"
        if(codigo == "26"):
            return "Sordicom"
        if(codigo == "ZY"):
            return "No causa"
        if(codigo == "ZZ"):
            return "Nombre de la figura tributaria"

    def get_total_venta_gravada(self, total_venta_gravada,tributos,descuentos):
        total_reteTributes = float(0.0)
        total_mainTributes = float(0.0)

        total_IVA = 0.0
        for tributo_name in tributos:
            tributo = tributos[str(tributo_name)]
            for tributo_item_percent_differenced in tributo:
                if(str(tributo_item_percent_differenced['codigo']) == '01'):
                    total_IVA = float(total_IVA) + float(str(format(tributo_item_percent_differenced['sumatoria'], '.2f')))
                    
        for tributo_name in tributos:
            tributo = tributos[str(tributo_name)]
            for tributo_item_percent_differenced in tributo:
                tax_amount = 0
                if(str(tributo_item_percent_differenced['codigo']) == '05' or str(tributo_item_percent_differenced['codigo']) == '06' or str(tributo_item_percent_differenced['codigo']) == '07' or str(tributo_item_percent_differenced['codigo']) == '08'):
                    total_reteTributes = float(total_reteTributes) + float(str(format(tributo_item_percent_differenced['sumatoria'], '.2f')))                    
                else:
                    total_mainTributes = float(total_mainTributes) + float(str(format(tributo_item_percent_differenced['sumatoria'], '.2f')))
                    #if(str(tributo_item_percent_differenced['codigo']) == '05'):
                    #    tax_amount = float(total_IVA) * (float(tributo_item_percent_differenced['porcentaje'])/100)
                    #    
                    #    tax_amount = float(total_IVA) * (float(tributo_item_percent_differenced['porcentaje'])/100)
                    #    total_mainTributes = float(total_mainTributes) + float(str(format(tax_amount, '.2f')))
                    #else:
                    #    total_mainTributes = float(total_mainTributes) + float(str(format(tributo_item_percent_differenced['sumatoria'], '.2f')))
        #with open('/odoo_12_dev/custom/addons/dian_efact/dianservice/log.js', 'w') as outfile:                            
        #    json.dump(str("--")+str(total_venta_gravada)+str("--")+str(total_mainTributes), outfile)
        return float(total_venta_gravada) + float(total_mainTributes) # float(total_reteTributes)
    
    def get_tributes_with_same_code(self, codigo,tributos, is_global=False):
        array = []
        taxAmount = 0.0
        for tribute in tributos:
            if(str(codigo) == str(tribute['codigo'])):
                array.append(tribute)
                if(is_global):
                    taxAmount = float(taxAmount) + float(tribute['sumatoria'])
                else:
                    taxAmount = float(taxAmount) + float(tribute['montoAfectacionTributo'])
        return {'array':array,'taxAmount':taxAmount}