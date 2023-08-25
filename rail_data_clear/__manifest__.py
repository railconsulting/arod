# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2018 Bonainfo <guoyihot@outlook.com>
# All Rights Reserved
#
##############################################################################
{
    'author': 'Dmmsys 124358678@qq.com ',
    'website': 'www.bonainfo.com,www.dmmsys.com',
    'version': '2.0',
    'category': 'Extra Tools',
    'license': 'OPL-1',
    'support': '124358678@qq.com, bower_guo@msn.com',
    'price': 28.00,
    'currency': 'EUR',
    'images': ['static/description/main_banner.png'],

    'name': 'Data Clear Tools V16',
    'summary': """A powerful testing tool.Easily clear any odoo object data what you want. """,
    'description': """Business Testing Data Clear. You can define default model group list by yourself to help your work. """,

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'data/clear_data.xml',
        'security/ir.model.access.csv',
        'views/clear_data_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
