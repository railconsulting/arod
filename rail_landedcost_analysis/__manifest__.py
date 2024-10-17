# -*- coding: utf-8 -*-
{
    'name': "Rail pivot analysis landed costs",

    'summary': """""",

    'description': """
    """,

    'author': 'Kevin Lopez/ Rail',
    'license': 'OPL-1',
    'category': 'Inventory',
    'version': '16.0.0.1',
    'installable': True,
    'auto_install': False,
    # any module necessary for this one to work correctly
    'depends': ['stock_landed_costs'],

    # always loaded
    'data': [
        'views/stock_landed_cost.xml',
    ],
}
