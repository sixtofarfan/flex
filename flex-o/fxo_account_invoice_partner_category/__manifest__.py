# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Invoice Partner Category",
    'description': """
        Modulo para visualizar categoria del partner en asiento contable
    """,
    'author': "Flexxoone",
    'depends': [
        'account_fields_it',
        'base_table',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_move.xml',
        'views/res_partner.xml',
    ],
}
