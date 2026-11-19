# -*- encoding: utf-8 -*-
{
    'name': 'EXTENCION PARA  EL EBILL PARA CAMBIOS YA QUE ALGUNAS EMPRESAS NO SE PUEDE ACTUALIZAR EL EBILL',
    'category': 'uncategorize',
    'author': 'ITGRUPO',
    'depends': ['ebill','query_ruc_dni'],
    'version': '1.0',
    'description':"""
     Descripcion
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        #'security/security.xml',
        'account_move.xml',
        ],
    'installable': True
}