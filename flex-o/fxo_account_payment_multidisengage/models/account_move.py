# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_remove_move_reconcile(self):
		for rec in self:
			invoice_payments_widget = json.loads(rec.invoice_payments_widget)
			if invoice_payments_widget:
				content = invoice_payments_widget.get('content')
				if content:
					for line in content:
						MoveLine = self.env['account.move.line'].browse(line.get('payment_id'))
						MoveLine.remove_move_reconcile()