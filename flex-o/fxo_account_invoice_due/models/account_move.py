# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime, calendar

class Respartner(models.Model):
	_inherit = 'res.partner'

	fxo_invoice_date_end = fields.Boolean(string='Facturacion Ultimo dia del mes')
	

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		res = super(AccountMove, self).action_post()
		if self.type != 'entry'and self.partner_id.fxo_invoice_date_end and self.type_document_id.code != '07': ## Notas de credito no considera
			last_day = calendar.monthrange(self.invoice_date.year, self.invoice_date.month)[1]
			last_date = datetime.date(self.invoice_date.year, self.invoice_date.month, last_day)
			self.invoice_date_due = last_date
		return res
