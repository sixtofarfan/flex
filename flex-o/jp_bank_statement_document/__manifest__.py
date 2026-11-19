# -*- coding: utf-8 -*-
{
    'name': "Type and Number on Bank Statement",

    'summary': """
        Type document and number in bank statements lines""",

    'description': """
        Show type document and number in bank statements lines to create some account 
        moves with data on lines.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.polimastersac.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base'],
    'depends': ['account_fields_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/bank_statement.xml',
        'views/report_statement.xml',
    ],
    'qweb': [
        'static/src/xml/account_reconciliation.xml',
    ],
}
