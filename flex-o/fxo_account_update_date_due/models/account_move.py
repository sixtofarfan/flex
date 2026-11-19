from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		res = super(AccountMove, self).action_post()
		if self.invoice_period_id and self.type in ('out_invoice'):
			self.invoice_date_due = self.invoice_period_id.date_end
		return res

	def change_date_due(self):
		for rec in self:
			if rec.invoice_period_id and rec.type in ('out_invoice'):
				rec.invoice_date_due = rec.invoice_period_id.date_end