# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetLinesWizard(models.TransientModel):
	_name = "get.lines.wizard"
	_description = "Get Lines Wizard"
	
	lines = fields.Many2many('account.move.line', string='Lines')
	
	def get_lines_wizard(self):
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Get Lines'),
			'res_model': 'get.lines.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('jp_am_select_invoice.view_get_lines_wizard').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def insert(self):
		vals=[]
		active_id = self.env.context.get('active_id')
		debit_credit = self.env.context.get('debit_credit')
		move_id = self.env['account.move'].search([('id','=',active_id)])
		# active_ids = self.env.context.get('active_ids')
		# debit_credit = self.env.context.get('type_line')
		for line in self.lines:
			if line.currency_id:
				total = abs(line.amount_residual_currency) * move_id.currency_rate
				total_currency = abs(line.amount_residual_currency)
				if total == 0:
					total = abs(line.amount_currency) * move_id.currency_rate
					total_currency = abs(line.amount_currency)
			else:
				total = abs(line.amount_residual)
				total_currency = 0
				if total == 0:
					total = abs(line.balance)
			val = {
					'move_id': active_id,
					'partner_id': line.partner_id.id,
					'type_document_id': line.type_document_id.id,
					'nro_comp': line.nro_comp,
					'name': line.name,
					'account_id': line.account_id.id,
					'import_number': line.import_number,
					'currency_id': line.currency_id.id,
					'amount_currency': total_currency * (-1 if debit_credit == 'credit' else 1),
					'tc': move_id.currency_rate,
					'debit': total if debit_credit == 'debit' else 0,#(sum(line.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit')) if line.type in ('in_invoice','in_refund') else sum(line.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit'))) if debit_credit == 'debit' else 0,
					'credit':total if debit_credit == 'credit' else 0,#(sum(line.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('credit')) if line.type in ('out_invoice','out_refund') else sum(line.line_ids.filtered(lambda x: x.account_internal_type in ('receivable', 'payable')).mapped('debit'))) if debit_credit == 'credit' else 0,
				}
			vals.append(val)
		self.env['account.move.line'].with_context(check_move_validity=False).create(vals)
