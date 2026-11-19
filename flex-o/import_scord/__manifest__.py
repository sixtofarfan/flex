{
    'name': 'Import Scord',
    'version': '1.0',
    'description': 'import',
    'summary': 'import',
    'author': 'My Company',
    'license': 'LGPL-3',
    'category': 'Sale',
    'depends': [
        'base',
        'api_bbva',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/res_company.xml',
        'views/log_import_xlsx.xml',
    ],
}