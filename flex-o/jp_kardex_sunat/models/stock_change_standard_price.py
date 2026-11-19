# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockChangeStandardPrice(models.TransientModel):
    _inherit = "stock.change.standard.price"

    new_price = fields.Float(
        'Price', digits='Kardex Cost',  required=True,
        help="If cost price is increased, stock variation account will be debited "
             "and stock output account will be credited with the value = (difference of amount * quantity available).\n"
             "If cost price is decreased, stock variation account will be creadited and stock input account will be debited.")
    