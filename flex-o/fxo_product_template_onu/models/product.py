# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    onu_code = fields.Many2one(comodel_name='einvoice.catalog.25', string='Codigo ONU')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('categ_id')
    def _onchange_category(self):
        if self.categ_id:
            if self.categ_id.onu_code:
                self.onu_code = self.categ_id.onu_code
