# -*- coding: utf-8 -*-
{
    'name': 'Account Partial Payment Reconcile',
    'version': '16.0.0.1',
    'author': 'GPT / Kevin Lopez',
    "sequence": 2,
    'category': 'Accounting',
    'depends': ['account'],
    'description': """
  Partial Payment Reconciliation and Unreconciliation
    """,
    'data': [
        'security/ir.model.access.csv',
        'wizard/partial_payment_wizard.xml',
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'rail_partial_payment_reconcile/static/src/css/account.css',
            'rail_partial_payment_reconcile/static/src/js/account_payment_field.js',
            'rail_partial_payment_reconcile/static/src/xml/**/*',
        ],
    },

    'application': True,
    'installable': True,
    "auto_install": False,
    "license": "LGPL-3",
}
