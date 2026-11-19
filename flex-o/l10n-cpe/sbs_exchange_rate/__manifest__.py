# -*- coding: utf-8 -*-

{
    'name': 'SBS - Currency Update',
    'version': '13.0.1.0.0',
    'author': 'SistemERP',
    'website': 'http://www.sistemerp.com',
    'description': """
    Tipo de Cambio según la SBS.
    """,
    'depends': [
        'account'
    ],
    'data': [
        'data/ir_cron.xml',
        'views/currency_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
