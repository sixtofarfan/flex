# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    global_discount = fields.Boolean("Add Global Discount", readonly=True, states={'draft': [('readonly', False)]},)
    discount_type = fields.Selection([('fixed','Fixed'),('percentage','Percentage')], 
        "Discount Type", readonly=True, states={'draft': [('readonly', False)]}, default='fixed')
    acs_discount_amount = fields.Float("Discount Amount", readonly=True, states={'draft': [('readonly', False)]},)
    discount_percentage = fields.Float("Discount Percentage", readonly=True, states={'draft': [('readonly', False)]},)

    def _discount_unset(self):
        if self.env.user.company_id.purchase_discount_product_id:
            self.env['purchase.order.line'].search([('order_id', 'in', self.ids), ('product_id', '=', self.env.user.company_id.purchase_discount_product_id.id)]).unlink()

    def create_discount(self):
        Line = self.env['purchase.order.line']

        product_id = self.env.user.company_id.purchase_discount_product_id
        if not product_id:
            raise UserError(_('Please set Purchase Discount product in General Settings first.'))

        # Remove Discount line first
        self._discount_unset()

        for order in self:
            amount = 0
            if order.discount_type == 'fixed':
                amount = order.acs_discount_amount
            if order.discount_type == 'percentage':
                amount = (order.amount_total * order.discount_percentage)/100

            # Create the Purchase line
            Line.create({
                'name': product_id.name,
                'price_unit': -amount,
                'product_qty': 1.0,
                'product_uom': product_id.uom_id.id,
                'product_id': product_id.id,
                'order_id': order.id,
                'date_planned': fields.datetime.now(),
                #'sequence': 100,
            })
        return True
