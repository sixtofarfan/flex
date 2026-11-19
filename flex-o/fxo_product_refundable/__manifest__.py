# -*- coding: utf-8 -*-
{
    'name': "Fxo Product Refundable",
    'description': """
        Modulo para agregar cuenta de reembolso en productos
    """,
    'author': "Flexxoone",
    'depends': [
        'account_fields_it',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/product_template.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
    ],
}
