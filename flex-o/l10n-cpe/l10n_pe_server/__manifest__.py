# -*- coding: utf-8 -*-
{
    'name': "Server Administration",

    'summary': """
        Server Administration""",

    'description': """
        Server Administration
    """,

    'author': "SistemERP",
    'website': "http://www.sistemerp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Peruvian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pe_server_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}