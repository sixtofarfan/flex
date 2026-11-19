# -*- coding: utf-8 -*-
{
    'name':
    " Sale Order Type Extend",
    'summary':
        """ Sale Order Type Extend""",
    'description':
        """ Sale Order Type Extend""",
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':[
        'sale_order_type',
        'sale_subscription',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_type.xml',
        'views/sale_order.xml',
        'views/subscription.xml',
    ],
}