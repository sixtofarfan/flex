# -*- coding: utf-8 -*-
{
    'name': "Kardex Valorizado SUNAT 13.1",

    'summary': """
        Kardex Valorizado SUNAT formato 13.1""",

    'description': """
        Con este módulo se puede obtener el kardex valorizado en tiempo real.
        Trabaja con cierres mensuales.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'stock_account',
        'stock_landed_costs',
        'report_xlsx',
        'account_base_it',
        'account_fields_it',
        'account_annul',
        'l10n_pe_invoice',
        'kardex_fisico_it',
        'stock_picking_note'],

    # always loaded
    'data': [
        'data/product_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/closure_report_template.xml',
        'reports/closure_report.xml',
        'views/account_move.xml',
        'views/closing_period.xml',
        'views/report.xml',
        'views/stock_inventory.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_line.xml',
        'wizards/kardex_wizard.xml',
        'views/kardex_menu.xml',
    ],
}