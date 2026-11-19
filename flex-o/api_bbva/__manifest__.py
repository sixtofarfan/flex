{
    'name': "Banco BBVA - REST API",
    'version': "1.0",
    'author': "Erick Delgado",
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
        'views/logs_request_view.xml',
        'views/company_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}