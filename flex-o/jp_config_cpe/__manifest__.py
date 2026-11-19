# -*- coding: utf-8 -*-
{
    'name': "CPE Settings",

    'summary': """
        Add settings page to CPE module""",

    'description': """
        With this settings page server, certificates ando other configurations
        can be managed in just on place. Even the accountatn without permission
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_pe_cpe'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/good_service.xml',
        'views/res_partner.xml',
        'views/good_service_view.xml',
        'views/res_config_settings_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
