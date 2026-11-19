# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Invoice Control",
    'description': """
        Modulo para el Control de Facturas Canceladas
    """,
    'author': "Flexxoone",
    'depends': ['base', 'account', 'purchase', 'account_fields_it', 'fxo_payment_request', 'fields_gamma'],
    'category': 'account',
    'version': '1.0',
    'data': [
        'views/fxo_payment_request.xml',
    ],
}