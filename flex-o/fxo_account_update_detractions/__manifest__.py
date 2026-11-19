# -*- encoding: utf-8 -*-
{
    'name': 'Fxo Account Update Detractions',
    'category': 'account',
    'author': 'Flexxoone',
    'website': 'http://flexxoone.com',
    'depends': ['account', 'account_fields_it'],
    'version': '1.0',
    'description':"""
    Modulo para Actualizar Facturas en base a Archivo de Detracciones
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_update_detractions.xml',
    ],
    'installable': True
}
