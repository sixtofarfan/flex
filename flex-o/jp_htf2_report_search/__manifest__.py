# -*- coding: utf-8 -*-
{
    'name': "jp_htf2_report_search",

    'summary': """
        Add funcionality to Hoja de Trabajo F2""",

    'description': """
        Add fields to search view and also graph and pivot views to extend
        functionality to the module
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_htf2_report'],

    # always loaded
    'data': [
        'views/f2_balance.xml',
        'views/f2_register.xml',
    ],
}
