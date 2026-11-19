# -*- coding: utf-8 -*-
{
    'name': "Product Lot/SN Manual Expiry Date",

    'summary': """
       Manually set Lot/SN expiry dates in purchase receipt packing and show expiry dates in sale/internal transfer packing.""",

    'description': """
       Manually set Lot/SN expiry dates in purchase receipt packing and show expiry dates in sale/internal transfer packing.
Product expiry date
best before date
lot expiry date
expiration dates
serial expiry date
lot life date
lot best before date
serial best before date
product lot expiry date
manual expiry date
lot manual expiry date
serial number manual expiry date
pacing expiry date
set expiry date manually
    """,
    'author': 'CorTex IT Solutions Ltd.',
    'company': "CorTex IT Solutions Ltd.",
    'website': "https://www.cortexsolutions.net",
    'live_test_url':"",
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 25,
    'support': 'support@cortexsolutions.net',
    'category': 'Inventory',
    'version': '1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'product_expiry'],

    # always loaded
    'data': [
        'views/stock_move_line.xml',
        'views/stock_production_lot.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,

}
