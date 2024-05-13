{
    "name": "Personalizaciones para AROD",
    "summary": """Personalizaciones para AROD""",
    "description": """Personalizaciones para AROD""",
    "version": "16.0.3",
    "depends": ["account","mrp","mrp_workorder_hr","delivery"],
    "application": True,
    "license": "OPL-1",
    "data": [
        'security/ir.model.access.csv',
        'wizard/payment_integration_moves.xml',
        'wizard/bank_flow_wizard.xml',
        'wizard/expenses_report.xml',
        'wizard/profit_report.xml',
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
