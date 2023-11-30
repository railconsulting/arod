# -*- coding: utf-8 -*-
{
    'name': "Work entry batch wizard",

    'summary': """
        Create a wizard for regist work entry records from
        payslip batch""",

    'description': """
        When handle a lot of employees it's a hard work record a lot of extra work
        entries per payslip, this module add a wizard to do it in the same view
    """,

    'author': "Rail / Kevin Lopez",
    'website': "http://www.rail.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/work_entry_batch.xml',
        'views/hr_payslip_run.xml',
    ],
}
