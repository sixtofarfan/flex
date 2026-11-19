# -*- encoding: utf-8 -*-
{
    'name': 'Fxo Account User Invoices',
    'category': 'account',
    'author': 'Flexxoone',
    'website': 'http://flexxoone.com',
    'depends': [
        'account', 
        'account_fields_it', 
        'fxo_subscription_invoice_extend',
        'ebill',
    ],
    'version': '1.0',
    'description':"""
    Modulo para crear Menu Mis Documentos en pantalla principal de modulos
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_move.xml',
    ],
    'installable': True
}
