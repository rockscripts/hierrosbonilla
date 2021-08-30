from lxml import etree
import json
import sys
from xml.dom import minidom
import hashlib

class Invoices:

    def fillDocument(self, XMLpath, xmlClientPath, fileName,  data):

        tree = etree.parse(
            str(XMLpath)+"/XMLdocuments/1_unfilled/UNFILLED-invoice.xml")
        XMLFileContents = etree.tostring(tree.getroot(
        ), pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")

        try:
            # fill xml with data
            data = json.dumps(data, indent=4)
            data = json.loads(data)
            InvoiceNode = tree.getroot()

            sequence = str(data['numero'])[4:]
            documentID = str(data["dian"]["autorizacion"]["prefijo"])+sequence
            CUFE_parts = self.createCUFE(data)

            for InvoiceSource in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"InvoiceSource"):
                IdentificationCode = InvoiceSource.find(
                    self.getInvoiceNameSpace("cbc")+"IdentificationCode")
                IdentificationCode.text = data["dian"]["autorizacion"]["codigo_pais"]

            for InvoiceControl in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"InvoiceControl"):
                InvoiceAuthorization = InvoiceControl.find(
                    self.getInvoiceNameSpace("sts")+"InvoiceAuthorization")
                InvoiceAuthorization.text = data["dian"]["autorizacion"]["codigo"]

            for AuthorizationPeriod in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"AuthorizationPeriod"):
                StartDate = AuthorizationPeriod.find(
                    self.getInvoiceNameSpace("cbc")+"StartDate")
                StartDate.text = data["dian"]["autorizacion"]["fecha_inicio"]
                EndDate = AuthorizationPeriod.find(
                    self.getInvoiceNameSpace("cbc")+"EndDate")
                EndDate.text = data["dian"]["autorizacion"]["fecha_fin"]

            for AuthorizedInvoices in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"AuthorizedInvoices"):
                Prefix = AuthorizedInvoices.find(
                    self.getInvoiceNameSpace("sts")+"Prefix")
                Prefix.text = data["dian"]["autorizacion"]["prefijo"]
                From = AuthorizedInvoices.find(
                    self.getInvoiceNameSpace("sts")+"From")
                From.text = data["dian"]["autorizacion"]["desde"]
                To = AuthorizedInvoices.find(self.getInvoiceNameSpace("sts")+"To")
                To.text = data["dian"]["autorizacion"]["hasta"]

            for SoftwareProvider in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"SoftwareProvider"):
                ProviderID = SoftwareProvider.find(
                    self.getInvoiceNameSpace("sts")+"ProviderID")
                ProviderID.text = data["dian"]["nit"]
                ProviderID.set("schemeName", data["emisor"]["tipo_documento"])
                if(int(data["emisor"]["tipo_documento"]) == 31):
                    if(data["dian"]["nit"] == "800197268"):
                        ProviderID.set("schemeID", str("4"))
                    else:
                        ProviderID.set("schemeID", str(data["emisor"]["vat_dv"]))

                SoftwareID = SoftwareProvider.find(
                    self.getInvoiceNameSpace("sts")+"SoftwareID")
                SoftwareID.text = data["dian"]["identificador_software"]

            for DianExtensions in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"DianExtensions"):
                SoftwareSecurityCode = DianExtensions.find(
                    self.getInvoiceNameSpace("sts")+"SoftwareSecurityCode")
                SoftwareSecurityCode.text = str(hashlib.sha384(str(str(data["dian"]["identificador_software"]) + str(
                    data["dian"]["pin_software"]) + documentID).encode('utf-8')).hexdigest())

            for DianExtensions in InvoiceNode.iter(self.getInvoiceNameSpace("sts")+"DianExtensions"):
                QRCode = DianExtensions.find(
                    self.getInvoiceNameSpace("sts")+"QRCode")
                if(str(data["ambiente_ejecucion"])=="1"):
                    QRCode.text = str(
                        "https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey="+str(CUFE_parts["sha384"]))
                if(str(data["ambiente_ejecucion"])=="2"):
                    QRCode.text = str(
                        "https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey="+str(CUFE_parts["sha384"]))


            # 10:standar | 04:exportacion
            # CustomizationID
            docModel = data["tipo_operacion"]
            if(str(data['exportacion']["exportation"]["es_exportacion"]) == "True"):
                docModel = "10"
            CustomizationID = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"CustomizationID")
            CustomizationID.text = docModel

            # ProfileExecutionID
            ProfileExecutionID = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"ProfileExecutionID")
            ProfileExecutionID.text = str(data["ambiente_ejecucion"])
            

            # DOCUMENT ID
            ID = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"ID")
            ID.text = documentID

            # CUFE
            UUID = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"UUID")
            UUID.text = CUFE_parts["sha384"]
            UUID.set('schemeID',str(data["ambiente_ejecucion"]))
            UUID.set('schemeName',str('CUFE-SHA384'))

            # ISSUE DATE & TIME
            IssueDate = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"IssueDate")
            IssueDate.text = data["fechaEmision"]

            IssueTime = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"IssueTime")
            IssueTime.text = data["horaEmision"]

            DueDate = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"DueDate")
            DueDate.text = data["fechaVencimiento"]

            Note = InvoiceNode.find(self.getInvoiceNameSpace("cbc")+"Note")
            note = "\n" + str("Factura: ")+str(" ") + \
                self.priceToLetter((data["totalVentaGravada"])) + "\n"
            note = note + "\n" + "\n" + str("CUFE: ") + "***************\n"
            note = note + self.getCUFE_Note(CUFE_parts["array"]) + "\n"
            note = note + str("CUFE cadena: ") + CUFE_parts["string"] + "\n"
            note = note + str("CUFE sha384: ") + CUFE_parts["sha384"] + "\n"
            Note.text = note

            InvoiceTypeCode = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"InvoiceTypeCode")
            data_exp = data["exportacion"]
            if(str(data_exp["exportation"]["es_exportacion"]) == str("True")):
                InvoiceTypeCode.text = str("02")   # fact exportacion
            else:
                InvoiceTypeCode.text = str("01")  # fact nacional

            # DocumentCurrencyCode
            DocumentCurrencyCode = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"DocumentCurrencyCode")
            DocumentCurrencyCode.text = data["tipoMoneda"]
            DocumentCurrencyCode.set("listID", "ISO 4217 Alpha")
            DocumentCurrencyCode.set("listName", "Currency")
            DocumentCurrencyCode.set(
                "listAgencyName", "United Nations Economic Commission for Europe")

            LineCountNumeric = InvoiceNode.find(
                self.getInvoiceNameSpace("cbc")+"LineCountNumeric")
            LineCountNumeric.text = str(len(data["items"]))

            for AccountingSupplierParty in InvoiceNode.findall(self.getInvoiceNameSpace("cac")+"AccountingSupplierParty"):
                AdditionalAccountID = AccountingSupplierParty.find(
                    self.getInvoiceNameSpace("cbc")+"AdditionalAccountID")
                AdditionalAccountID.text = str(data["emisor"]["tipo_persona"])

                for Party in AccountingSupplierParty.iter(self.getInvoiceNameSpace("cac")+"Party"):
                    IndustryClassificationCode = Party.find(
                            self.getInvoiceNameSpace("cbc")+"IndustryClassificationCode")

                    if(str(data["emisor"]["ciiu"]) != ""):                        
                        IndustryClassificationCode.text = str(
                            data["emisor"]["ciiu"])
                    else:
                        Party.remove(IndustryClassificationCode)

                    for PartyIdentification in Party.iter(self.getInvoiceNameSpace("cac")+"PartyIdentification"):
                        ID = PartyIdentification.find(
                            self.getInvoiceNameSpace("cbc")+"ID")
                        ID.text = data["emisor"]["nro"]
                        ID.set("schemeAgencyID", "195")
                        ID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        ID.set("schemeName", data["emisor"]["tipo_documento"])
                        if(int(data["emisor"]["tipo_documento"]) == 31):
                            ID.set("schemeID", str(data["emisor"]["vat_dv"]))

                    for PartyName in Party.iter(self.getInvoiceNameSpace("cac")+"PartyName"):
                        Name = PartyName.find(
                            self.getInvoiceNameSpace("cbc")+"Name")
                        Name.text = etree.CDATA(data["emisor"]["nombre"])

                    for PhysicalLocation in Party.iter(self.getInvoiceNameSpace("cac")+"PhysicalLocation"):
                        for Address in PhysicalLocation.iter(self.getInvoiceNameSpace("cac")+"Address"):

                            # UPDATE
                            ID = Address.find(self.getInvoiceNameSpace("cbc")+"ID")
                            ID.text = str(data["emisor"]["municipio_code"])

                            CityName = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CityName")
                            CityName.text = data["emisor"]["municipio"]

                            PostalZone = Address.find(
                                self.getInvoiceNameSpace("cbc")+"PostalZone")
                            PostalZone.text = data["emisor"]["codigoPostal"]

                            CountrySubentity = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentity")
                            CountrySubentity.text = etree.CDATA(
                                data["emisor"]["departamento"])

                            CountrySubentityCode = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentityCode")
                            CountrySubentityCode.text = str(data["emisor"]["codigoPostal"])[
                                0:2]  # UPDATE ubigeo 63 quindio

                            for AddressLine in Address.iter(self.getInvoiceNameSpace("cac")+"AddressLine"):
                                Line = AddressLine.find(
                                    self.getInvoiceNameSpace("cbc")+"Line")
                                Line.text = etree.CDATA(
                                    data["emisor"]["direccion"])

                            for Country in Address.iter(self.getInvoiceNameSpace("cac")+"Country"):
                                IdentificationCode = Country.find(
                                    self.getInvoiceNameSpace("cbc")+"IdentificationCode")
                                IdentificationCode.text = data["emisor"]["codigoPais"]
                                Name = Country.find(
                                    self.getInvoiceNameSpace("cbc")+"Name")
                                Name.text = data["emisor"]["nombrePais"]
                                Name.set("languageID", "es")

                    for PartyTaxScheme in Party.iter(self.getInvoiceNameSpace("cac")+"PartyTaxScheme"):
                        RegistrationName = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"RegistrationName")
                        RegistrationName.text = etree.CDATA(
                            data["emisor"]["nombre"])
                        CompanyID = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"CompanyID")
                        CompanyID.text = data["emisor"]["nro"]
                        CompanyID.set("schemeAgencyID", "195")
                        CompanyID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        CompanyID.set(
                            "schemeName", data["emisor"]["tipo_documento"])
                        if(int(data["emisor"]["tipo_documento"]) == 31):
                            CompanyID.set("schemeID", str(
                                data["emisor"]["vat_dv"]))

                        TaxLevelCode = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"TaxLevelCode")
                        TaxLevelCode.text = str(data["emisor"]["responsabilidad"])
                        TaxLevelCode.set("listName", str(
                            data["emisor"]["regimen"]))

                        for RegistrationAddress in PartyTaxScheme.iter(self.getInvoiceNameSpace("cac")+"RegistrationAddress"):
                            ID = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"ID")
                            ID.text =  str(data["emisor"]["municipio_code"])

                            CityName = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CityName")
                            CityName.text =  str(data["emisor"]["municipio"])

                            PostalZone = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"PostalZone")
                            PostalZone.text =  str(data["emisor"]["codigoPostal"])

                            CountrySubentity = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentity")
                            CountrySubentity.text =  str(data["emisor"]["departamento"])

                            CountrySubentityCode = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentityCode")
                            CountrySubentityCode.text =  str(data["emisor"]["codigoPostal"])[0:2]

                            for AddressLine in Party.iter(self.getInvoiceNameSpace("cac")+"AddressLine"):
                                Line = AddressLine.find(
                                self.getInvoiceNameSpace("cbc")+"Line")
                                Line.text =  str(data["emisor"]["direccion"])
                            
                            for Country in RegistrationAddress.iter(self.getInvoiceNameSpace("cac")+"Country"):
                                    IdentificationCode = Country.find(
                                        self.getInvoiceNameSpace("cbc")+"IdentificationCode")
                                    IdentificationCode.text = data["emisor"]["codigoPais"]
                                    Name = Country.find(
                                        self.getInvoiceNameSpace("cbc")+"Name")
                                    Name.text = data["emisor"]["nombrePais"]
                                    Name.set("languageID", "es")

                        for TaxScheme in PartyTaxScheme.iter(self.getInvoiceNameSpace("cac")+"TaxScheme"):
                            ID = TaxScheme.find(self.getInvoiceNameSpace("cbc")+"ID")
                            Name = TaxScheme.find(self.getInvoiceNameSpace("cbc")+"Name")
                            if(int(data["emisor"]["regimen"])==49): # no responsable de iva                               
                                ID.text =  str("ZZ")
                                Name.text = str("No Aplica")
                            if(int(data["emisor"]["regimen"])==48):
                                ID.text =  str("01")
                                Name.text = str("IVA")
                        


                    for PartyLegalEntity in Party.iter(self.getInvoiceNameSpace("cac")+"PartyLegalEntity"):

                        RegistrationName = PartyLegalEntity.find(
                            self.getInvoiceNameSpace("cbc")+"RegistrationName")
                        RegistrationName.text = etree.CDATA(
                            data["emisor"]["nombre"])

                        CompanyID = PartyLegalEntity.find(
                            self.getInvoiceNameSpace("cbc")+"CompanyID")
                        CompanyID.text = data["emisor"]["nro"]
                        CompanyID.set("schemeAgencyID", "195")
                        CompanyID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        CompanyID.set(
                            "schemeName", data["emisor"]["tipo_documento"])
                        if(int(data["emisor"]["tipo_documento"]) == 31):
                            CompanyID.set("schemeID", str(
                                data["emisor"]["vat_dv"]))

                        for CorporateRegistrationScheme in PartyLegalEntity.iter(self.getInvoiceNameSpace("cac")+"CorporateRegistrationScheme"):
                            ID = CorporateRegistrationScheme.find(
                                self.getInvoiceNameSpace("cbc")+"ID")
                            ID.text = str(data["dian"]["autorizacion"]["prefijo"])
                            Name = CorporateRegistrationScheme.find(
                                self.getInvoiceNameSpace("cbc")+"Name")
                            Name.text = str(data["emisor"]["matricula"])

                    for Contact in Party.iter(self.getInvoiceNameSpace("cac")+"Contact"):
                        Telephone = Contact.find(
                            self.getInvoiceNameSpace("cbc")+"Telephone")
                        Telephone.text = data["emisor"]["telefono"]
                        ElectronicMail = Contact.find(
                            self.getInvoiceNameSpace("cbc")+"ElectronicMail")
                        ElectronicMail.text = etree.CDATA(
                            data["emisor"]["correo_electronico"])

            for AccountingCustomerParty in InvoiceNode.findall(self.getInvoiceNameSpace("cac")+"AccountingCustomerParty"):
                AdditionalAccountID = AccountingCustomerParty.find(
                    self.getInvoiceNameSpace("cbc")+"AdditionalAccountID")
                AdditionalAccountID.text = str(data["receptor"]["tipo_persona"])

                for Party in AccountingCustomerParty.iter(self.getInvoiceNameSpace("cac")+"Party"):
                    
                    for PartyIdentification in Party.iter(self.getInvoiceNameSpace("cac")+"PartyIdentification"):
                        ID = PartyIdentification.find(
                            self.getInvoiceNameSpace("cbc")+"ID")
                        ID.text = data["receptor"]["nro"]
                        ID.set("schemeAgencyID", "195")
                        ID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        ID.set("schemeName", data["receptor"]["tipo_documento"])
                        if(int(data["receptor"]["tipo_documento"]) == 31):
                            ID.set("schemeID", str(data["receptor"]["vat_dv"]))

                    for PartyName in Party.iter(self.getInvoiceNameSpace("cac")+"PartyName"):
                        Name = PartyName.find(
                            self.getInvoiceNameSpace("cbc")+"Name")
                        Name.text = etree.CDATA(data["receptor"]["nombre"])

                    for PhysicalLocation in Party.iter(self.getInvoiceNameSpace("cac")+"PhysicalLocation"):
                        for Address in PhysicalLocation.iter(self.getInvoiceNameSpace("cac")+"Address"):
                            # UPDATE
                            ID = Address.find(self.getInvoiceNameSpace("cbc")+"ID")
                            # UPDATE ubigeo 63 quindio 001 armenia - tabla 6.4.3
                            ID.text = str(data["receptor"]["municipio_code"])

                            CityName = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CityName")
                            CityName.text = data["receptor"]["municipio"]

                            PostalZone = Address.find(
                                self.getInvoiceNameSpace("cbc")+"PostalZone")
                            PostalZone.text = str(data["receptor"]["codigoPostal"])

                            CountrySubentity = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentity")
                            CountrySubentity.text = etree.CDATA(
                                data["receptor"]["departamento"])

                            CountrySubentityCode = Address.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentityCode")
                            CountrySubentityCode.text = str(data["receptor"]["codigoPostal"])[
                                0:2]  # UPDATE ubigeo 63 quindio

                            for AddressLine in Address.iter(self.getInvoiceNameSpace("cac")+"AddressLine"):
                                Line = AddressLine.find(
                                    self.getInvoiceNameSpace("cbc")+"Line")
                                Line.text = etree.CDATA(
                                    data["receptor"]["direccion"])

                            for Country in Address.iter(self.getInvoiceNameSpace("cac")+"Country"):
                                IdentificationCode = Country.find(
                                    self.getInvoiceNameSpace("cbc")+"IdentificationCode")
                                IdentificationCode.text = data["receptor"]["codigoPais"]
                                Name = Country.find(
                                    self.getInvoiceNameSpace("cbc")+"Name")
                                Name.text = data["receptor"]["nombrePais"]
                                Name.set("languageID", "es")                                        

                    for PartyTaxScheme in Party.iter(self.getInvoiceNameSpace("cac")+"PartyTaxScheme"):
                        RegistrationName = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"RegistrationName")
                        RegistrationName.text = etree.CDATA(
                            data["receptor"]["nombre"])

                        CompanyID = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"CompanyID")
                        CompanyID.text = data["receptor"]["nro"]
                        CompanyID.set("schemeAgencyID", "195")
                        CompanyID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        CompanyID.set(
                            "schemeName", data["receptor"]["tipo_documento"])
                        if(int(data["receptor"]["tipo_documento"]) == 31):
                            CompanyID.set("schemeID", str(
                                data["receptor"]["vat_dv"]))

                        TaxLevelCode = PartyTaxScheme.find(
                            self.getInvoiceNameSpace("cbc")+"TaxLevelCode")
                        TaxLevelCode.text = str(
                            data["receptor"]["responsabilidad"])
                        TaxLevelCode.set("listName", str(
                            data["receptor"]["regimen"]))
                        
                        for RegistrationAddress in PartyTaxScheme.iter(self.getInvoiceNameSpace("cac")+"RegistrationAddress"):
                            ID = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"ID")
                            ID.text =  str(data["receptor"]["municipio_code"])

                            CityName = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CityName")
                            CityName.text =  str(data["receptor"]["municipio"])

                            PostalZone = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"PostalZone")
                            PostalZone.text =  str(data["receptor"]["codigoPostal"])

                            CountrySubentity = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentity")
                            CountrySubentity.text =  str(data["receptor"]["departamento"])

                            CountrySubentityCode = RegistrationAddress.find(
                                self.getInvoiceNameSpace("cbc")+"CountrySubentityCode")
                            CountrySubentityCode.text =  str(data["receptor"]["codigoPostal"])[0:2]

                            for AddressLine in Party.iter(self.getInvoiceNameSpace("cac")+"AddressLine"):
                                Line = AddressLine.find(
                                self.getInvoiceNameSpace("cbc")+"Line")
                                Line.text =  str(data["receptor"]["direccion"])
                            
                            for Country in RegistrationAddress.iter(self.getInvoiceNameSpace("cac")+"Country"):
                                    IdentificationCode = Country.find(
                                        self.getInvoiceNameSpace("cbc")+"IdentificationCode")
                                    IdentificationCode.text = data["receptor"]["codigoPais"]
                                    Name = Country.find(
                                        self.getInvoiceNameSpace("cbc")+"Name")
                                    Name.text = data["receptor"]["nombrePais"]
                                    Name.set("languageID", "es")

                        for TaxScheme in PartyTaxScheme.iter(self.getInvoiceNameSpace("cac")+"TaxScheme"):
                            ID = TaxScheme.find(self.getInvoiceNameSpace("cbc")+"ID")
                            Name = TaxScheme.find(self.getInvoiceNameSpace("cbc")+"Name")
                            if(int(data["receptor"]["regimen"])==49): # no responsable de iva                               
                                ID.text =  str("ZZ")
                                Name.text = str("No Aplica")
                            if(int(data["receptor"]["regimen"])==48):
                                ID.text =  str("01")
                                Name.text = str("IVA")

                    for PartyLegalEntity in Party.iter(self.getInvoiceNameSpace("cac")+"PartyLegalEntity"):
                        RegistrationName = PartyLegalEntity.find(
                            self.getInvoiceNameSpace("cbc")+"RegistrationName")
                        RegistrationName.text = etree.CDATA(
                            data["receptor"]["nombre"])

                        CompanyID = PartyLegalEntity.find(
                            self.getInvoiceNameSpace("cbc")+"CompanyID")
                        CompanyID.text = data["receptor"]["nro"]
                        CompanyID.set("schemeAgencyID", "195")
                        CompanyID.set(
                            "schemeAgencyName", "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)")
                        CompanyID.set(
                            "schemeName", data["receptor"]["tipo_documento"])
                        if(int(data["receptor"]["tipo_documento"]) == 31):
                            CompanyID.set("schemeID", str(
                                data["receptor"]["vat_dv"]))

                    for Contact in Party.iter(self.getInvoiceNameSpace("cac")+"Contact"):
                        Telephone = Contact.find(
                            self.getInvoiceNameSpace("cbc")+"Telephone")
                        Telephone.text = data["receptor"]["telefono"]
                        ElectronicMail = Contact.find(
                            self.getInvoiceNameSpace("cbc")+"ElectronicMail")
                        ElectronicMail.text = etree.CDATA(
                            data["receptor"]["correo_electronico"])

            for PaymentMeans in InvoiceNode.findall(self.getInvoiceNameSpace("cac")+"PaymentMeans"):
                ID = PaymentMeans.find(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = str(data['pagos']["dian_payment_means_id"])  # 1:contado 2:credito
                PaymentMeansCode = PaymentMeans.find(
                    self.getInvoiceNameSpace("cbc")+"PaymentMeansCode")
                
                PaymentDueDate = PaymentMeans.find(
                        self.getInvoiceNameSpace("cbc")+"PaymentDueDate")
                PaymentDueDate.text = str(data['pagos']["payment_due_date"])
                
                # efectivo, transferencia, giro...
                PaymentMeansCode.text = str(data['pagos']["payment_means_code"])
                if(str(data['pagos']["payment_id"]) != ""):
                    PaymentID = PaymentMeans.find(
                        self.getInvoiceNameSpace("cbc")+"PaymentID")
                    PaymentID.text = str(data['pagos']["payment_id"])

            # descuentos
            descuentos_globales = data["descuentos"]["globales"]
            descuento_global_index = 1
            total_descuento_global = float(0.0)
            for descuento_global in descuentos_globales:
                AllowanceCharge = etree.Element(
                    self.getInvoiceNameSpace("cac")+"AllowanceCharge")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = str(descuento_global_index)
                AllowanceCharge.append(ID)
                ChargeIndicator = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"ChargeIndicator")
                ChargeIndicator.text = str('false')
                AllowanceCharge.append(ChargeIndicator)
                AllowanceChargeCode = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"AllowanceChargeCode")
                AllowanceChargeCode.text = str(descuento_global['codigo'])
                AllowanceCharge.append(AllowanceChargeCode)
                AllowanceChargeReason = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"AllowanceChargeReason")
                AllowanceChargeReason.text = str(descuento_global['razon'])
                AllowanceCharge.append(AllowanceChargeReason)
                MultiplierFactorNumeric = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"MultiplierFactorNumeric")
                MultiplierFactorNumeric.text = str(
                    int(descuento_global['porcentaje']))
                AllowanceCharge.append(MultiplierFactorNumeric)
                Amount = etree.Element(self.getInvoiceNameSpace("cbc")+"Amount")
                Amount.text = str(abs(descuento_global['monto']))
                Amount.set("currencyID", data["tipoMoneda"])
                AllowanceCharge.append(Amount)
                BaseAmount = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"BaseAmount")
                BaseAmount.text = format(float(data["subTotalVenta"]), '.2f')
                BaseAmount.set("currencyID", data["tipoMoneda"])
                AllowanceCharge.append(BaseAmount)
                InvoiceNode.append(AllowanceCharge)
                total_descuento_global = float(
                    total_descuento_global) + float(abs(descuento_global['monto']))
                descuento_global_index = descuento_global_index + 1

            data_exp = data["exportacion"]
            if(str(data_exp["exportation"]["es_exportacion"]) == str("True")):
                PaymentExchangeRate = etree.Element(
                    self.getInvoiceNameSpace("cac")+"PaymentExchangeRate")

                SourceCurrencyCode = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"SourceCurrencyCode")
                SourceCurrencyCode.text = str(
                    data_exp["exportation"]["divisa_origen"])
                PaymentExchangeRate.append(SourceCurrencyCode)

                SourceCurrencyBaseRate = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"SourceCurrencyBaseRate")
                SourceCurrencyBaseRate.text = str(
                    data_exp["exportation"]["divisa_origen_rate"])
                PaymentExchangeRate.append(SourceCurrencyBaseRate)

                TargetCurrencyCode = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"TargetCurrencyCode")
                TargetCurrencyCode.text = str(
                    data_exp["exportation"]["divisa_destino"])
                PaymentExchangeRate.append(TargetCurrencyCode)

                TargetCurrencyBaseRate = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"TargetCurrencyBaseRate")
                TargetCurrencyBaseRate.text = str(
                    data_exp["exportation"]["divisa_destino_rate"])
                PaymentExchangeRate.append(TargetCurrencyBaseRate)

                CalculationRate = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"CalculationRate")
                CalculationRate.text = str(
                    format(float(data_exp["exportation"]["calculo_rate"]), '.5f'))
                PaymentExchangeRate.append(CalculationRate)

                Date = etree.Element(self.getInvoiceNameSpace("cbc")+"Date")
                Date.text = str(data["fechaEmision"])
                PaymentExchangeRate.append(Date)

                InvoiceNode.append(PaymentExchangeRate)

            # Global tax information
            total_cargo_iva = 0.0
            tributos = data['tributos']
            tag_tax_total_added = False
            for tributo_name in tributos:
                tributo = tributos[str(tributo_name)]
                tag_tax_total_added = False
                totalSubtaxes = self.get_global_tax_amount(str(tributo_name), tributos)
                for tributo_item_percent_differenced in tributo:

                    if(float(tributo_item_percent_differenced['total_venta']) == 0):
                        pass
                    else:
                        if(str(tributo_item_percent_differenced['codigo']) == '01'):
                            total_cargo_iva = float(tributo_item_percent_differenced['sumatoria'])

                        # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                        if(str(tributo_item_percent_differenced['codigo']) != '05' and str(tributo_item_percent_differenced['codigo']) != '06' and str(tributo_item_percent_differenced['codigo']) != '07' and str(tributo_item_percent_differenced['codigo']) != '08'):
                            
                            if(tag_tax_total_added==False):
                                TaxTotal = etree.Element(
                                    self.getInvoiceNameSpace("cac")+"TaxTotal")
                                TaxAmount = etree.Element(
                                    self.getInvoiceNameSpace("cbc")+"TaxAmount")
                                TaxAmount.text = str(
                                    format(totalSubtaxes, '.2f'))
                                TaxAmount.set("currencyID", data["tipoMoneda"])
                                TaxTotal.append(TaxAmount)

                                TaxEvidenceIndicator = etree.Element(
                                    self.getInvoiceNameSpace("cbc")+"TaxEvidenceIndicator")
                                TaxEvidenceIndicator.text = str("false")
                                TaxTotal.append(TaxEvidenceIndicator)

                            TaxSubtotal = etree.Element(
                                self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                            TaxableAmount = etree.Element(
                                self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                            TaxableAmount.text = str(
                                format(tributo_item_percent_differenced['total_venta'], '.2f'))
                            TaxableAmount.set("currencyID", data["tipoMoneda"])
                            TaxSubtotal.append(TaxableAmount)

                            TaxAmount = etree.Element(
                                self.getInvoiceNameSpace("cbc")+"TaxAmount")
                            TaxAmount.text = str(
                                format(tributo_item_percent_differenced['sumatoria'], '.2f'))
                            TaxAmount.set("currencyID", data["tipoMoneda"])
                            TaxSubtotal.append(TaxAmount)

                            TaxCategory = etree.Element(
                                self.getInvoiceNameSpace("cac")+"TaxCategory")
                            
                            if(str(tributo_item_percent_differenced['codigo'])!="22"):
                                Percent = etree.Element(
                                    self.getInvoiceNameSpace("cbc")+"Percent")
                                Percent.text = str(format(float(tributo_item_percent_differenced['porcentaje']), '.2f'))
                                TaxCategory.append(Percent)
                                
                            TaxScheme = etree.Element(
                                self.getInvoiceNameSpace("cac")+"TaxScheme")
                            ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                            ID.text = tributo_item_percent_differenced['codigo']
                            TaxScheme.append(ID)
                            Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                            Name.text = self.getTributName(tributo_item_percent_differenced['codigo'])
                            TaxScheme.append(Name)
                            TaxCategory.append(TaxScheme)
                            TaxSubtotal.append(TaxCategory)
                            TaxTotal.append(TaxSubtotal)

                            if(tag_tax_total_added==False):
                                InvoiceNode.append(TaxTotal)
                                tag_tax_total_added=True

            # Global tax information for RETENEDORES DE IMPUESTOS
            total_reteTributes = float(0.0)
            total_rete_IVA = float(0.0)
            tributos = data['tributos']
            main_tags_added = False
            current_code = False
            for tributo_name in tributos:
                tributo = tributos[str(tributo_name)]
                for tributo_item_percent_differenced in tributo:
                    # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                    if(str(tributo_item_percent_differenced['codigo']) == '05' or str(tributo_item_percent_differenced['codigo']) == '06' or str(tributo_item_percent_differenced['codigo']) == '07' or str(tributo_item_percent_differenced['codigo']) == '08'):

                        tributes_array = self.get_tributes_with_same_code(str(tributo_item_percent_differenced['codigo']),tributo,True)
                        if(current_code != str(tributo_item_percent_differenced['codigo'])):
                            main_tags_added = False
                        current_code = str(tributo_item_percent_differenced['codigo'])
                        if(not main_tags_added):
                            WithholdingTaxTotal = etree.Element(
                                self.getInvoiceNameSpace("cac")+"WithholdingTaxTotal")
                            TaxAmount = etree.Element(
                                self.getInvoiceNameSpace("cbc")+"TaxAmount")
                            
                            tax_amount = 0.0
                            if(str(tributo_item_percent_differenced['codigo']) == '05'):
                                tax_amount = float(total_cargo_iva) * (float(tributo_item_percent_differenced['porcentaje'])/100)
                                TaxAmount.text = format(float(tax_amount), '.2f')  
                                total_rete_IVA = tax_amount
                            else:
                                tax_amount = float(tributes_array['taxAmount'])
                                TaxAmount.text = format(float(tax_amount), '.2f') 

                            TaxAmount.set("currencyID", data["tipoMoneda"])
                            WithholdingTaxTotal.append(TaxAmount)                                                    

                        TaxSubtotal = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                        TaxableAmount = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                        
                        if(str(tributo_item_percent_differenced['codigo']) == '05'):
                            TaxableAmount.text = format(
                                float(total_cargo_iva), '.2f')                         
                        else:                            
                            TaxableAmount.text = format(
                                float(tributo_item_percent_differenced['total_venta']), '.2f')

                        TaxableAmount.set("currencyID", data["tipoMoneda"])
                        TaxSubtotal.append(TaxableAmount)

                        TaxAmount = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxAmount")
                    
                        tax_amount = 0.0
                        if(str(tributo_item_percent_differenced['codigo']) == '05'):
                            tax_amount = float(total_cargo_iva) * (float(tributo_item_percent_differenced['porcentaje'])/100)
                            TaxAmount.text = format(float(tax_amount), '.2f')  
                            total_rete_IVA = tax_amount
                        else:
                            tax_amount = float(tributo_item_percent_differenced['sumatoria'])
                            TaxAmount.text = format(float(tributo_item_percent_differenced['sumatoria']), '.2f') 

                        TaxAmount.set("currencyID", data["tipoMoneda"])
                        TaxSubtotal.append(TaxAmount)
                        

                        TaxCategory = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxCategory")
                        Percent = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"Percent")
                        Percent.text = str(format(float(tributo_item_percent_differenced['porcentaje']), '.2f'))
                        TaxCategory.append(Percent)
                        TaxScheme = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxScheme")
                        ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                        ID.text = tributo_item_percent_differenced['codigo']
                        TaxScheme.append(ID)
                        Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                        Name.text = self.getTributName(tributo_item_percent_differenced['codigo'])
                        TaxScheme.append(Name)                     
                        TaxCategory.append(TaxScheme)

                        TaxSubtotal.append(TaxCategory)
                        WithholdingTaxTotal.append(TaxSubtotal)

                        if(not main_tags_added):
                            InvoiceNode.append(WithholdingTaxTotal)
                            main_tags_added = True

                        if(str(tributo_item_percent_differenced['codigo']) == '06' or str(tributo_item_percent_differenced['codigo']) == '07' or str(tributo_item_percent_differenced['codigo']) == '08'):
                            total_reteTributes = float(total_reteTributes) + float(str(format(tributo_item_percent_differenced['sumatoria'], '.2f')))               
#
            LegalMonetaryTotal = etree.Element(
                self.getInvoiceNameSpace("cac")+"LegalMonetaryTotal")

            # Valor bruto antes de tributos: Total valor bruto, suma de los valores brutos de las líneas de la factura.
            # sum LineExtensionAmount items
            LineExtensionAmount = etree.Element(
                self.getInvoiceNameSpace("cbc")+"LineExtensionAmount")
            lineExtensionAmount = float(
                self.getGlobalLineExtensionAmount(data["items"]))
            LineExtensionAmount.text = format(lineExtensionAmount, '.2f')
            LineExtensionAmount.set("currencyID", data["tipoMoneda"])
            LegalMonetaryTotal.append(LineExtensionAmount)

            # Total Valor Base Imponible : Base imponible para el cálculo de los tributo
            # <!-- <cac:TaxTotal> <cac:TaxSubtotal><cbc:TaxableAmount  SUMATORIA GLOBAL-->
            TaxExclusiveAmount = etree.Element(
                self.getInvoiceNameSpace("cbc")+"TaxExclusiveAmount")
            TaxExclusiveAmount.text = format(
                float(self.getGlobalTaxableAmount(data['items'])), '.2f')
            TaxExclusiveAmount.set("currencyID", data["tipoMoneda"])
            LegalMonetaryTotal.append(TaxExclusiveAmount)

            # Total de Valor bruto con tributos. Los tributos retenidos son retirados en el cálculo de PayableAmount
            # <!--cbc:LineExtensionAmount + sum all (<cac:TaxTotal> <cbc:TaxAmount )-->
            TaxInclusiveAmount = etree.Element(
                self.getInvoiceNameSpace("cbc")+"TaxInclusiveAmount")
           
            TaxInclusiveAmount.text = format(self.get_total_venta_gravada(data["subTotalVenta"],data['tributos'],data['descuentos']), '.2f')
            TaxInclusiveAmount.set("currencyID", data["tipoMoneda"])
            LegalMonetaryTotal.append(TaxInclusiveAmount)

            if(total_descuento_global>0):
                AllowanceTotalAmount = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"AllowanceTotalAmount")
                AllowanceTotalAmount.text = format(float(
                    total_descuento_global) + float(total_descuento_global), '.2f')
                AllowanceTotalAmount.set("currencyID", data["tipoMoneda"])
                LegalMonetaryTotal.append(AllowanceTotalAmount)

            # Valor a Pagar de Factura: Valor total de
            # ítems (incluyendo cargos y descuentos a
            # nivel de ítems)+valor tributos + valor
            # cargos – valor descuentos – valor anticipos
            PayableAmount = etree.Element(
                self.getInvoiceNameSpace("cbc")+"PayableAmount")

            payableAmount = float(0.0)
            if(float(total_rete_IVA) > 0):
                payableAmount = format( float(float(self.getGlobalTaxInclusiveAmount(str(lineExtensionAmount), tributos)) - float(total_descuento_global)), '.2f') 
            else:
                payableAmount = format(float(data["totalVentaGravada"]) - float(total_descuento_global), '.2f')
            
            payableAmount = format(float(self.get_total_venta_gravada(data["subTotalVenta"],data['tributos'],data['descuentos'])), '.2f')
            
            if(float(payableAmount)>0):
                PayableAmount.text = format(float(payableAmount), '.2f')
                PayableAmount.set("currencyID", data["tipoMoneda"])
                LegalMonetaryTotal.append(PayableAmount)

            InvoiceNode.append(LegalMonetaryTotal)

            # INVOICE LINES
            index = 0
            items = data["items"]
            for item in items:
                descuento_linea = item["descuento"]

                InvoiceLine = etree.Element(
                    self.getInvoiceNameSpace("cac")+"InvoiceLine")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.text = str(index+1)
                InvoiceLine.append(ID)

                InvoicedQuantity = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"InvoicedQuantity")
                InvoicedQuantity.text = item["cantidad"]
                InvoicedQuantity.set("unitCode", item["unidadMedida"])
                InvoiceLine.append(InvoicedQuantity)

                LineExtensionAmount = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"LineExtensionAmount")
                LineExtensionAmount.text = format(
                    item["subTotalVenta"], '.2f')  # viene con descuento aplicao
                LineExtensionAmount.set("currencyID", data["tipoMoneda"])
                InvoiceLine.append(LineExtensionAmount)

                # descuentos
                if('codigo' in descuento_linea):
                    AllowanceCharge = etree.Element(
                        self.getInvoiceNameSpace("cac")+"AllowanceCharge")
                    ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                    ID.text = str(1)
                    AllowanceCharge.append(ID)
                    ChargeIndicator = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"ChargeIndicator")
                    ChargeIndicator.text = str('false')
                    AllowanceCharge.append(ChargeIndicator)
                    AllowanceChargeCode = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"AllowanceChargeCode")
                    AllowanceChargeCode.text = str(descuento_linea['codigo'])
                    #AllowanceCharge.append(AllowanceChargeCode)
                    AllowanceChargeReason = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"AllowanceChargeReason")
                    AllowanceChargeReason.text = str(descuento_linea['razon'])
                    AllowanceCharge.append(AllowanceChargeReason)
                    MultiplierFactorNumeric = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"MultiplierFactorNumeric")
                    MultiplierFactorNumeric.text = str(
                        int(descuento_linea['porcentaje']))
                    AllowanceCharge.append(MultiplierFactorNumeric)
                    Amount = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"Amount")
                    Amount.text = format(float(descuento_linea['monto']), '.2f')
                    Amount.set("currencyID", data["tipoMoneda"])
                    AllowanceCharge.append(Amount)
                    BaseAmount = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"BaseAmount")
                    if('monto' in descuento_linea):
                        BaseAmount.text = format(
                            float(item["subTotalVenta"]) + float(descuento_linea['monto']), '.2f')
                    else:
                        BaseAmount.text = format(
                            float(item["subTotalVenta"]), '.2f')
                    BaseAmount.set("currencyID", data["tipoMoneda"])
                    AllowanceCharge.append(BaseAmount)
                    InvoiceLine.append(AllowanceCharge)

                total_cargo_iva = 0.0
                tributos = item['tributos']
                for tributo in tributos:
                    # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                    if(str(tributo['codigo']) != '05' and str(tributo['codigo']) != '06' and str(tributo['codigo']) != '07' and str(tributo['codigo']) != '08'):

                        if(str(tributo['codigo']) == '01'):
                            total_cargo_iva = total_cargo_iva + float(tributo['montoAfectacionTributo'])

                        TaxTotal = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxTotal")
                        TaxAmount = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxAmount")
                        TaxAmount.text = format(
                            float(tributo['montoAfectacionTributo']), '.2f')
                        TaxAmount.set("currencyID", data["tipoMoneda"])
                        TaxTotal.append(TaxAmount)

                        TaxEvidenceIndicator = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxEvidenceIndicator")
                        TaxEvidenceIndicator.text = str("false")
                        TaxTotal.append(TaxEvidenceIndicator)

                        TaxSubtotal = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                        TaxableAmount = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                        TaxableAmount.text = format(
                            float(item["subTotalVenta"]), '.2f')
                        TaxableAmount.set("currencyID", data["tipoMoneda"])
                        TaxSubtotal.append(TaxableAmount)

                        TaxAmount = etree.Element(
                            self.getInvoiceNameSpace("cbc")+"TaxAmount")
                        TaxAmount.text = format(
                            float(tributo['montoAfectacionTributo']), '.2f')
                        TaxAmount.set("currencyID", data["tipoMoneda"])
                        TaxSubtotal.append(TaxAmount)

                        if(str(tributo['codigo'])=="22"):
                            BaseUnitMeasure = etree.Element(self.getInvoiceNameSpace("cbc")+"BaseUnitMeasure")
                            BaseUnitMeasure.text = format(float(item["cantidad"]),".0f") 
                            BaseUnitMeasure.set("unitCode",str('NIU'))
                            TaxSubtotal.append(BaseUnitMeasure)
                            PerUnitAmount = etree.Element(self.getInvoiceNameSpace("cbc")+"PerUnitAmount")
                            PerUnitAmount.text =   format(float(tributo['porcentaje']),'.2f')
                            PerUnitAmount.set("currencyID",data["tipoMoneda"])
                            TaxSubtotal.append(PerUnitAmount)

                        TaxCategory = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxCategory")                                                

                        if(str(tributo['codigo'])!="22"):
                            Percent = etree.Element(
                                self.getInvoiceNameSpace("cbc")+"Percent")
                            Percent.text = str(format(float(tributo['porcentaje']), '.2f'))
                            TaxCategory.append(Percent)

                        TaxScheme = etree.Element(
                            self.getInvoiceNameSpace("cac")+"TaxScheme")
                        ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                        ID.text = tributo['codigo']
                        TaxScheme.append(ID)
                        Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                        Name.text = self.getTributName(tributo['codigo'])
                        TaxScheme.append(Name)                    
                        TaxCategory.append(TaxScheme)

                        TaxSubtotal.append(TaxCategory)
                        TaxTotal.append(TaxSubtotal)
                        InvoiceLine.append(TaxTotal)
                
                tributos = item['tributos']
                tributes_added = []
                for tributo in tributos:
                    # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                    if(str(tributo['codigo']) == '05' or str(tributo['codigo']) == '06' or str(tributo['codigo']) == '07' or str(tributo['codigo']) == '08'):

                        alredy_added = False
                        if(str(tributo['codigo']) in tributes_added):
                            alredy_added = True

                        if(not alredy_added):
                            tributes_added.append(str(tributo['codigo']))

                            same_tributes = self.get_tributes_with_same_code(str(tributo['codigo']),tributos)                            
                            
                            WithholdingTaxTotal = etree.Element(
                                self.getInvoiceNameSpace("cac")+"WithholdingTaxTotal")
                            TaxAmount = etree.Element(
                                self.getInvoiceNameSpace("cbc")+"TaxAmount")

                            tax_amount = 0.0
                            if(str(tributo['codigo']) == '05'):
                                tax_amount = float(total_cargo_iva) * (float(tributo['porcentaje'])/100)
                                TaxAmount.text = format(float(tax_amount), '.2f')  
                            else:
                                tax_amount = float(same_tributes['taxAmount'])
                                TaxAmount.text = format(float(tax_amount), '.2f')                            
                            
                            TaxAmount.set("currencyID", data["tipoMoneda"])
                            WithholdingTaxTotal.append(TaxAmount)
                            
                            if(len(same_tributes['array'])>0):
                                for item_array in same_tributes['array']:
                                    TaxSubtotal = etree.Element(
                                        self.getInvoiceNameSpace("cac")+"TaxSubtotal")
                                    TaxableAmount = etree.Element(
                                        self.getInvoiceNameSpace("cbc")+"TaxableAmount")
                                    
                                    if(str(tributo['codigo']) == '05'):
                                        TaxableAmount.text = format(
                                            float(total_cargo_iva), '.2f')       
                                        #TaxableAmount.text = format(
                                        #    float(item["subTotalVenta"]), '.2f')                     
                                    else:                            
                                        TaxableAmount.text = format(
                                            float(item["subTotalVenta"]), '.2f')
                                            
                                    TaxableAmount.set("currencyID", data["tipoMoneda"])
                                    TaxSubtotal.append(TaxableAmount)

                                    TaxAmount = etree.Element(
                                        self.getInvoiceNameSpace("cbc")+"TaxAmount")
 
                                    tax_amount = 0.0
                                    if(str(tributo['codigo']) == '05'):
                                        tax_amount = float(total_cargo_iva) * (float(tributo['porcentaje'])/100)
                                        TaxAmount.text = format(float(tax_amount), '.2f') 
                                    else:
                                        TaxAmount.text = format(float(item_array['montoAfectacionTributo']), '.2f')

                                    TaxAmount.set("currencyID", data["tipoMoneda"])
                                    TaxSubtotal.append(TaxAmount)

                                    TaxCategory = etree.Element(
                                        self.getInvoiceNameSpace("cac")+"TaxCategory")

                                    Percent = etree.Element(
                                        self.getInvoiceNameSpace("cbc")+"Percent")
                                    Percent.text = format(float(tributo['porcentaje']), '.2f')
                                    TaxCategory.append(Percent)

                                    TaxScheme = etree.Element(
                                        self.getInvoiceNameSpace("cac")+"TaxScheme")
                                    ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                                    ID.text = tributo['codigo']
                                    TaxScheme.append(ID)
                                    Name = etree.Element(self.getInvoiceNameSpace("cbc")+"Name")
                                    Name.text = self.getTributName(tributo['codigo'])
                                    TaxScheme.append(Name)                                    
                                    TaxCategory.append(TaxScheme)

                                    TaxSubtotal.append(TaxCategory)
                                    WithholdingTaxTotal.append(TaxSubtotal)
                                    
                            InvoiceLine.append(WithholdingTaxTotal)

                Item = etree.Element(self.getInvoiceNameSpace("cac")+"Item")
                Description = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"Description")
                Description.text = item['descripcion']
                Item.append(Description)

                BrandName = etree.Element(
                        self.getInvoiceNameSpace("cbc")+"BrandName")
                if(item['brand_name']):                    
                    BrandName.text = item['brand_name']
                    Item.append(BrandName)

                ModelName = etree.Element(self.getInvoiceNameSpace("cbc")+"ModelName")
                if('model' in item):
                    if(item['model']):                        
                        ModelName.text = item['model']
                        Item.append(ModelName)
                

                StandardItemIdentification = etree.Element( self.getInvoiceNameSpace("cac")+"StandardItemIdentification")
                ID = etree.Element(self.getInvoiceNameSpace("cbc")+"ID")
                ID.set("schemeAgencyID", "10")
                ID.set("schemeID", "001")
                ID.text = item["clasificacionProductoServicioCodigo"]
                StandardItemIdentification.append(ID)

                Item.append(StandardItemIdentification)

                InvoiceLine.append(Item)

                Price = etree.Element(self.getInvoiceNameSpace("cac")+"Price")
                PriceAmount = etree.Element(
                    self.getInvoiceNameSpace("cbc")+"PriceAmount")
                PriceAmount.text = format(float(item['precioUnidad']), '.2f')
                PriceAmount.set("currencyID", data["tipoMoneda"])
                Price.append(PriceAmount) 

                BaseQuantity = etree.Element(self.getInvoiceNameSpace("cbc")+"BaseQuantity")
                BaseQuantity.text = str("1")
                BaseQuantity.set("unitCode", item["unidadMedida"])
                Price.append(BaseQuantity)

                InvoiceLine.append(Price)

                InvoiceNode.append(InvoiceLine)
                index = index+1
        except Exception as e:
            exc_traceback = sys.exc_info() 
            #with open('/odoo/custom/dian/dian_efact/dianservice/log.js', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)

        tree.write(XMLpath+"/XMLdocuments/2_unsigned/"+xmlClientPath+"/"+fileName+".xml",
                   pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes")
        self.prettyXMLSave(XMLpath+"/XMLdocuments/2_unsigned/" +
                           xmlClientPath+"/"+fileName+".xml")
        return XMLpath+"/XMLdocuments/2_unsigned/"+xmlClientPath+"/"+fileName+".xml"

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

    def getInvoiceNameSpace(self, namespace):
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
        tributes_ordered_by_code = ["01","04","03"]
        tag_tax_total_added=False
        for tribute_code in tributes_ordered_by_code:
            if(int(tribute_code)<=9):
                tribute_code = str(str(tribute_code).zfill(2))
            tributo = tributos[str(tribute_code)]
            tag_tax_total_added=False
            totalSubtaxes = self.get_global_tax_amount(str(tribute_code), tributos)
            for tributo_item_percent_differenced in tributo:
                ID = tributo_item_percent_differenced['codigo']                
                # Doesn't applies for reteIVA, reteFuente, reteICA, reteCREEE
                if(str(ID) != '05' and str(ID) != '06' and str(ID) != '07' and str(ID) != '08' and str(ID) != '22'):
                    subtotals_same_code = totalSubtaxes                  
                    if(tag_tax_total_added==False):
                        TaxAmount = format( subtotals_same_code, '.2f')
                        tributes_string = str(tributes_string) + str(ID) + str(TaxAmount)                        
                        tributes_array.append({"id": ID, "amount": TaxAmount})
                        tag_tax_total_added = True
        tributes_result = {"string": tributes_string, "array": tributes_array}
        return tributes_result
        
    def getCUFE_Note(self, CUFE_array):
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
    
    def get_global_tax_amount(self, codigo, taxes):
        taxAmount = 0.0
        for tax_code in taxes:
            subtaxes = taxes[str(tax_code)]
            for tax in subtaxes:
                if(str(codigo)==str(tax_code)):
                    taxAmount = float(taxAmount) + float(tax['sumatoria'])
        return taxAmount