# -*- coding: utf-8 -*-
{
    'name': "Automate Multipayment",

    'summary': """
        Automate module multipayment advance from Itgrupo""",

    'description': """
        This module extends and automate the module account_payment_advance_it
        to register detractions easilly.
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
        'account_fields_it',
        'account_multipayment_advance_it',
        'fields_gamma',
        'account_invoice_detracciones_it',
        'account_massive_payment_detractions_it',
        'fxo_account_bank_extend',
        'product',
        'l10n_pe',
        'l10n_latam_base',
        'l10n_pe_invoice',
        'l10n_pe_cpe',
        'popup_it'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/good_service.xml',
        'data/einvoice_catalog_01.xml',
        'data/l10n_latam_identification_type.xml',
        'views/l10n_latam_identification_type.xml',
        'views/einvoice_catalog_01.xml',
        'views/res_bank.xml',
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/good_service_view.xml',
        'views/main_parameter.xml',
        'views/multipayment_advance_it.xml',
        'views/product_product.xml',
        'wizard/get_invoices_wizard.xml',
        'wizard/multipayment_advance_wizard.xml',
    ],
}
