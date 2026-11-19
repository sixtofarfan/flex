# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Analytic Id",
    'description': """
        Se agrega el campo analytic_account_id a la vista tree de Libro Mayor
    """,
    'author': "Flexxoone",
    'depends': [
        'account',
    ],
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_move_line.xml',
    ],
}
