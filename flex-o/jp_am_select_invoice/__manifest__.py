# -*- coding: utf-8 -*-
{
    'name': "jp_am_select_invoice",

    'summary': """
        Add lines from sale or purchase documents""",

    'description': """
        Add lines to account entry with data from any sale
        or purchase document.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_fields_it','jp_foreign_trade_logistics'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move.xml',
        # 'wizard/get_invoices_wizard.xml',
        'wizard/get_lines_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
