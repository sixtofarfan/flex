# -*- coding: utf-8 -*-
{
    'name':
    " Contract Invoice Extend ",
    'summary':
        """  Contract Invoice Extend  """,
    'description':
        """ Contract Invoice Extend  """,
    'author': "Flexxoone",
    'website': "http://flexxoone.com/",
    'category': 'sale',
    'version': '0.1',
    'depends':[
        'product',
        'fxo_res_partner_collection',
        'sale_subscription',
        'ebill', 
        'automatic_series_update',
        'fxo_feasibility',
        'fxo_ebill_lot_in_invoice',
        'fxo_account_analytic',
        'currency_rate_personalize',
        'l10n_pe_cpe',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account.xml',
        'views/main_parameter.xml',
        'views/sale_subscription_log.xml',
        'views/product_pricelist_item.xml',
        'views/sale_order.xml',
    ],
}
