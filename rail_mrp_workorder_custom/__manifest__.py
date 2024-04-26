{
    "name": "Personalizaciones para AROD",
    "summary": """MRP Workorder Custom Screen""",
    "description": """ MRP Workorder Custom Screen""",
    "version": "16.0.3",
    "depends": ["account","mrp","mrp_workorder_hr"],
    "application": True,
    "license": "OPL-1",
    "data": [
        'security/ir.model.access.csv',
        'wizard/payment_integration_moves.xml',
        'views/mrp_production.xml',
        #'views/mrp_workorder.xml',
        'views/account_payment.xml',
        'reports/payment_integration_report.xml',
    ],
    'assets': {
       'web.assets_backend': [
            'rail_mrp_workorder_custom/static/src/**/*.js',
            'rail_mrp_workorder_custom/static/src/**/*.xml',
        ],
    },
    "auto_install": False,
    "installable": True,
}
