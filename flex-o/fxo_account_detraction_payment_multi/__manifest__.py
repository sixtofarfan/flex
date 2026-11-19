# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Move Detraction Payment",
    'description': """
        Modulo generar pagos de detracciones desde lineas de asiento
    """,
    'author': "Flexxoone",
    'depends': ['base', 'account', 'account_fields_it'],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '1.0',
    'data': [
        'security/ir.model.access.csv',
        'views/am_detraction_payment.xml',
        'wizard/am_detraction_payment_wizard.xml',
    ],
}
