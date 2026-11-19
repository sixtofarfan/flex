# -*- coding: utf-8 -*-
{
    'name':"Patient",
    'summary':
        """ Agregar paciente en facturas y en Stock Picking """,
    'description':
        """ Agregar paciente en facturas y en Stock Picking""",
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':['account','stock'],
    'data': [
        'views/account_move.xml',
        'views/stock_picking.xml'
    ],
}