from odoo import models, fields, api, _

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	advance_id = fields.Many2one('multipayment.advance.it')
	partner_bank_acc_id = fields.Many2one('res.partner.bank', string='Cuenta Bancaria')

	def _get_partner_bank_account(self):
		if self.partner_id and self.journal_id:
			acc = self.env['multipayment.advance.it'].get_acc(self.partner_id, self.journal_id)
			self.partner_bank_acc_id = acc.id if acc else None