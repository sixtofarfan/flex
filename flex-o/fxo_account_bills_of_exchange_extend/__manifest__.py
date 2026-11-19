# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Bills of Exchange Extend",
    'description': """
        Modulo para extender bills of exchange y agregar campos de gamma
    """,
    'author': "Flexxoone",
    'depends': [
        'jp_account_bills_of_exchange',
        'fields_gamma',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'data/attachment.xml',
        'views/account_bill.xml',
        'views/account_advanced_bill_form.xml',
        'reports/bill_advanced_form_template.xml',
        'wizard/aceptation_wizard.xml',
    ],
}
