# -*- coding: utf-8 -*-
{
    'name': "jp_aml_by_journal",

    'summary': """
        Change account_move_line depending on currency and journal""",

    'description': """
        Change the journal items depending on journal configures accounts
        by currency
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
