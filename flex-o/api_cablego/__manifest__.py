{
    'name': "Cable GO - REST API",
    'version': "1.0",
    'author': "Flexxoone",
    'category': "Tools",
    'support': "http://flexxoone.com/",
    'summary':'Extends the Cable Go API giving it api access',
    'description':'Extends the api framework giving it api access',    
    'license':'LGPL-3',
    'data': [
    ],
    'demo': [],
    'depends': ['base', 'mail', 'web', 'base_setup'],
    # 'images':[
    #     'static/description/1.jpg',
    # ],
    'data': [
        'security/ir.model.access.csv',
        'views/company_views.xml',
        'views/logs_request_view.xml'
    ],
    'installable': True,
}
