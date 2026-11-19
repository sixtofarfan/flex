# -*- coding: utf-8 -*-
{
    'name': "Fxo Sale Subscription Suspend",
    'description':
        """ 
        Modulo para suspender o reactivar las Subscripciones
        """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '1.0',
    'depends': [
        'sale_subscription',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/sale_subscription_suspend_reactivated.xml',
    ],
}
