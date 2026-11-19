# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Journal Rep IT",
    'description': """
        Extension de modulo para agregar campos de gamma
    """,
    'author': "Flexxoone",
    'website': "https://flexxoone.com",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'account_journal_rep_it',
    ],
    # always loaded
    'data': [
        'views/account_journal_book.xml',
    ],
}