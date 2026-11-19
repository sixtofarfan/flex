# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def _get_computed_account(self):
		self.ensure_one()

		if not self.product_id:
			return
		fiscal_position = self.move_id.fiscal_position_id
		accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position, journal_id=self.journal_id.id)
		if self.move_id.is_sale_document(include_receipts=True):
			# Out invoice.
			return accounts['income']
		elif self.move_id.is_purchase_document(include_receipts=True):
			# In invoice.
			return accounts['expense']

	def _get_computed_taxes(self):
		res = super(AccountMoveLine, self)._get_computed_taxes()
		if self.journal_id.is_refundable:
			return None
		else:
			return res