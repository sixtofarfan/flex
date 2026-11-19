# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = "account.payment"

	def post(self):
		for rec in self:
			if rec.order_id and rec.order_id.partner_id.credit_balance <= 0 and rec.payment_type == 'outbound':
				raise UserError('El partner del Routing Order tiene credito negativo y no puede completar esta operacion')
		return super(AccountPayment, self).post()