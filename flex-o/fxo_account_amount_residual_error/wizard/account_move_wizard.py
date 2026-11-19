# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMoveWizard(models.TransientModel):
	_name = 'account.move.wizard'

	def update_amount_residual_signed(self):
		for rec in self.env['account.move'].browse(self._context.get('active_ids')):
			if rec.currency_id.name == 'USD':
				rec.amount_residual_signed = rec.amount_residual * rec.currency_rate