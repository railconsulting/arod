{
    'name': "Importar facturas de proveedor via XML",
    'summary': """""",
    'description': """
    """,
    'author': "Rail / Kevin Lopez",
    'license': 'OPL-1',
    'category': 'Location',
    'version': '16.0.0.1',
    'depends': [
        'base',
        'account',
        'portal',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data_sequence.xml',
        'views/account_move_views.xml',
        'views/xml_import_invoice_views.xml',
        #'views/portal_templates.xml',
        'wizard/xml_import_wizard_views.xml',
        'views/res_config_parameters_view_extended.xml',
    ],
    'external_dependencies': {
        'python': [
            'cfdiclient',
        ],
    },
}
