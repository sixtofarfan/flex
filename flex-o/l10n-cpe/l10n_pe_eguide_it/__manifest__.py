# -*- coding: utf-8 -*-
{
    'name': "Eguide It",

    'summary': """
        Eguide para it grupo""",

    'description': """
        Extension de modulo l10n_pe_eguide para trabajar con modulo de itgrupo
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_eguide','remission_guide_it'],
    #'depends': ['l10n_pe_eguide'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_view.xml',
    ],
}
