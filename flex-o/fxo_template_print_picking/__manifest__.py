# -*- coding: utf-8 -*-
{
    'name': 'module for print Guide',
    'version': '1.0',
    "author": "[Flexxoone]",
    'summary': 'Módulo para la impresión de guias preimpresas',
    'sequence': 35,
    'license': 'AGPL-3',
    'category': 'Stock',
    'description': """
Impresion de Guia
========================
Impresion en papel preimpreso
""",
    'depends': [
        'stock',
    ],
    'data': [
        'data/report_paperformat.xml',
        'report/report.xml',
        #'report/repor_extend.xml'
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
