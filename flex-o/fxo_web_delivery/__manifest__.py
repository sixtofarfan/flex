# -*- coding: utf-8 -*-
{
    'name': "Shop extend Ecommerce",
    'summary':
    """
        Registro
    """,
    'description':
    """
    Registro
    """,
    'author':
    "ING Gregorio Blanco",
    'website':
    "http://www.yourcompany.com",

    
    'category':
    'Uncategorized',
    'version':
    '0.1',

    # any module necessary for this one to work correctly
    'depends':
    [
        'web', 'sale','delivery' ,'ebill'
    ],

    # always loaded
    'data': [
        'views/delivery.xml', 
    ],
}