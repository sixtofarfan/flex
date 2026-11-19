# -*- coding: utf-8 -*-
{
    'name': "Fxo Difered Cost",
    'description': """
        Modulo para el manejo de gastos diferidos
    """,
    'author': "Flexxoone",
    'depends': [
        'base',
        'account',
        'account_fields_it',
        'ebill',
        'jp_automate_multipayment',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_move.xml',
        'views/main_parameter.xml',
        'views/account_tax.xml',
        'wizard/account_move_defered_wizard.xml',
    ],
}
