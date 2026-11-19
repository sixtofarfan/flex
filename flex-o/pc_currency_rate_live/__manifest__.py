# -*- coding: utf-8 -*-
{
    'name': "Tipo de cambio SUNAT",

    'summary': """
        Obtiene el tipo de cambio sunat desde la SBS""",

    'description': """
        Obtiene los tipos de cambio desde la SBS automaticamente y agrega un widget en la parte superior
        y un menu para visualizar los tipos de cmabio, actualizar en rango o manualmente.
    """,

    'author': "Codex Development",
    'website': "http://www.perucodex.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'currency_rate_live'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_currency.xml',
        'wizards/manual_wizard.xml',
        'wizards/range_wizard.xml',
    ],
    'qweb': [
        'static/src/xml/systray_template_pc.xml',
    ],    
            
    
    

    'installable': True,
    'application': True,

    'price': 69.99,
    'currency': 'USD',
    'images': ['static/description/banner.gif'],
    'sequence': 0,

}
