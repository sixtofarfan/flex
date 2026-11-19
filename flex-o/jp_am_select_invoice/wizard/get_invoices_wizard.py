# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetInvoicesLines(models.TransientModel):
	_name = "get.invoices.lines.wizard"
	_description = "Get Invoices Lines Wizard"
	
	invoices = fields.Many2many('account.move', string='Invoices')
	
	def get_invoices_lines_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Invoices'),
			'res_model': 'get.invoices.lines.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_am_select_invoice.view_get_invoices_lines_wizard').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
		
	def insert(self):
		vals=[]
		active_id = self.env.context.get('active_id')
		debit_credit = self.env.context.get('debit_credit')
		for invoice in self.invoices:
			val = {
					'move_id': active_id,
					'partner_id': invoice.partner_id.id,
					'type_document_id': invoice.type_document_id.id,
					'nro_comp': invoice.ref,
					'name': invoice.glosa,
					'account_id': invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).account_id.id,
					'import_number': invoice.import_number,
					'currency_id': invoice.currency_id.id,
					'amount_currency': invoice.amount_total * (-1 if debit_credit == 'credit' else 1),
					'tc': self.env['account.move'].search([('id','=', active_id)]).currency_rate,
					'debit': invoice.amount_total * self.env['account.move'].search([('id','=', active_id)]).currency_rate if debit_credit == 'debit' else 0,#(sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit')) if invoice.type in ('in_invoice','in_refund') else sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit'))) if debit_credit == 'debit' else 0,
					'credit': invoice.amount_total * self.env['account.move'].search([('id','=', active_id)]).currency_rate if debit_credit == 'credit' else 0,#(sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit')) if invoice.type in ('out_invoice','out_refund') else sum(invoice.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit'))) if debit_credit == 'credit' else 0,
				}
			vals.append(val)
			# for line in invoice.line_ids:
			# 	print(line.account_internal_type)
			# 	print(line.debit)
			# 	print(line.credit)
			# 	print(line.balance)
		self.env['account.move.line'].with_context(check_move_validity=False).create(vals)
