# -*- coding: utf-8 -*-
{
    'name': "Guide Serie",

    'summary': """
        Guide Serie by location""",

    'description': """
        Avoid picking validation if guide serie does not correspond to location.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','stock_picking_note'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/ir_sequence.xml',
        'views/stock_location.xml',
        'views/stock_picking.xml',
    ],
}
