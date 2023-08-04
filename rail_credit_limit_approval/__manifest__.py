# -*- coding: utf-8 -*-
{
    'name': "Credit limit approvals",

    'summary': """
        Restringe la venta a clientes que superen su limite de credito""",

    'author': "Rail / Kevin Lopez",
    'license': 'OPL-1',
    'website': "https://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','rail_odoo_approvals'],

    # always loaded
    'data':[
        'security/ir.model.access.csv',
        'wizards/credit_approval.xml',
        'views/sale_order.xml',
    ],

}
