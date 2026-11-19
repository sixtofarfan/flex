# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class ProductCategory(models.Model):

    _inherit = "product.category"

    transit_account = fields.Many2one(
        'account.account', string="Transit Account",
        help="This account will be used to create account move when receiving products. Nothing would be created if blank.")
