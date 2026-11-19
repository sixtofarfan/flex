{
    'name': "Fxo Salesman",
    'description': """
        Agrega campo salesman_id en varios lugares
    """,
    'author': "Flexxoone",
    'depends': [
        'account_fields_it',
        'sale_enterprise',
        'base',
        'stock',
    ],
    'website': "https://flexxoone.com",
    'category': 'account',
    'version': '0.1',
    'data': [
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
    ],
}
