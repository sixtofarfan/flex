# -*- coding: utf-8 -*-
{
    'name': "Importe en nota de crédito",

    'summary': """
        Cambia el importe en la nota de crédito segun el item""",

    'description': """
        Automatización para la nota de crédito cuando se cambia el
        importe de un item y adecuación al item en la pestaña sunat
        segun módulo de ItGrupo.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
