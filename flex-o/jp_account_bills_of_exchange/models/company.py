# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

sequences = [
	{'name': _('Bills of exchange form'), 'code': 'account.bill.form','prefix': _('BEF-')},
	{'name': _('Import bills form'), 'code': 'account.import.bill.form','prefix': _('IB-')},
	{'name': _('Advanced bills form'), 'code': 'account.advanced.bill.form','prefix': _('ABF-')},
	{'name': _('Refinancing dues form'), 'code': 'account.refinancing.form','prefix': _('RDF-')},
	{'name': _('Send bank form'), 'code': 'account.send.bank','prefix': _('SBF-')},
	{'name': _('Renewal form'), 'code': 'renew.bill.form','prefix': _('RF-')},
	{'name': _('Protest payment'), 'code': 'account.protest.payment','prefix': _('PP-')},
	{'name': _('Bill payment'), 'code': 'account.bill.payment','prefix': _('BP-')},
	{'name': _('Bill protest'), 'code': 'account.protest.bill','prefix': _('BPR-')},
	{'name': _('Bill renew'), 'code': 'account.renew.bill','prefix': _('BR-')},
	{'name': _('Bank disbursement'), 'code': 'account.bank.disbursement','prefix': _('BD-')},
	]

class ResCompany(models.Model):
	_inherit = "res.company"

	customer_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Customer Journal for Bills of Exchange')
	supplier_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Supplier Journal for Bills of Exchange')
	retention_boe_account_id = fields.Many2one(comodel_name='account.account', string='Retention Account for Bills of Exchange')
	protests_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Protests Journal')
	protests_financial_expenses_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Protests Financial Expenses Journal')
	bank_interests_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Bank Interests Journal')
	round_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Round Gain and Loss Journal')
	bank_claim_journal_id = fields.Many2one(comodel_name='account.journal', string='Bank Interests Claim Journal')
	advanced_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Advanced Journal')
	protests_financial_expenses_boe_account_id = fields.Many2one(comodel_name='account.account', string='Protests Financial Expenses Account')

	def _create_boe_sequence(self):
		for sequence in sequences:
			vals = []
			for company in self:
				company_has_boe_seq = self.env['ir.sequence'].search([('code', '=', sequence['code'])]).mapped('company_id')
				if not company_has_boe_seq:
					vals.append({
						'name': sequence['name'],
						'code': sequence['code'],
						'company_id': company.id,
						'prefix': sequence['prefix'],
						'padding': 6,
						'number_next': 1,
						'number_increment': 1
					})
			if vals:
				self.env['ir.sequence'].create(vals)

	@api.model
	def create_missing_boe_sequence(self):
		company_ids  = self.env['res.company'].search([])
		company_has_boe_seq = self.env['ir.sequence'].search([('code', '=', 'account.bill.form')]).mapped('company_id')
		company_todo_sequence = company_ids - company_has_boe_seq
		company_todo_sequence._create_boe_sequence()

	def _create_per_company_boe_sequences(self):
		self.ensure_one()
		self._create_boe_sequence()

	@api.model
	def create(self, vals):
		company = super(ResCompany, self).create(vals)
		company.sudo()._create_per_company_boe_sequences()
		return company