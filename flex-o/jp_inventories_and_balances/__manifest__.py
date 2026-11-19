# -*- coding: utf-8 -*-
{
    'name': "PLE Inventories and Balances",

    'summary': """
        PLE Inventories and balances text files""",

    'description': """
        This module generate all the 23 text files for PLE for inventories and balances
        with a single clik.
    """,

    'author': "Ing. Jean Paul Casis", 
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'account_sunat_rep_it',
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sector_item.xml',
        'data/table_03.xml',
        'data/table_34.xml',
        'wizards/account_sunat_rep.xml',
        'views/account_menu_ib.xml',
        'views/res_config_settings_views.xml',
        'views/table_34_views.xml',
    ],
}
