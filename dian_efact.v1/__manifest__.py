# -*- coding: utf-8 -*-
{
    'name': 'Dian - Emisión electrónica Colombiana',
    'description': "Addon para enviar documentos a Dian",
    'author': "ROCKSCRIPTS",
    'website': "https://instagram.com/rockscripts",
    'summary': "Emisión de documentos contables a Dian",
    'version': '0.1',
    "license": "OPL-1",
    'price':'100',
    'currency':'USD',
    'support': 'rockscripts@gmail.com',
    'category': 'module_category_account_voucher',
    "images": ["images/banner.png"],
        # any module necessary for this one to work correctly
    'depends': ['base','account','delivery'],

    # always loaded
    'data': [
#                'security/ir.model.access.csv',
                'views/views.xml',
                'views/templates.xml',
                'views/template_invoice.xml',
                'views/template_quote.xml',
                'views/edocs.xml'
            ],
    'qweb': [
                'static/src/xml/pos_ticket.xml',
                'static/src/xml/pos_screen.xml',
                'static/src/xml/website.xml'
            ],
    #"external_dependencies": {"python" : ["pytesseract"]},
    'installable': True,
}
