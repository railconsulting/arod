# -*- coding: utf-8 -*-
{
    'name': "Rail flujo automatico de anticipos",

    'summary': """
        Crea automaticamente la nota de credito para facturas de anticipo y aplica los folios de origen""",

    'author': "Rail / Kevin Lopez",
    'website': "https://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','sale','l10n_mx_edi'],

    # always loaded
    'data': [
        'views/product_template.xml',
        'wizard/sale_advance_payment_inv.xml',
    ],
}
