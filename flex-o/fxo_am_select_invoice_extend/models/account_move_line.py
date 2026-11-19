from odoo import models, fields, api, _


class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		res = super(AccountMove, self).action_post()
		for inv in self.line_ids:
			inv.fxo_apply_payments()
		return res



class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	

	def fxo_apply_payments(self):
		if  self.account_line_id.id:
			line  = self.account_line_id
			line += self
			line.reconcile()

	@api.onchange('account_line_id')
	def _onchange_account_line_id(self):
		self.type_document_id = self.account_line_id.type_document_id
		self.nro_comp = self.account_line_id.nro_comp
		self.import_number = self.account_line_id.import_number
		self.date = self.account_line_id.date
		self.order_id = self.account_line_id.order_id
		self.request_id = self.account_line_id.request_id.id
		self.debit  =  self.account_line_id.amount_residual * -1 if self.account_line_id.credit > 0 else 0 
		self.credit =  self.account_line_id.amount_residual * -1 if self.account_line_id.debit >  0 else 0  
		if not self.move_id.is_invoice(include_receipts=True):
			self.partner_id = self.account_line_id.partner_id
			self.name = self.account_line_id.name
			self.account_id = self.account_line_id.account_id
			self.currency_id = self.account_line_id.currency_id
			if self.currency_id:
				self.amount_currency = self.account_line_id.amount_residual_currency * -1 
			# else:
			# 	self.debit = self.account_line_id.credit
			# 	self.credit = self.account_line_id.debit
