# -*- encoding: utf-8 -*-

{
    'name' : 'Kardex',
    'version' : '16.0.0.1',
    'category': 'Custom',
    'description': """Modulo para reporte de kardex""",
    'author': 'Kevin Lopez',
    'website': '',
    'depends' : [ 'stock' ],
    'data' : [
        'security/ir.model.access.csv',
        'security/groups_view_cost.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/report_stockinventory.xml',
        'report/kardex_report_template.xml',
        'report/kardex_report_format.xml',
        'wizard/kardex_wizard.xml',
    ],
    'installable': True,
    'certificate': '',
}
