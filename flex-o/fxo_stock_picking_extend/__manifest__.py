# -*- coding: utf-8 -*-
{
    'name':
    "Stock Picking Extend",
    'summary':
    """
        Modulo de extensión para la impresión de guías y guías electrónicas""",
    'description':
    """
        Modulo especial para agregar los datos del transportista y unificar
        las pestañas de Personalización Peruana y Transportista en la guía 
        de salida. Ademas de agrega la verificación si es una guía electrónica
        en la serie.
    """,
    'author':
    "Jean Paul Casis",
    'website':
    "http://www.flexxoone.com",

    'category':
    'Uncategorized',
    'version':
    '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'stock_account', 'product', 'stock', 'mrp', 'purchase_requisition','sale_stock', 'fleet',
    ],

    # always loaded
    'data': [
        'views/res_partner_view.xml',
        'views/stock_picking_views.xml',
    ],
    
}
