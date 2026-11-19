# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Custom Reconcile",
    'description': """
        Modulo hacer conciliaciones masivas
    """,
    'author': "Flexxoone",
    'depends': [
        'base',
        'account',
        'account_fields_it',
        'fxo_account_bank_statement_import_it',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'security/ir.model.access.csv',
        'views/account_bank_statement.xml',
        'views/main_parameter.xml',
    ],
}