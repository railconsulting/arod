# -*- coding: utf-8 -*-
{
    'name': "Entradas contables complementarias",

    'summary': """
        Permite modificar automaticamente los asientos contables de proveedores
        para hacer registro de lineas complementarias""",

    'author': "Rail/ Kevin Lopez",
    'website': "https://www.rail.com.mx",

    'category': 'accounting',
    'version': '16.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_journal.xml',
        'views/partner.xml',
        'views/account_move.xml',
    ],

}
