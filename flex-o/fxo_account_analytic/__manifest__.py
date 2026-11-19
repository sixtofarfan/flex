# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Analytic",
    'description': """
        Agrega campos en apuntes analiticos
    """,
    'author': "Flexxoone",
    'depends': ['base', 'account', 'analytic', 'account_fields_it'],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_analytic_line.xml',
        'views/account_move_line.xml',
        'views/purchase_order.xml',
    ],
}
