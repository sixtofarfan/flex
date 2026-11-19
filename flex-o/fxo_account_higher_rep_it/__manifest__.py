# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Higher Rep IT",
    'description': """
        Extension de modulo para agregar campos de gamma
    """,
    'author': "Flexxoone",
    'website': "https://flexxoone.com",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'account_higher_rep_it',
        'fxo_payment_request',
    ],
    # always loaded
    'data': [
        'fxo_functions.sql',
        'data/data.xml',
        'views/account_higher_book.xml',
    ],
}
