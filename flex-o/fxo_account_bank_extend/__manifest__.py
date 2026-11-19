# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Bank Extend",
    'description': """
        Agrega campo tipo de cuenta en cuentas bancarias
    """,
    'author': "Flexxoone",
    'website': "http://soft.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'views/res_partner_bank.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
