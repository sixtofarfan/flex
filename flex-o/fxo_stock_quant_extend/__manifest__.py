# -*- coding: utf-8 -*-
{
    'name': "Fxo Stock Quant Extend",
    'description':
    """
        Modulo para agregar campo life_date del lote en vista de quants
    """,
    'author': "Flexxoone",
    'website':
    "http://www.flexxoone.com",

    'category':
    'Uncategorized',
    'version':'0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'stock',
        'product_expiry',
    ],

    # always loaded
    'data': [
        'views/stock_quant.xml',
    ],
    
}
