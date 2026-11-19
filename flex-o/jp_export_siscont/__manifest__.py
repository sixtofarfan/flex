# -*- coding: utf-8 -*-
{
    'name': "Export to Siscont",

    'summary': """
        Export to siscont account journal entries""",

    'description': """
        Export sales, purchases, other vouchers or all to Siscont.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'report_xlsx',
        ],

    # always loaded
    'data': [
        # 'data/sequences.xml',
        'security/ir.model.access.csv',
        'wizard/export_siscont_wizard.xml',
        'views/wizard_menu.xml',
        'views/report.xml',
        # 'views/export_vouchers.xml',
        # 'views/templates.xml',
    ],
}
