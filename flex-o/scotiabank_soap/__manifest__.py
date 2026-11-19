{
    'name': "Banco scotiabank - SOAP API",
    'version': "1.0",
    'author': "ING Jose Blanco",
    'category': "Tools",
    'support': "odoo.com",
    'summary':'Extends the Banco scotiabank giving it soap access',
    'description':'Extends the soap framework giving it soap access',    
    'license':'LGPL-3',
    'data': [
    ],
    'demo': [],
    'depends': ['base', 'mail', 'web', 'base_setup'],
    'images':[
        'static/description/1.jpg',
    ],
    'data': [
        'views/logs_request_view.xml',
        'views/company_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}