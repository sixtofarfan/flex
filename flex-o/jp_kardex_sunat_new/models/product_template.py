# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Kardex Cost', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")

    def get_kardex_template(self):
        products = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        if len(products)>1:
            raise UserError(_('There is product variants. You must get the kardex for each variant.'))
        return {
            'context':{'active_id':products[0].id},
            'name': 'Kardex',
            'type': 'ir.actions.act_window',
            'res_model': 'kardex.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            }