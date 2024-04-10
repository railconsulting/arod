# -*- coding: utf-8 -*-
{
    'name': "Default uso CFDI en partners",

    'summary': """
        Permite elegir un uso de cfdi por default a aplicar en facturas""",

    'author': "Rail / Kevin Lopez",
    'website': "https://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','l10n_mx_edi_40'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/partner.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
