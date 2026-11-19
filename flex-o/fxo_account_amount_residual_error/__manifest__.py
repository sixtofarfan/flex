# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Amount Residual Error",
    'description': """
        Modulo para solucionar error de calculo en amount_residual_signed
    """,
    'author': "Flexxoone",
    'website': "http://soft.pvodoo.com",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['base', 'account'],
    'data': [
        'security/security.xml',
        'views/account_move.xml',
        'wizard/account_move_wizard.xml',
    ],
}
