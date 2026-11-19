# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from json import dumps
import json
from odoo.tools import float_round

class AccountMove(models.Model):
	_inherit = "account.move"

	show_all_payments = fields.Boolean(string='Mostrar todos los pagos', default=False)

	def _compute_payments_widget_to_reconcile_info(self):
		for move in self:
			move.invoice_outstanding_credits_debits_widget = json.dumps(False)
			move.invoice_has_outstanding = False

			if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
				continue
			pay_term_line_ids = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
			
			# Obtener las cuentas de anticipos dese los parametros principales
			# y con eso se pueden mostrar los anticipos para poder aplicar en
			# las facturas
			advance_payment_account_id = []
			mp = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
			if move.is_inbound():
				advance_payment_account_id.append(mp.customer_advance_account_nc.id)
				advance_payment_account_id.append(mp.customer_advance_account_fc.id)
				for account in mp.other_accounts_client.ids:
					advance_payment_account_id.append(account)
			else:
				advance_payment_account_id.append(mp.supplier_advance_account_nc.id)
				advance_payment_account_id.append(mp.supplier_advance_account_fc.id)
				# advance_payment_account_id.append(mp.supplier_advance_account_receipt_nc.id)
				# advance_payment_account_id.append(mp.supplier_advance_account_receipt_fc.id)
				for account in mp.other_accounts_supplier.ids:
					advance_payment_account_id.append(account)

			domain = ['|', ('account_id', 'in', pay_term_line_ids.mapped('account_id').ids),
					  ('account_id', 'in', advance_payment_account_id),
					  '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
					  '|',('partner_id', '=', move.commercial_partner_id.id),
					  ('import_number', '=', move.import_number or ''),
					  ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
					  ('amount_residual_currency', '!=', 0.0),
					  ]

			if move.is_inbound():
				domain.extend([('credit', '>', 0), ('debit', '=', 0)])
				type_payment = _('Outstanding credits')
			else:
				domain.extend([('credit', '=', 0), ('debit', '>', 0)])
				type_payment = _('Outstanding debits')
			if not move.show_all_payments:
				domain.insert(0, ('order_id', 'in', move.mapped('invoice_line_ids.order_id.id')))
			info = {'title': '', 'outstanding': True, 'content': [], 'move_id': move.id}
			lines = self.env['account.move.line'].search(domain)
			currency_id = move.currency_id
			if len(lines) != 0:
				for line in lines:
					# get the outstanding residual value in invoice currency
					if line.currency_id and line.currency_id == move.currency_id:
						amount_to_show = abs(line.amount_residual_currency)
					else:
						currency = line.company_id.currency_id
						amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
														   line.date or fields.Date.today())
					if float_is_zero(amount_to_show, precision_rounding=move.currency_id.rounding):
						continue
					info['content'].append({
						'journal_name': line.ref or line.move_id.name,
						'amount': amount_to_show,
						'currency': currency_id.symbol,
						'id': line.id,
						'position': currency_id.position,
						'digits': [69, move.currency_id.decimal_places],
						'payment_date': fields.Date.to_string(line.date),
						'original_currency_id': line.currency_id.symbol if line.currency_id else self.env.company.currency_id.symbol,
						'original_amount': abs(line.amount_residual_currency),
						# 'type_change': line.tc,
					})
				info['title'] = type_payment
				move.invoice_outstanding_credits_debits_widget = json.dumps(info)
				move.invoice_has_outstanding = True