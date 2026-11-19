# -*- coding: utf-8 -*-
{
    'name':
    "Fxo Account Invoice Apportion",
    'description':
    """Modulo para generar Prorrateo en facturas""",
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'account',
    'version': '0.1',
    'depends':['account_fields_it', 'fields_gamma'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
    ],
}