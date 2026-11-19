# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime, calendar

class AccountMove(models.Model):
	_inherit = 'account.move'

	def set_invoice_to_draft(self):
		for inv in self:
			if inv.state == 'posted' and inv.invoice_payment_state == 'not_paid':
				inv.button_draft()