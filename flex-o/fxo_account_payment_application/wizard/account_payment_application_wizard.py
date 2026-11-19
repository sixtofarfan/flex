# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountPaymentApplicationWizard(models.TransientModel):
	_name = 'account.payment.application.wizard'
	_description = 'Account Payment Application Wizard'

	payment_wizard_line_ids = fields.One2many('account.payment.application.wizard.line', 'wizard_id')

	def apply_payments(self):
		for line in self.payment_wizard_line_ids:
			for json_line in line.move_line_json_ids:
				context = {
					'currency_rate': json_line.move_line_id.payment_id.type_change,
					'payment_date': json_line.move_line_id.payment_id.payment_date,
				}
				if line.move_id.type == 'out_invoice':
					MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
					if not MainParameter.custom_client_journal:
						raise UserError('No se ha definido un Diario para aplicacion de facturas de cliente')
					context.update({'custom_journal': MainParameter.custom_client_journal})
				line.move_id.with_context(context).js_assign_outstanding_line(json_line.move_line_id.id)

class AccountPaymentApplicationWizardLine(models.TransientModel):
	_name = 'account.payment.application.wizard.line'
	_description = 'Account Payment Application Wizard Line'

	wizard_id = fields.Many2one('account.payment.application.wizard', ondelete='cascade')
	move_id = fields.Many2one('account.move', string='Factura')
	move_line_json_ids = fields.One2many('account.move.line.json', 'wizard_line_id', string='Debitos Pendientes')

class AccountMoveLineJson(models.TransientModel):
	_name = 'account.move.line.json'
	_description = 'Account Move Line Json'

	wizard_line_id = fields.Many2one('account.payment.application.wizard.line', ondelete='cascade')
	move_line_id = fields.Many2one('account.move.line', string='Apunte Contable')
	name = fields.Char(string='Nombre')