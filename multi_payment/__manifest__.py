{
    "name": "Multi Payment For Customer Invoices and Vendor Bills",
    "version": "16.0.0.1",
    "description": """
        Using this module you can pay multiple invoice payment in one click.
    """,
    'author': 'Kevin Lopez for Rail',
    'website': "http://www.odugt.com",
    'category': "Accounting",
    'summary': "Using this module you can pay multiple invoice payment in one click. Multiple invoice payment in one "
               "click for customer",
    "depends": [
        "account",
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_view.xml',
    ],
    'qweb': [],
    'css': [],
    'js': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 16.00,
    'currency': 'USD',
    'license': 'OPL-1',
}

