# -*- coding: utf-8 -*-
{
    'name': "Actualizacion direccion del Partner",
    'author': "Fiberlux",
    'summary': "Actualizacion de los pequeños detalles en los modulo desarrollados",
    'description': "",
    'version': '1.0',
    'category': 'Tools',
    "license": "Other proprietary",
    'price': 00.00,
    'currency': 'PEN',
    "development_status": "Beta",
    "maintainers": [],
    'contributors': [],
    'depends': [
        'base',
        'sale_management',
        'sale',
    ],
    'data': [
        # "security/security_category.xml",
        # "security/security_data.xml",
        # "security/ir.model.access.csv",
        "views/xpath/xpath_res_partner_views.xml",
        "views/xpath/xpath_sale_order_views.xml"
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
