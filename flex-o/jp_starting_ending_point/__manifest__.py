# -*- coding: utf-8 -*-
{
    'name': "Starting and ending point",

    'summary': """
        Add selection field to picking""",

    'description': """
            This module add model to satrting and ending point in pickings and the user
            can select wich adress to delivery items.
    """,

    'author': "Ing. Jean Paul Casis",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock','stock_picking_note'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking.xml',
        # 'views/templates.xml',
    ],
}
