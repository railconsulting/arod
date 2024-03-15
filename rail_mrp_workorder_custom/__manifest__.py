{
    "name": "MRP Workorder Custom",
    "summary": """MRP Workorder Custom Screen""",
    "description": """ MRP Workorder Custom Screen""",
    "version": "16.0.3",
    "depends": ["mrp","mrp_workorder_hr"],
    "application": True,
    "license": "OPL-1",
    "data": [
        'views/mrp_production.xml',
        #'views/mrp_workorder.xml',
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
