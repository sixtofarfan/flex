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
        'web', 
        'portal', 
        'website',
        'account_base_it', 
        'survey',
        'auth_signup',
        'mail',
        'l10n_latam_base',
        'website_sale',
        'fxo_web_signup'
    ],

    # always loaded
    'data': [
        'views/total.xml', 
    ],
}