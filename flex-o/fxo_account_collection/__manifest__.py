# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Collection",
    'description': """
        Modulo generar archivos xls para macros de recaudacion
    """,
    'author': "Flexxoone",
    'depends': [
        'base',
        'account',
        'account_fields_it',
        'jp_automate_multipayment',
        'fxo_account_balance_collection',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/account_collection.xml',
        'wizard/account_collection_wizard.xml',
    ],
}
