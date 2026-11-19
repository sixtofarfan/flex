# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_payment(models.Model):
	_inherit = 'account.payment'

	@api.onchange('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
	@api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
	def _compute_destination_account_id_new(self):
		if not self.destination_account_id:
			self._compute_destination_account_id()