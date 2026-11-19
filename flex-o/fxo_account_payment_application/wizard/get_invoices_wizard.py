# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetPaymentInvoicesWizard(models.TransientModel):
	_name = "get.payment.invoices.wizard"
	_description = "Get Payment Invoices Wizard"
	
	invoices = fields.Many2many('account.move', string='Invoices')
	
	def get_invoices_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Invoices'),
			'res_model': 'get.payment.invoices.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('fxo_account_payment_application.view_get_payment_invoices_wizard').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
		
	def insert(self):
		active_id = self.env.context.get('active_id')
		payment_application = self.env['account.payment.application'].search([('id','=', active_id)])
		for invoice in self.invoices:
			if not payment_application.debit_id.currency_id or payment_application.debit_id.currency_id == self.env.company.currency_id:
				application_amount = invoice.amount_residual_signed if invoice.currency_id == self.env.company.currency_id else invoice.amount_residual * payment_application.currency_rate
			else:	
				application_amount = invoice.amount_residual_signed / payment_application.currency_rate if invoice.currency_id == self.env.company.currency_id else invoice.amount_residual
			payment_application.application_lines.create({
				'application_id': active_id,
				'invoice': invoice.id,
				'application_amount': application_amount,
				})
			payment_application.verify_application_amounts()