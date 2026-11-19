# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountDetractionsWizard(models.TransientModel):
	_inherit = 'account.detractions.wizard'

	def get_data(self, invoice, m):
		res = super(AccountDetractionsWizard, self).get_data(invoice, m)
		res['bill_to_numberdocument'] = invoice.partner_id.id if invoice.partner_id else None,
		return res