# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class sale_order(models.Model):
    _inherit = 'sale.order'

    mp_response = fields.Html( string="mercadopago")
    mp_json_response = fields.Text( string="JSON MP Response")