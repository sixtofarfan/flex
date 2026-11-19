
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	# def _get_product_accounts(self, journal_id=None):
	# 	accounts = super(ProductTemplate, self)._get_product_accounts()
	# 	if journal_id:
	# 		Journal = self.env['account.journal'].browse(journal_id)
	# 		currency = 'USD' if Journal.currency_id.name == 'USD' else 'PEN'
	# 		if Journal and Journal.is_refundable:
	# 			income = Journal.currency_item_ids.filtered(
	# 				lambda c: c.currency_id.name == currency and
	# 					c.type == 'income'
	# 			)
	# 			expense = Journal.currency_item_ids.filtered(
	# 				lambda c: c.currency_id.name == currency and
	# 					c.type == 'expense'
	# 			)
	# 			if income:
	# 				accounts['income'] = income.account_id
	# 			if expense:
	# 				accounts['expense'] = expense.account_id
	# 	return accounts

	def get_product_accounts(self, fiscal_pos=None, journal_id=None):
		accounts = self._get_product_accounts()
		if not fiscal_pos:
			fiscal_pos = self.env['account.fiscal.position']
		return fiscal_pos.map_accounts(accounts)