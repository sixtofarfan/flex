# -*- coding: utf-8 -*-
{
    'name': "Fxo Purchase Order Import",
    'description': """
        Modulo para importar lineas de orden de compra desde otras compañias
    """,
    'author': "Flexxoone",
    'depends': [
        'purchase',
        'fxo_project_extended',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'purchase',
    'version': '0.1',
    'data': [
        'views/purchase_order.xml',
        'wizard/purchase_order_line_import.xml',
    ],
}
