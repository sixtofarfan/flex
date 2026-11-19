# -*- coding: utf-8 -*-
{
    'name' : 'module for print contract subscription',
    'version': '1.0',
    "author": "[Flexxoone]",
    'summary': 'Módulo para la impresión de contratos en subscripciones',
    'category': 'Tools',
    'description':"""""",
    'depends' : [
        'sale_subscription', 
        'fxo_sale_subscription_type',
        ],
    'data': [
        "views/view_sale_suscription.xml",
        'report/report_paperformat.xml',
        'report/contract_subscription.xml',
        'report/report.xml',
        'security/ir.model.access.csv'
    ],
}
