# -*- encoding: utf-8 -*-
{
    'name': 'Fxo Account Update Date Due',
    'category': 'account',
    'author': 'Flexxoone',
    'website': 'http://flexxoone.com',
    'depends': ['account', 'account_fields_it', 'fxo_account_collection'],
    'version': '1.0',
    'description':"""
    Modulo para Actualizar Fecha de Finalizacion en Facturas con la fecha fin del periodo de Facturacion
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'views/account_move.xml',
    ],
    'installable': True
}
