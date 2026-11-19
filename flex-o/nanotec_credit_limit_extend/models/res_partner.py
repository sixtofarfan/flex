# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.translate import _
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__) 


class res_partner(models.Model):
	_inherit = "res.partner"

	@api.depends('credit_ids', 'check_credit_limit', 'credit')
	def _get_credit_limit(self):
		res = super(res_partner, self)._get_credit_limit()
		for rec in self:
			Orders = self.env['sale.order'].search([('partner_id', '=', rec.id)])
			for order in Orders:
				Payments = self.env['account.payment'].search([
					('internal_ref', '=', order.internal_ref),
					('order_id', '=', order.id),
					('state', '=', 'posted'),
				])
				if rec.credit_limit2:
					credit_balance = rec.credit_limit2
				else:
					credit_balance = 0
				for pay in Payments:
					if pay.currency_id.name == 'PEN':
						if pay.payment_type == 'inbound':
							credit_balance += pay.amount
						elif pay.payment_type == 'outbound':
							credit_balance -= pay.amount
					else:
						if pay.payment_type == 'inbound':
							credit_balance += pay.amount * pay.type_change
						elif pay.payment_type == 'outbound':
							credit_balance -= pay.amount * pay.type_change
				self.credit_balance = credit_balance
		return res