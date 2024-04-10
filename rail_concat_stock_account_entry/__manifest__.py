# -*- coding: utf-8 -*-
{
    'name': "Concat stock account entries",
    'summary': """
        Concat stock account entry from many entries to a single one for each 
        origin move""",
    'author': "Rail / Kevin Lopez",
    'website': "https://www.rail.com.mx",
    'category': 'Account',
    'version': '16.0.0.1',
    'depends': ['stock_account'],
    'license': 'LGPL-3',
    'data': [
        'views/account_payment.xml',
    ],
}
