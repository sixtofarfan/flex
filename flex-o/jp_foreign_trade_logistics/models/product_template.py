# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ 

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_product_accounts(self):
        res = super(ProductTemplate, self)._get_product_accounts()
        if self.categ_id.transit_account:
            res.update({'expense': self.categ_id.transit_account,})
        return res