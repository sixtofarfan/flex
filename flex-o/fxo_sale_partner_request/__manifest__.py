# -*- coding: utf-8 -*-
{
    'name':
    " Solicitud de permanencia ",
    'summary':
        """  Solicitud de permanencia  """,
    'description':
        """ Solicitud de permanencia  """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':['product','ebill','base','sale','sales_team','approvals'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval.xml',
        'views/crm_team.xml',
        'views/crm.xml',
        'data/data.xml',
    ],
}