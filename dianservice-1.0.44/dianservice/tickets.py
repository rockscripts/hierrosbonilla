from lxml import etree
import json

class Tickets:

    def fillDocument(self, XMLpath, xmlClientPath, fileName,  data):
        
        tree = etree.parse(XMLpath+"/XMLdocuments/1_unfilled/UNFILLED-ticket.xml")
        XMLFileContents = etree.tostring(tree.getroot(), pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes")

        #fill xml with data
        data  = json.dumps(data , indent=4)
        data = json.loads(data)
        InvoiceNode = tree.getroot()
        documentID = str(data["serie"])+"-"+str(data["numero"])
        
        #DOCUMENT ID
        ID = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"ID")
        ID.text = documentID

        #ISSUE DATE & TIME
        IssueDate = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"IssueDate")
        IssueDate.text = data["fechaEmision"]

        IssueTime = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"IssueTime")
        IssueTime.text = data["horaEmision"]

        #DUE DATE
        for PaymentMeans in InvoiceNode.iter(self.getInvoiceNameSpace("cac")+"PaymentMeans"):
            PaymentDueDate = PaymentMeans.find(self.getInvoiceNameSpace("cbc")+"PaymentDueDate")
            PaymentDueDate.text = data["fechaVencimiento"]

        InvoiceTypeCode = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"InvoiceTypeCode")
        InvoiceTypeCode.text = "03"
        InvoiceTypeCode.set("listAgencyName","PE:SUNAT")
        InvoiceTypeCode.set("listName","Tipo de Operacion")
        InvoiceTypeCode.set("listURI","urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01")
        InvoiceTypeCode.set("listID","0101")
        InvoiceTypeCode.set("listSchemeURI","urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo51")

        Note = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"Note")
        Note.text = self.precioALiteral((data["totalVenta"])) # totalVenta in spanish letters
        Note.set("languageLocaleID","1000")

        #DocumentCurrencyCode
        DocumentCurrencyCode = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"DocumentCurrencyCode")
        DocumentCurrencyCode.text = data["tipoMoneda"]
        DocumentCurrencyCode.set("listID","ISO 4217 Alpha")
        DocumentCurrencyCode.set("listName","Currency")
        DocumentCurrencyCode.set("listAgencyName","United Nations Economic Commission for Europe")

        #SIGNATURE
        for Signature in InvoiceNode.iter(self.getInvoiceNameSpace("cac")+"Signature"):
            ID = Signature.find(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = "S"+documentID

            SignatoryParty = Signature.find(self.getInvoiceNameSpace("cac")+"SignatoryParty")
            PartyIdentification = SignatoryParty.find(self.getInvoiceNameSpace("cac")+"PartyIdentification")
            ID = PartyIdentification.find(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = data["emisor"]["nro"] 

            PartyName = SignatoryParty.find(self.getInvoiceNameSpace("cac")+"PartyName")
            Name = PartyName.find(self.getInvoiceNameSpace("cbc")+"Name")
            Name.text = etree.CDATA(data["emisor"]["nombre"])

            DigitalSignatureAttachment = Signature.find(self.getInvoiceNameSpace("cac")+"DigitalSignatureAttachment")
            ExternalReference = DigitalSignatureAttachment.find(self.getInvoiceNameSpace("cac")+"ExternalReference")
            URI = ExternalReference.find(self.getInvoiceNameSpace("cbc")+"URI")
            URI.text = "#S"+documentID
        
        
        #AccountingSupplierParty -> PartyName
        for AccountingSupplierParty in InvoiceNode.findall(self.getInvoiceNameSpace("cac")+"AccountingSupplierParty"):
            Party =  AccountingSupplierParty.find(self.getInvoiceNameSpace("cac")+"Party")
            PartyIdentification = Party.find(self.getInvoiceNameSpace("cac")+"PartyIdentification")
            ID = PartyIdentification.find(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = data["emisor"]["nro"]
            ID.set("schemeID",str(data["emisor"]["tipo"]))

            PartyLegalEntity = Party.find(self.getInvoiceNameSpace("cac")+"PartyLegalEntity")
            RegistrationName = PartyLegalEntity.find(self.getInvoiceNameSpace("cbc")+"RegistrationName")
            RegistrationName.text = etree.CDATA(data["emisor"]["nombre"])

            RegistrationAddress = PartyLegalEntity.find(self.getInvoiceNameSpace("cac")+"RegistrationAddress")
            AddressTypeCode = RegistrationAddress.find(self.getInvoiceNameSpace("cbc")+"AddressTypeCode")
            AddressTypeCode.text = data["emisor"]["ubigeo"]

        
        #AccountingCustomerParty -> PartyName
        for AccountingCustomerParty in InvoiceNode.findall(self.getInvoiceNameSpace("cac")+"AccountingCustomerParty"):
            Party =  AccountingCustomerParty.find(self.getInvoiceNameSpace("cac")+"Party")
            PartyIdentification = Party.find(self.getInvoiceNameSpace("cac")+"PartyIdentification")
            ID = PartyIdentification.find(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = data["receptor"]["nro"]
            ID.set("schemeID",str(data["receptor"]["tipo"]))

            PartyLegalEntity = Party.find(self.getInvoiceNameSpace("cac")+"PartyLegalEntity")
            RegistrationName = PartyLegalEntity.find(self.getInvoiceNameSpace("cbc")+"RegistrationName")
            RegistrationName.text = etree.CDATA(data["receptor"]["nombre"])

        #TAXTOTAL
            TaxTotal = etree.Element(self.getInvoiceNameSpace("cac")+"TaxTotal")
            TaxAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxAmount")
            TaxAmount.text = self.getTaxAmount(data['tributo'])            
            TaxAmount.set("currencyID",data["tipoMoneda"])
            TaxTotal.append(TaxAmount)

            if(float(data['tributo']['IGV']['total_venta'])>0):
                TaxSubtotal = etree.Element(self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                
                #TAXTOTAL FOR IGV VAT
                TaxableAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                TaxableAmount.text = self.getTaxAmount(data['tributo'])
                TaxableAmount.set("currencyID",data["tipoMoneda"])
                TaxSubtotal.append(TaxableAmount)

                TaxAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxAmount")
                TaxAmount.text = str(round(float(data['tributo']['IGV']['total_venta']),2))
                TaxAmount.set("currencyID",data["tipoMoneda"])
                TaxSubtotal.append(TaxAmount)

                TaxCategory = etree.Element(self.getInvoiceNameSpace("cac")+"TaxCategory")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = 'S' #=> IGV
                ID.set("schemeID","UN/ECE 5305")
                ID.set("schemeName","Tax Category Identifier")
                ID.set("schemeAgencyName","United Nations Economic Commission for Europe")
                TaxCategory.append(ID)
                
                TaxScheme = etree.Element(self.getInvoiceNameSpace("cac")+"TaxScheme")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = "1000"
                ID.set("schemeID","UN/ECE 5153")
                ID.set("schemeAgencyID","6")
                TaxScheme.append(ID)
                
                Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                Name.text = "IGV"
                TaxScheme.append(Name)

                TaxTypeCode = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxTypeCode")
                TaxTypeCode.text = "VAT"         
                TaxScheme.append(TaxTypeCode)            

                TaxCategory.append(TaxScheme)
                TaxSubtotal.append(TaxCategory) 
                TaxTotal.append(TaxSubtotal) 

         
         #TAXTOTAL FOR INAFECTO

            if(float(data['tributo']['inafecto']['total_venta'])>0):
                TaxSubtotal = etree.Element(self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                TaxableAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                TaxableAmount.text = str(round(float(data['tributo']['inafecto']['total_venta']),2))
                TaxableAmount.set("currencyID",data["tipoMoneda"])
                TaxSubtotal.append(TaxableAmount)

                TaxAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxAmount")
                TaxAmount.text = str(round(float(data['tributo']['inafecto']['sumatoria']),2))
                TaxAmount.set("currencyID",data["tipoMoneda"])
                TaxSubtotal.append(TaxAmount)

                TaxCategory = etree.Element(self.getInvoiceNameSpace("cac")+"TaxCategory")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = 'O' #=> IGV
                ID.set("schemeID","UN/ECE 5305")
                ID.set("schemeName","Tax Category Identifier")
                ID.set("schemeAgencyName","United Nations Economic Commission for Europe")
                TaxCategory.append(ID)
                
                TaxScheme = etree.Element(self.getInvoiceNameSpace("cac")+"TaxScheme")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = "9998"
                ID.set("schemeID","UN/ECE 5153")
                ID.set("schemeAgencyID","6")
                TaxScheme.append(ID)
                
                Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                Name.text = "INA"
                TaxScheme.append(Name)

                TaxTypeCode = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxTypeCode")
                TaxTypeCode.text = "FRE"         
                TaxScheme.append(TaxTypeCode)            

                TaxCategory.append(TaxScheme)
                TaxSubtotal.append(TaxCategory) 
                TaxTotal.append(TaxSubtotal)          
            
            InvoiceNode.append(TaxTotal)

        LegalMonetaryTotal = etree.Element(self.getInvoiceNameSpace("cac")+"LegalMonetaryTotal")
        PayableAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"PayableAmount")
        PayableAmount.text = str(round(float(data["totalVenta"]),2))
        PayableAmount.set("currencyID",data["tipoMoneda"])
        LegalMonetaryTotal.append(PayableAmount)
        InvoiceNode.append(LegalMonetaryTotal)

        #INVOICE LINES
        index = 0
        #item = data["items"][index]
        items = data["items"]
        for item in items:     
            trubuteDetails = self.getTributeDetails(item["tributo"]["codigo"]) 

            InvoiceLine = etree.Element(self.getInvoiceNameSpace("cac")+"InvoiceLine")
            ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = str(index+1)
            InvoiceLine.append(ID)

            InvoicedQuantity = etree.Element(self.getInvoiceNameSpace("cbc")+"InvoicedQuantity")
            InvoicedQuantity.text = item["cantidad"]
            InvoicedQuantity.set("unitCode",item["unidadMedidaCantidad"])
            InvoicedQuantity.set("unitCodeListID","UN/ECE rec 20")
            InvoicedQuantity.set("unitCodeListAgencyName","United Nations Economic Commission for Europe")
            InvoiceLine.append(InvoicedQuantity)

            LineExtensionAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"LineExtensionAmount")
            LineExtensionAmount.text = str(item["valorVenta"])
            LineExtensionAmount.set("currencyID",data["tipoMoneda"])
            InvoiceLine.append(LineExtensionAmount)
            
            PricingReference = etree.Element(self.getInvoiceNameSpace("cac")+"PricingReference")
            AlternativeConditionPrice = etree.Element(self.getInvoiceNameSpace("cac")+"AlternativeConditionPrice")
            PriceAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"PriceAmount")
            PriceAmount.text = str(round(float(item["precioVentaUnitario"]),2))
            PriceAmount.set("currencyID",data["tipoMoneda"])
            AlternativeConditionPrice.append(PriceAmount)  

            PriceTypeCode = etree.Element(self.getInvoiceNameSpace("cbc")+"PriceTypeCode")
            PriceTypeCode.text = item["tipoPrecioVentaUnitario"]
            PriceTypeCode.set("listName","Tipo de Precio")
            PriceTypeCode.set("listAgencyName","PE:SUNAT")
            PriceTypeCode.set("listURI","urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16")

            AlternativeConditionPrice.append(PriceTypeCode)   
            PricingReference.append(AlternativeConditionPrice)
            InvoiceLine.append(PricingReference)

            TaxTotal = etree.Element(self.getInvoiceNameSpace("cac")+"TaxTotal")
            TaxAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxAmount")
            TaxAmount.text = str(round(float(item["tributo"]["montoAfectacionTributo"]),2))
            TaxAmount.set("currencyID",data["tipoMoneda"])
            TaxTotal.append(TaxAmount)

            TaxSubtotal = etree.Element(self.getInvoiceNameSpace("cac")+"TaxSubtotal")
            TaxableAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxableAmount")
            TaxableAmount.text = str(round(float(item["valorVenta"]),2))
            TaxableAmount.set("currencyID",data["tipoMoneda"])
            TaxSubtotal.append(TaxableAmount)


            TaxAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxAmount")
            TaxAmount.text = str(round(float(item["tributo"]["montoAfectacionTributo"]),2))
            TaxAmount.set("currencyID",data["tipoMoneda"])
            TaxSubtotal.append(TaxAmount)    

            TaxCategory = etree.Element(self.getInvoiceNameSpace("cac")+"TaxCategory")

            ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")            
            ID.text = trubuteDetails['category_code']
            ID.set("schemeID","UN/ECE 5305")
            ID.set("schemeName","Tax Category Identifier")
            ID.set("schemeAgencyName","United Nations Economic Commission for Europe")   
            TaxCategory.append(ID)

            Percent = etree.Element(self.getInvoiceNameSpace("cbc")+"Percent")
            Percent.text = str(round(float(item["tributo"]["porcentaje"]),2))
            TaxCategory.append(Percent)

            #Getting error
            if(item["tributo"]["codigo"]=="2000"):                 
                TaxExemptionReasonCode = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxExemptionReasonCode")
                TaxExemptionReasonCode.text = str("10")
                TaxExemptionReasonCode.set("listAgencyName","PE:SUNAT")
                TaxExemptionReasonCode.set("listName","SUNAT:Codigo de Tipo de Afectacion del IGV")
                TaxExemptionReasonCode.set("listURI","urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07")        
                TaxCategory.append(TaxExemptionReasonCode)

                TierRange = etree.Element(self.getInvoiceNameSpace("cbc")+"TierRange")
                TierRange.text = str("01")
                TaxCategory.append(TierRange)
            else:    
                TaxExemptionReasonCode = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxExemptionReasonCode")
                TaxExemptionReasonCode.text = str(item['tributo']["tipoAfectacionTributo"])
                TaxExemptionReasonCode.set("listAgencyName","PE:SUNAT")
                TaxExemptionReasonCode.set("listName","SUNAT:Codigo de Tipo de Afectacion del IGV")
                TaxExemptionReasonCode.set("listURI","urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07")           
                TaxCategory.append(TaxExemptionReasonCode)
                

            TaxScheme = etree.Element(self.getInvoiceNameSpace("cac")+"TaxScheme")
            ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = item["tributo"]["codigo"]   
            ID.set("schemeID","UN/ECE 5153")
            ID.set("schemeName","Tax Scheme Identifier")
            ID.set("schemeAgencyName","United Nations Economic Commission for Europe")   
            
            TaxScheme.append(ID)

            Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
            Name.text = str(trubuteDetails['name']).strip()
            TaxScheme.append(Name)
            TaxTypeCode = etree.Element(self.getInvoiceNameSpace("cbc")+"TaxTypeCode")
            TaxTypeCode.text = trubuteDetails['name_code']
            TaxScheme.append(TaxTypeCode)
            TaxCategory.append(TaxScheme)
            TaxSubtotal.append(TaxCategory)    
            TaxTotal.append(TaxSubtotal)
            InvoiceLine.append(TaxTotal)

            Item = etree.Element(self.getInvoiceNameSpace("cac")+"Item")
            Description = etree.Element(self.getInvoiceNameSpace("cbc")+"Description")
            Description.text = etree.CDATA(item["descripcion"])
            Item.append(Description)
            SellersItemIdentification =  etree.Element(self.getInvoiceNameSpace("cac")+"SellersItemIdentification")
            ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = item["id"]
            SellersItemIdentification.append(ID)
            Item.append(SellersItemIdentification)
            
            InvoiceLine.append(Item)

            Price = etree.Element(self.getInvoiceNameSpace("cac")+"Price")
            PriceAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"PriceAmount")
            PriceAmount.text = str(item["valorVenta"])
            PriceAmount.set("currencyID",data["tipoMoneda"])
            Price.append(PriceAmount)
            InvoiceLine.append(Price)

            InvoiceNode.append(InvoiceLine)
            index = index+1

        tree.write(XMLpath+"/XMLdocuments/2_unsigned/"+fileName+".xml")
        
        return XMLpath+"/XMLdocuments/2_unsigned/"+fileName+".xml"

    def getInvoiceNameSpace(self, namespace):
        if(namespace=="sac"):
           return "{urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1}"
        if(namespace=="cbc"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
        if(namespace=="ext"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}"
        if(namespace=="cac"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"


    def precioALiteral(self, numero):
        indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero)*100))
        #print 'decimal : ',decimal 
        contador = 0
        numero_letras = ""
        while entero >0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.convierte_cifra(a,1).strip()
            else :
                en_letras = self.convierte_cifra(a,0).strip()
            if a==0:
                numero_letras = en_letras+" "+numero_letras
            elif a==1:
                if contador in (1,3):
                    numero_letras = indicador[contador][0]+" "+numero_letras
                else:
                    numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
            else:
                numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)
        numero_letras = numero_letras+" Y " + str(decimal) +"/100 SOLES"
        return numero_letras
 
    def convierte_cifra(self, numero,sw):
            lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
            lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
                            ("VEINTE","VEINTI"),("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
                            ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
                            ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
                            ("NOVENTA" , "NOVENTA Y ")
                        ]
            lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
            centena = int (numero / 100)
            decena = int((numero -(centena * 100))/10)
            unidad = int(numero - (centena * 100 + decena * 10))
            #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
        
            texto_centena = ""
            texto_decena = ""
            texto_unidad = ""
        
            #Validad las centenas
            texto_centena = lista_centana[centena]
            if centena == 1:
                if (decena + unidad)!=0:
                    texto_centena = texto_centena[1]
                else :
                    texto_centena = texto_centena[0]
        
            #Valida las decenas
            texto_decena = lista_decena[decena]
            if decena == 1 :
                texto_decena = texto_decena[unidad]
            elif decena > 1 :
                if unidad != 0 :
                    texto_decena = texto_decena[1]
                else:
                    texto_decena = texto_decena[0]
            #Validar las unidades
            #print "texto_unidad: ",texto_unidad
            if decena != 1:
                texto_unidad = lista_unidad[unidad]
                if unidad == 1:
                    texto_unidad = texto_unidad[sw]
        
            return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)
    

    def getTributeDetails(self,codigo):
        response = {}
        if(codigo=="1000"):
            response['name'] = "IGV"
            response['name_code'] = "VAT"
            response['category_code'] = "S"
        if(codigo=="2000"):
            response['name'] = "ISC"
            response['name_code'] = "EXC"
            response['category_code'] = "S"
        if(codigo=="9995"):
            response['name'] = "EXPORTACION"
            response['name_code'] = "FRE"
            response['category_code'] = "G"
        if(codigo=="9996"):
            response['name'] = "GRATUITO"
            response['name_code'] = "FRE"
            response['category_code'] = "Z"
        if(codigo=="9997"):
            response['name'] = "EXONERADO"
            response['name_code'] = "VAT"
            response['category_code'] = "E"
        if(codigo=="9998"):
            response['name'] = "INA"
            response['name_code'] = "FRE"
            response['category_code'] = "O"
        if(codigo=="9999"):
            response['name'] = "OTROS CONCEPTOS DE PAGO"
            response['name_code'] = "OTH"
            response['category_code'] = "S"
        return response

    def getTaxAmount(self, tributo):
        taxAmount = float(tributo['IGV']['sumatoria']) + float(tributo['inafecto']['sumatoria']) +float(tributo['exonerado']['sumatoria']) + float(tributo['exportacion']['sumatoria']) + float(tributo['other']['sumatoria'])
        return str(taxAmount)

    def getGlobalTaxableAmountIGV(self, tributo):
        taxAmount = float(tributo['IGV']['total_venta']) + float(tributo['inafecto']['total_venta']) +float(tributo['exonerado']['total_venta']) + float(tributo['exportacion']['total_venta']) + float(tributo['other']['total_venta'])
        return str(taxAmount)