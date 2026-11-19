# -*- coding: utf-8 -*-
{
    'name': "Fxo Sale Subscription State Update",
    'description':
        """ 
        Modulo para cambiar estados de lineas de Subscripcion
        """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '1.0',
    'depends':[
            'fxo_feasibility',
            'odoo_job_costing_management',
            'sale_subscription',
            ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/sale_subscription.xml',
        'views/sale_subscription_line_state.xml',
    ],
}