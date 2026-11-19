# -*- coding: utf-8 -*-

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

import odoo.modules as addons
loaded_modules = addons.module.loaded


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_to_split = fields.Float(string='Split Qty.')
    price_to_split = fields.Float(string='Split Price.')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        res = super(AccountMoveLine, self).copy(default=default)
        if "sale" in loaded_modules and self.env.context.get('from_split_invoice'):
            sale_lines = self.env['sale.order.line'].search([('invoice_lines','in',self.id)])
            for order_line in sale_lines:
                order_line.invoice_lines = [(4,res.id)]
        return res
