# -*- coding: utf-8 -*-
{
    'name': "Hide Ebill buttons",

    'summary': """
        Hide Ebill buttons and features""",

    'description': """
        This module hides some buttons and features from Itgrupo ebill module
        when working with l10n_pe_cpe module for electronic invoice
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','ebill'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
