# -*- coding: utf-8 -*-
#@Author:   Jesus Ernesto Diaz Diaz
#Date:      02-Nov-2023
{
    'name': "Show currency rate",

    'summary': """It show the currency rate used in several forms, i.e. invoices, credit memos, payments, purchase orders, sale orders, quotations, etc.""",

    'author': "Rail Consulting",
    'website': "https://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '1.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account','purchase','sale'],

    # always loaded
    'data': [
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml'
    ],
    'license': 'LGPL-3',
}
