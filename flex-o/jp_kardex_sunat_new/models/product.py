# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        'Cost', company_dependent=True,
        digits='Kardex Cost',
        groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")
    last_cost_kardex = fields.Float(string='Last cost for kardex', digits=(12, 8))

    def _prepare_out_svl_vals(self, quantity, company):
        res = super(ProductProduct, self)._prepare_out_svl_vals(quantity, company)
        res.update({
            'unit_cost': self.last_cost_kardex,
            'value': self.last_cost_kardex * quantity * -1,
            })
        return res
    
    def get_kardex_product(self):
        return {
            'context':{'active_id':self.id},
            'name': 'Kardex',
            'type': 'ir.actions.act_window',
            'res_model': 'kardex.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }