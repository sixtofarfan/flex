# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def get_tax_by_journal(self):
		for rec in self:
			Move = rec.move_id
			Taxs = self.env['parameter.tax.line'].search([
				('journal_id', '=', Move.journal_id.id),
				('type_document_id', '=', Move.type_document_id.id),
			]).mapped('tax_id')
			if Taxs:
				rec.tax_ids = [(6, 0, Taxs.ids)]
	
	@api.model_create_multi
	def create(self, vals_list):
		res = super(AccountMoveLine, self).create(vals_list)
		res.get_tax_by_journal()
		return res