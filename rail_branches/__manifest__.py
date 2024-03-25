# -*- coding: utf-8 -*-
{
    'name': 'Manejo de multiples unidades operativas',
    'version': '16.0.0.1',
    'category': 'Sales',
    'summary': 'Manejos de sucursales / unidades operativas',
    'author': 'Rail / Kevin Lopez',
    'website': 'https://www.rail.com.mx',
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'account', 'purchase_stock','web'],
    'uninstall_hook': '_uninstall_hook',
    'data': [
        'security/branch_security.xml',
        'security/multi_branch.xml',
        'security/ir.model.access.csv',
        'views/res_branch_view.xml',
        'views/res_users.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/stock_move.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
        'views/purchase_order.xml',
        'views/stock_warehouse.xml',
        'views/stock_location.xml',
        'views/account_bank_statement.xml',
        'wizard/account_payment.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/stock_quant_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rail_branches/static/src/js/session.js',
            'rail_branches/static/src/js/branch_service.js',
            'rail_branches/static/src/xml/branch.xml'
        ]
    },
    'license' : 'OPL-1',
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
