# -*- coding: utf-8 -*-
{
    'name': "Fxo Account by Currency",
    'description': """
        Modulo para utilizar distintas cuentas en lineas de factura
    """,
    'author': "Flexxoone",
    'depends': [
        'base',
        'account',
        'account_fields_it',
        'jp_aml_by_journal',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_journal.xml',
    ],
}
