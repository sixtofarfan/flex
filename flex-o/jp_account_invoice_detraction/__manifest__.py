# -*- coding: utf-8 -*-
{
    'name': "Account Invoice Detractions",

    'summary': """
        Add detraction button to invoices and generate account
        moves for the journal""",

    'description': """
        This module adds a button to the invoices and thus be
        able to provision the deduction in the corresponding 
        accounting journal.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://soft.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'l10n_pe_datas',
                'l10n_pe_invoice',
                'jp_config_cpe',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/detraction_create_file.xml',
        'data/ir_sequence_data.xml',
        'data/bank.xml',
        # 'data/good_service.xml',
        'views/payment.xml',
        'views/account_invoice.xml',
        'views/detraction.xml',
        # 'views/product.xml',
        # 'views/res_partner.xml',
        'views/res_partner_bank.xml',
        # 'views/good_service_view.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}