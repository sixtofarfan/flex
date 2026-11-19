# -*- coding: utf-8 -*-
{
    'name':
    " Res Partner Collection",
    'summary':
        """ Distribucion de cobradores""",
    'description':
        """ DIstribucion de Cobrador:
        Debes Colocar en el pedido de venta, el equipo de cobradores ( campo nuevo, debes crear un registro nuevo de cobradores )
        y con este registro se aplica al momento de validar el pedido de venta. En caso el cliente no tenga un cobrador, el sistema asignara uno de forma equitativa entre 
        los del grupo de cobradores. 

        En el formulario de partner se visualiza el campo 'cobrador'  """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':['sale','base'],
    'data': [
        'views/res_partner.xml'
    ],
}