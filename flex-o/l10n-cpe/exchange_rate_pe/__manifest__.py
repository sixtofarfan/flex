# -*- coding: utf-8 -*-
###############################################################################

{
    'name': 'Peruvian exchange rate',
    'version': '13.0',
    'author': 'SistemERP',
    'category': 'Accounting',
    'summary': 'Peruvian exchange rate',
    'license': 'AGPL-3',
    'description': """
Peruvian exchange rate
    """,
    'website': 'http://sistemerp.com',
    'depends': ['account'],
    'data': [
        'views/form_view.xml',
        'data/res_currency_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    "sequence": 2,
}
