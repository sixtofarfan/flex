# -*- coding: utf-8 -*-
{
    'name': 'Import Shipment/Delivery/Internal Transfer',
    'summary': "Import picking (Shipment/Delivery/Internal Transfer) from CSV/Excel",
    'description': "Import picking (Shipment/Delivery/Internal Transfer) from CSV/Excel",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    'support': 'ipredictitsolutions@gmail.com',

    'category': 'Warehouse',
    'version': '13.0.0.1.0',
    'depends': ['stock'],

    'data': [
        'wizard/stock_picking_view.xml',
        'views/stock_picking_import_view.xml',
    ],

    'license': "OPL-1",
    'price': 20,
    'currency': "EUR",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/main.png'],
}
