# -*- coding: utf-8 -*-
{
    'name':"Api Rest",
    'summary':
        """ Api Rest """,
    'description':
    """
        Api Rest
    """,
    'author':"Ing Gregorio Code",
    'website': "http://gregoriocode.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category':'API',
    'version':'0.1',
    # any module necessary for this one to work correctly
    'depends':
        ['base','web','sale_subscription'],
    # always loaded
    'data': [
        'data/ir_configparameter_data.xml'
    ]
}