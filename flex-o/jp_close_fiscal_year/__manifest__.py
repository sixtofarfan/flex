# -*- coding: utf-8 -*-
{
    'name': "Close Fiscal Year",

    'summary': """
        Close accounting fiscal year for Perú""",

    'description': """
        Accounting closure procedure to get initial journal entry
        for next fiscal year
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_base_it','account_fields_it'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_closure.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
