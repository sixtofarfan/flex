# -*- coding: utf-8 -*-
{
    'name': "SUNAT currency rate",

    'summary': """
        Get SUNAT currency rate from SBS""",

    'description': """
        Import exchange rates from SUNAT. Add system tray with today rate
        and a menu to update rates.
    """,

    'author': "Ing. Jean Paul Casis",
    'version': '13.1.0.0.0',
    'support': 'pollarolas@gmail.com',
    'website': 'https://www.odoo.com',
    "license": "AGPL-3",
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/exchange_rate.xml',
        'views/res_currency_view.xml',
        'views/res_config_settings_views.xml',
        'wizards/range_wizard.xml',
    ],
    'qweb': [
        'static/src/xml/systray.xml',
    ],

    'external_dependencies': {
    'python': ['pandas','numpy','lxml'],
    },

    'price': 35,
    'currency': 'USD',

}
