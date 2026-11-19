# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Collections Report",
    'description': """
        Modulo generar reporte de Cobranzas
    """,
    'author': "Flexxoone",
    'depends': [
        'base',
        'account',
        'account_fields_it',
        'base_table',
        'fxo_account_balance_collection',
        'fxo_res_partner_state',
    ],
    'website': "http://soft.pvodoo.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'security/ir.model.access.csv',
        'views/account_collection_report.xml',
    ],
}