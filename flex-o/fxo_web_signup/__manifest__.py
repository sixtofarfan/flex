# -*- coding: utf-8 -*-
{
    'name': "Registro Web Flexxoone",
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

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
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
        'website_sale'
    ],

    # always loaded
    'data': [
        'views/signup.xml', 
        'views/template.xml',
        'views/portal_my_details.xml',
        'views/address.xml',
        'views/l10n_latam_base.xml'
    ],
}