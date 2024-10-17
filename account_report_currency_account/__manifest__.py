{
    'name': 'Account custom filters CURRENCY/ACCOUNT',
    'version': '16.0.0.1.0',
    'category': 'Account',
    'author': 'Kevin',
    'depends': ['account_reports'],
    'data': [
        'data/report.xml'
    ],
   'assets': {
        
        'web.assets_backend': [
           
            'account_report_currency_account/static/src/js/account_report.js',
          
        ],
       
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
