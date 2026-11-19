# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountMove(models.Model):
	_inherit = "account.move"

	@api.onchange('journal_id', 'invoice_line_ids.product_id', 'currency_id')
	def get_refundable_journal(self):
		for rec in self:
			if rec.journal_id and rec.journal_id.is_liquidation_refundable:
				for line in rec.invoice_line_ids:
					if rec.currency_id.name == 'PEN' and line.product_id.product_tmpl_id.account_refundable_nc_id:
						line.account_id = line.product_id.product_tmpl_id.account_refundable_nc_id.id
					elif rec.currency_id.name == 'USD' and line.product_id.product_tmpl_id.account_refundable_fc_id:
						line.account_id = line.product_id.product_tmpl_id.account_refundable_fc_id.id

	def action_post(self):
		res = super(AccountMove, self).action_post()
		for rec in self:
			rec.get_refundable_journal()
		return res

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.onchange('product_id')
	def _onchange_product_id(self):
		res = super(AccountMoveLine, self)._onchange_product_id()
		for line in self:
			line._get_refundable_journal()
		return res

	def _get_refundable_journal(self):
		for rec in self:
			if rec.journal_id and \
				rec.journal_id.is_liquidation_refundable and \
				rec.move_id.currency_id.name == 'PEN' and \
				rec.product_id.product_tmpl_id.account_refundable_nc_id:
				rec.account_id = rec.product_id.product_tmpl_id.account_refundable_nc_id.id
			elif rec.journal_id and \
				rec.journal_id.is_liquidation_refundable and \
				rec.move_id.currency_id.name == 'USD' and \
				rec.product_id.product_tmpl_id.account_refundable_fc_id:
				rec.account_id = rec.product_id.product_tmpl_id.account_refundable_fc_id.id