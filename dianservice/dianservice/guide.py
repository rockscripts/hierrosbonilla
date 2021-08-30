from lxml import etree
import json

class Guide:

    def fillDocument(self, XMLpath, xmlClientPath, fileName,  data):
        
        tree = etree.parse(XMLpath+"/XMLdocuments/1_unfilled/UNFILLED-delivery-guide.xml")
        XMLFileContents = etree.tostring(tree.getroot(), pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes")

        #fill xml with data
        data  = json.dumps(data , indent=4)
        data = json.loads(data)
        DespatchAdviceNode = tree.getroot()
        documentID = str(data["serie"])+"-"+str(data["numero"])
        
        #DOCUMENT ID
        ID = DespatchAdviceNode.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
        ID.text = documentID

        #ISSUE DATE & TIME
        IssueDate = DespatchAdviceNode.find(self.getDespatchAdviceNameSpace("cbc")+"IssueDate")
        IssueDate.text = data["fechaEmision"]

        #NOTE
        Note = DespatchAdviceNode.find(self.getDespatchAdviceNameSpace("cbc")+"Note")
        Note.text = data["nota"]

        #SIGNATURE
        for Signature in DespatchAdviceNode.iter(self.getDespatchAdviceNameSpace("cac")+"Signature"):
            ID = Signature.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = documentID

            SignatoryParty = Signature.find(self.getDespatchAdviceNameSpace("cac")+"SignatoryParty")
            PartyIdentification = SignatoryParty.find(self.getDespatchAdviceNameSpace("cac")+"PartyIdentification")
            ID = PartyIdentification.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = data["emisor"]["nro"] 

            PartyName = SignatoryParty.find(self.getDespatchAdviceNameSpace("cac")+"PartyName")
            Name = PartyName.find(self.getDespatchAdviceNameSpace("cbc")+"Name")
            Name.text = etree.CDATA(data["emisor"]["nombre"])

            DigitalSignatureAttachment = Signature.find(self.getDespatchAdviceNameSpace("cac")+"DigitalSignatureAttachment")
            ExternalReference = DigitalSignatureAttachment.find(self.getDespatchAdviceNameSpace("cac")+"ExternalReference")
            URI = ExternalReference.find(self.getDespatchAdviceNameSpace("cbc")+"URI")
            URI.text = "#S"+documentID
        
        
        #DespatchSupplierParty -> PartyName
        for DespatchSupplierParty in DespatchAdviceNode.findall(self.getDespatchAdviceNameSpace("cac")+"DespatchSupplierParty"):

            CustomerAssignedAccountID = DespatchSupplierParty.find(self.getDespatchAdviceNameSpace("cbc")+"CustomerAssignedAccountID")
            CustomerAssignedAccountID.text = data["emisor"]["nro"]
            
            for Party in DespatchSupplierParty.iter(self.getDespatchAdviceNameSpace("cac")+"Party"):                
                for PartyLegalEntity  in Party.iter(self.getDespatchAdviceNameSpace("cac")+"PartyLegalEntity"):
                    RegistrationName = PartyLegalEntity.find(self.getDespatchAdviceNameSpace("cbc")+"RegistrationName")
                    RegistrationName.text = etree.CDATA(data["emisor"]["nombre"])                    

        
        #DeliveryCustomerParty -> PartyName
        for DeliveryCustomerParty in DespatchAdviceNode.findall(self.getDespatchAdviceNameSpace("cac")+"DeliveryCustomerParty"):
            CustomerAssignedAccountID = DeliveryCustomerParty.find(self.getDespatchAdviceNameSpace("cbc")+"CustomerAssignedAccountID")
            CustomerAssignedAccountID.text = data["receptor"]["nro"]

            Party =  DeliveryCustomerParty.find(self.getDespatchAdviceNameSpace("cac")+"Party")

            PartyLegalEntity = Party.find(self.getDespatchAdviceNameSpace("cac")+"PartyLegalEntity")
            RegistrationName = PartyLegalEntity.find(self.getDespatchAdviceNameSpace("cbc")+"RegistrationName")
            RegistrationName.text = etree.CDATA(data["receptor"]["nombre"])

         #DeliveryCustomerParty -> PartyName
        for Shipment in DespatchAdviceNode.findall(self.getDespatchAdviceNameSpace("cac")+"Shipment"):
            ID = Shipment.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = str(data["numero"])

            GrossWeightMeasure = Shipment.find(self.getDespatchAdviceNameSpace("cbc")+"GrossWeightMeasure")
            GrossWeightMeasure.text = str(data["peso"])

            ShipmentStage =  Shipment.find(self.getDespatchAdviceNameSpace("cac")+"ShipmentStage")
            TransportModeCode = ShipmentStage.find(self.getDespatchAdviceNameSpace("cbc")+"TransportModeCode")
            TransportModeCode.text = str('01') #public transport

            TransitPeriod = ShipmentStage.find(self.getDespatchAdviceNameSpace("cac")+"TransitPeriod")
            StartDate = TransitPeriod.find(self.getDespatchAdviceNameSpace("cbc")+"StartDate")
            StartDate.text = data["fechaEmision"]

            CarrierParty = ShipmentStage.find(self.getDespatchAdviceNameSpace("cac")+"CarrierParty")
            PartyIdentification = CarrierParty.find(self.getDespatchAdviceNameSpace("cac")+"PartyIdentification")
            ID = PartyIdentification.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = data['transportista']['nro']
            PartyName = CarrierParty.find(self.getDespatchAdviceNameSpace("cac")+"PartyName")
            Name = PartyName.find(self.getDespatchAdviceNameSpace("cbc")+"Name")
            Name.text = etree.CDATA(str(data['transportista']['nombre']))

            Delivery =  Shipment.find(self.getDespatchAdviceNameSpace("cac")+"Delivery")
            DeliveryAddress = Delivery.find(self.getDespatchAdviceNameSpace("cac")+"DeliveryAddress")
            ID = DeliveryAddress.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = str(data['ubigeo']['destino'])
            StreetName = DeliveryAddress.find(self.getDespatchAdviceNameSpace("cbc")+"StreetName")
            StreetName.text = etree.CDATA(str(data['receptor']['direccion']))
            Country = DeliveryAddress.find(self.getDespatchAdviceNameSpace("cac")+"Country")
            IdentificationCode = Country.find(self.getDespatchAdviceNameSpace("cbc")+"IdentificationCode")
            IdentificationCode.text = data['receptor']['codigoPais']

            OriginAddress =  Shipment.find(self.getDespatchAdviceNameSpace("cac")+"OriginAddress")
            ID = OriginAddress.find(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = str(data['ubigeo']['origen'])
            StreetName = OriginAddress.find(self.getDespatchAdviceNameSpace("cbc")+"StreetName")
            StreetName.text = etree.CDATA(str(data['emisor']['direccion']))
            Country = OriginAddress.find(self.getDespatchAdviceNameSpace("cac")+"Country")
            IdentificationCode = Country.find(self.getDespatchAdviceNameSpace("cbc")+"IdentificationCode")
            IdentificationCode.text = data['emisor']['codigoPais']            
            

        #INVOICE LINES
        index = 0
        #item = data["items"][index]
        items = data["items"]
        for item in items:
            DespatchLine = etree.Element(self.getDespatchAdviceNameSpace("cac")+"DespatchLine")
            ID = etree.Element(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = str(index+1)
            DespatchLine.append(ID)

            DeliveredQuantity = etree.Element(self.getDespatchAdviceNameSpace("cbc")+"DeliveredQuantity")
            DeliveredQuantity.text = str(item["cantidad"])
            DeliveredQuantity.set("unitCode",item["unidadMedidaCantidad"])
            DespatchLine.append(DeliveredQuantity)

            
            OrderLineReference = etree.Element(self.getDespatchAdviceNameSpace("cac")+"OrderLineReference")            
            LineID = etree.Element(self.getDespatchAdviceNameSpace("cbc")+"LineID")
            LineID.text = str(index+1)
            OrderLineReference.append(LineID)
            DespatchLine.append(OrderLineReference)

            Item = etree.Element(self.getDespatchAdviceNameSpace("cac")+"Item")
            Name = etree.Element(self.getDespatchAdviceNameSpace("cbc")+"Name")
            Name.text = etree.CDATA(item["nombre"])
            Item.append(Name)

            SellersItemIdentification =  etree.Element(self.getDespatchAdviceNameSpace("cac")+"SellersItemIdentification")
            ID = etree.Element(self.getDespatchAdviceNameSpace("cbc")+"ID")
            ID.text = item["id"]
            SellersItemIdentification.append(ID)
            Item.append(SellersItemIdentification)
            
            DespatchLine.append(Item)
            DespatchAdviceNode.append(DespatchLine)
            index = index+1

        tree.write(XMLpath+"/XMLdocuments/2_unsigned/"+fileName+".xml")
        
        return XMLpath+"/XMLdocuments/2_unsigned/"+fileName+".xml"

    def getDespatchAdviceNameSpace(self, namespace):
        if(namespace=="sac"):
           return "{urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1}"
        if(namespace=="cbc"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
        if(namespace=="ext"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}"
        if(namespace=="cac"):
           return "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"