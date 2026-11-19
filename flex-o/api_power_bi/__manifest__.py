{
    'name': "Api PowerBI - REST API",
    'version': "1.0",
    'author': "Ing Jose Blanco",
    'category': "Tools",
    'support': "odoo.com",
    'summary':'Extends the Banco API giving it api access',
    'description':'Extends the api framework giving it api access',    
    'license':'LGPL-3',
    'data': [
    ],
    'demo': [],
    'depends': ['base', 'mail', 'web', 'base_setup'],
    'images':[
        'static/description/1.jpg',
    ],
    'data': [
        'views/company_views.xml',
    ],
    'installable': True,
}