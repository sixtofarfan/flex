# -*- coding: utf-8 -*-
{
    'name':
    " Permanence Sale Partner",
    'summary':
        """ Solicitud de Permanencia para Sale Partner""",
    'description':
        """ 
        Funcionalidad sobre Permanencia y que actualize el vendedor y a su vez pueda extender el tiempo por defecto como vendedor.
        """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':['sale','base','fxo_res_partner_collection'],
    'data': [
        'views/res_partner.xml',
        'views/data.xml'
    ],
}