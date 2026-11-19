# -*- coding: utf-8 -*-
{
    'name':
    "Registro Indeci",
    'summary':
    """
        Registro de datos del ciudadano con acceso a encuestas para
        los simulacros""",
    'description':
    """
        Interacción activa con los ciudadanos sobre las actividades 
        de simulacros que realiza el Instituto Nacional de Defensa 
        Civil (INDECI) y recopilar información que permita elaborar 
        datos estadísticos que sirva de apoyo en la toma de decisiones.
    """,
    'author':
    "Jean Paul Casis",
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
    ['base', 'web', 'portal', 'website', 'survey', 'l10n_pe_toponyms'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/res_partner_view.xml',
        'views/address_mapbox.xml',
        'views/templates.xml',
        'views/res_partner_view.xml'
    ],
}