# -*- coding: utf-8 -*-
{
    'name': "Unbilled Sales & Undelivered Invoices",

    'summary': """
        Show unbilled sales and undelivered invoices""",

    'description': """
        This modules modify the search view in sales module to get
        unbilled sales in list. Also modifies Invoice tree view and
        filter invoices that does not haven been delivered yet.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','sale','stock','jp_kardex_sunat'],

    # always loaded
    'data': [
        'views/account_move_view.xml',
        'views/sale_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}