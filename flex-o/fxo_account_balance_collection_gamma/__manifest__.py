# -*- coding: utf-8 -*-
{
    'name': "Account Balance Collection Gamma",
    'description': """
        Extension de modulo fxo_account_balance_collection para agregar campos de gamma
    """,
    'author': "Flexxoone",
    'website': "https://flexxoone.com",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'fxo_account_balance_collection',
        'jp_account_bills_of_exchange',
        'nanotec_credit_limit',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_balance_detail.xml',
        'views/account_balance_period.xml',
        'views/import_move_apertura_it.xml',
        'views/main_parameter.xml',
        'views/maturity_analisis_book.xml',
        'views/maturity_analisis_dollars_book.xml',
        'wizard/account_balance_period_rep.xml',
        'wizard/maturity_analisis_dollars_rep.xml',
        'fxo_functions.sql',
    ],
}
