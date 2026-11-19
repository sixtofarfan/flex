# -*- coding: utf-8 -*-
{
    'name': "Fxo Account Payment Efficiency",
    'description': """
        Modulo para el Reporte de Eficiencia de Cobranza
    """,
    'author': "Flexxoone",
    'depends': [
        'account_balance_doc_rep_it', 'report_xlsx'
    ],
    'category': 'account',
    'version': '0.1',
    'data': [
        'report/report.xml',
        'wizard/payment_efficiency_wizard.xml',

    ],
}
