# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def action_confirm(self):
		res = super(SaleOrder, self).action_confirm()
		for rec in self:
			for line in rec.order_line:
				SubLine = line.subscription_id.recurring_invoice_line_ids.filtered(lambda l: l.product_id == line.product_id and l.partner_street_destination == line.partner_street_destination)
				if SubLine:
					SubLine.write({
						'fees_number': line.nro_quotes,
						'qty_months': line.qty_months,
					})
		return res

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	
	qty_months = fields.Integer(string='Numero de Meses')

	@api.onchange('discount')
	def get_qty_months(self):
		self.qty_months = 1 if self.discount > 0 else 0

	@api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
	def _onchange_discount(self):
		res = super(SaleOrderLine, self)._onchange_discount()
		Pricelist = self.order_id.pricelist_id
		for item in Pricelist.item_ids:
			if item.applied_on == '2_product_category':
				if item.categ_id == self.product_id.categ_id and item.discount_extra > 0:
					self.discount = item.discount_extra
					self.qty_months = item.default_months
			elif item.applied_on == '1_product':
				if item.product_tmpl_id == self.product_id.product_tmpl_id and item.discount_extra > 0:
					self.discount = item.discount_extra
					self.qty_months = item.default_months
			elif item.applied_on == '0_product_variant':
				if item.product_id == self.product_id and item.discount_extra > 0:
					self.discount = item.discount_extra
					self.qty_months = item.default_months
		return res