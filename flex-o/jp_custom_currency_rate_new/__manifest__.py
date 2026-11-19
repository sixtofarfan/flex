# -*- coding: utf-8 -*-
{
    'name': "Custom Currency Rate JP",

    'summary': """
        Utilizar tipos de cambio personalizado en facturas y pagos
        """,

    'description': """
        Este módulo ayuda a publicar los asientos contables tomando
        en cuenta los tipos de cambio personalizados tanto de las factuas
        como también los pagos.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
        'account',
        'account_fields_it',
        'currency_rate_personalize',
		# 'web_notify',
        ],

    # always loaded
    'data': [
        'views/account_move.xml',
    ],
}
