# -*- coding: utf-8 -*-
{
    'name': "Account Balance Collection",
    'description': """
        Agrega campo en collection_id y account_period en account move, extiende importar detalle de saldos reportes de cuentas corrientes de ITGRUPO
    """,
    'author': "Flexxoone",
    'website': "https://flexxoone.com",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'maturity_analysis_rep_it',
        'account_balance_doc_rep_it',
        'import_saldos_iniciales_it',
        'account_balance_doc_advance_it',
        'nanotec_credit_limit',
        'fxo_account_requirement_credit_note'
    ],
    # always loaded
    'data': [
        'data/attachment_sample.xml',
        'views/account_move.xml',
        'views/maturity_analysis_book.xml',
        'views/account_balance_period.xml',
        'views/account_balance_date.xml',
        'views/account_balance_detail.xml',
        'views/import_move_apertura_it.xml',
        'views/main_parameter.xml',
        'fxo_functions.sql',
    ],
}
