# -*- coding: utf-8 -*-
{
    'name':
    " Product Pricelist Extend",
    'summary':
        """ Agregar Precio por producto Departamento Provincia y Distritos""",
    'description':
        """ Agregar Precio por producto Departamento Provincia y Distritos""",
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':['product','ebill','base'],
    'data': [
        'views/product_pricelist_view_extend.xml',
        'views/res_partner.xml',
        'wizard/wizard.xml',
    ],
}