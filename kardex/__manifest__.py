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
        'wizard/asistente_kardex.xml',
        'views/reporte_kardex.xml',
        'views/report_stockinventory.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'certificate': '',
}
