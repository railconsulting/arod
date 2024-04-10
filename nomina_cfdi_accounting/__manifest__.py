# -*- coding: utf-8 -*-
{
    'name': "Nomina MX contabilidad",

    'summary': """
        Optimizacion de asientos contables para lotes den ominas""",

    'author': "Rail / Kevin Lopez",
    'website': "https://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'payroll',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','hr','hr_payroll','nomina_cfdi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_department.xml',
        'views/hr_payslip_run.xml',
        'views/res_config_settings.xml',
    ],

}
