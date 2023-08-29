# -*- coding: utf-8 -*-
{
    'name': 'Reglas de acceso para stock',
    'author': 'GPT / Kevin Lopez',
    'version': '16.0.1.1',
    'description': """Restricciones para almacenes, ubicaciones y tipos de operacion""",
    "license" : "OPL-1",
    'depends': ['base','sale_management','stock','account'],
    'data': [
        'security/warehouse_restrictions_group.xml',
        'security/warehouse_restrictions_rules.xml',
        'views/account_payment_term.xml',
        'views/warehouse_restrict_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'category': 'Warehouse',
}
