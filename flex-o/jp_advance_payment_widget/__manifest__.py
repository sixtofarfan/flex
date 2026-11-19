# -*- coding: utf-8 -*-
{
    'name': "Payment Box Widget",

    'summary': """
        Show advance payments on invoices, get date and rate""",

    'description': """
        This module adds functionallity on advance payments
        to show them on invoices that haves differents accounts
        between them.

        Also shows a small box before payment to enter date and
        payment rate for the application.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_base_it','jp_account_credit_note'],

    # always loaded
    'data': [
        'views/account.xml',
        'views/main_parameter.xml',
        'views/account_payment.xml',
        'views/account_move.xml',
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
}
