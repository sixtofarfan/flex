# -*- coding: utf-8 -*-
{
    'name': "SUNAT Dua and free invoice",

    'summary': """
        Compute fiels for SUNAT Dua and free invoice""",

    'description': """
        This module computes account move lines and adds some fields
        to account move lines in order to see them in the corresponding
        sunat register.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','tax_register_voucher',],

    # always loaded
    'data': [
        'views/account_move.xml',
        'views/report_invoice.xml',
    ],
}
