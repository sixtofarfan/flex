# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	salesman_id = fields.Many2one('res.partner', string='Codigo Vendedor')

	@api.onchange('partner_id')
	def get_salesman_by_partner(self):
		for rec in self:
			if rec.partner_id and rec.partner_id.salesman_id:
				rec.salesman_id = rec.partner_id.salesman_id.id

	def _create_invoices(self, grouped=False, final=False):
		res = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
		res.get_salesman_by_partner()
		return res

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	custom_salesman_id = fields.Many2one('res.partner', related='order_id.salesman_id', string='Codigo Vendedor')

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoice(self, order, so_line, amount):
    	res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
    	if order.salesman_id:
    		res.get_salesman_by_partner()
    	return res