# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools.translate import _

class AccountFollowupReport(models.AbstractModel):
	_inherit = "account.followup.report"

	def _get_columns_name(self, options):
		"""
		Override
		Return the name of the columns of the follow-ups report
		"""
		headers = [{},
					{'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
					{'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
					{'name': _('Source Document'), 'style': 'text-align:center; white-space:nowrap;'},
					{'name': _('Type Document'), 'style': 'text-align:center; white-space:nowrap;'},
					{'name': _('Communication'), 'style': 'text-align:right; white-space:nowrap;'},
					{'name': _('Expected Date'), 'class': 'date', 'style': 'white-space:nowrap;'},
					{'name': _('Excluded'), 'class': 'date', 'style': 'white-space:nowrap;'},
					{'name': _('Total Due'), 'class': 'number o_price_total', 'style': 'text-align:right; white-space:nowrap;'}
					]
		if self.env.context.get('print_mode'):
			headers = headers[:6] + headers[8:]  # Remove the 'Expected Date' and 'Excluded' columns
		return headers
    
	def _get_lines(self, options, line_id=None):
		"""
		Override
		Compute and return the lines of the columns of the follow-ups report.
		"""
        # Get date format for the lang
		partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
		if not partner:
			return []

		lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code
		lines = []
		res = {}
		res_boe = {}
		today = fields.Date.today()
		line_num = 0
		# facturas
		am_ids = self.env['account.move'].search([('partner_id','=',partner.id),('amount_residual','!=',0)])
		aml_ids = am_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable')
		# for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
		for l in aml_ids:
			if l.company_id == self.env.company:
				if self.env.context.get('print_mode') and l.blocked:
					continue
				currency = l.currency_id or l.company_id.currency_id
				if currency not in res:
					res[currency] = []
				res[currency].append(l)
		for currency, aml_recs in res.items():
			total = 0
			total_issued = 0
			for aml in aml_recs:
				amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
				date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
				total += not aml.blocked and amount or 0
				is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
				is_payment = aml.payment_id
				if is_overdue or is_payment:
					total_issued += not aml.blocked and amount or 0
				if is_overdue:
					date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
				if is_payment:
					date_due = ''
				move_line_name = aml.ref or aml.name
				if self.env.context.get('print_mode'):
					move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
				amount = formatLang(self.env, amount, currency_obj=currency)
				line_num += 1
				expected_pay_date = format_date(self.env, aml.expected_pay_date, lang_code=lang_code) if aml.expected_pay_date else ''
				invoice_origin = aml.move_id.invoice_origin or ''
				if len(invoice_origin) > 43:
					invoice_origin = invoice_origin[:40] + '...'
				type_document = aml.type_document_id.name
				columns = [
					format_date(self.env, aml.date, lang_code=lang_code),
					date_due,
					invoice_origin,
					type_document,
					move_line_name,
					(expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
					{'name': '', 'blocked': aml.blocked},
					amount,
				]
				if self.env.context.get('print_mode'):
					columns = columns[:5] + columns[7:]
				lines.append({
					'id': aml.id,
					'account_move': aml.move_id,
					'name': aml.move_id.name,
					'caret_options': 'followup',
					'move_id': aml.move_id.id,
					'type': is_payment and 'payment' or 'unreconciled_aml',
					'unfoldable': False,
					'columns': [type(v) == dict and v or {'name': v} for v in columns],
				})
			total_due = formatLang(self.env, total, currency_obj=currency)
			line_num += 1
			lines.append({
				'id': line_num,
				'name': '',
				'class': 'total',
				'style': 'border-top-style: double',
				'unfoldable': False,
				'level': 3,
				'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [total >= 0 and _('Total Due') or '', total_due]],
			})
			if total_issued > 0:
				total_issued = formatLang(self.env, total_issued, currency_obj=currency)
				line_num += 1
				lines.append({
					'id': line_num,
					'name': '',
					'class': 'total',
					'unfoldable': False,
					'level': 3,
					'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [_('Total Overdue'), total_issued]],
				})
			# Add an empty line after the total to make a space between two currencies
			line_num += 1
			lines.append({
				'id': line_num,
				'name': '',
				'class': '',
				'style': 'border-bottom-style: none',
				'unfoldable': False,
				'level': 0,
				'columns': [{} for col in columns],
			})
		# Remove the last empty line
		if lines:
			lines.pop()
		boe_ids = self.env['account.bill'].search([('responsable_id','=',partner.id),('state_of_bill','in',('disbursed','portfolio','protested','to_renew'))]).sorted(key=lambda l: l.bill_date_due or l.bill_date_issue)
		for l in boe_ids:
			if l.company_id == self.env.company:
				# if self.env.context.get('print_mode') and False:
				# 	continue
				currency = l.bill_currency_id or l.company_id.currency_id
				if currency not in res_boe:
					res_boe[currency] = []
				res_boe[currency].append(l)
		for currency, aml_recs in res_boe.items():
			total = 0
			total_issued = 0
			for aml in aml_recs:
				amount = aml.bill_amount_total - sum(pay.payment_amount_signed for pay in aml.partial_payment_ids) #aml.amount_residual_currency if aml.currency_id else aml.amount_residual
				date_due = format_date(self.env, aml.bill_date_due or aml.bill_date_issue, lang_code=lang_code)
				total += amount or 0
				is_overdue = today > aml.bill_date_due if aml.bill_date_due else today > aml.bill_date_issue
				# is_payment = aml.payment_id
				if is_overdue:
					total_issued += amount or 0
				if is_overdue:
					date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
				if is_payment:
					date_due = ''
				move_line_name = aml.bank_number or aml.bill_number
				if self.env.context.get('print_mode'):
					move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
				amount = formatLang(self.env, amount, currency_obj=currency)
				line_num += 1
				expected_pay_date = format_date(self.env, aml.bill_date_due, lang_code=lang_code) if aml.bill_date_due else ''
				invoice_origin = aml.bill_form_id.name or aml.send_form_id.name
				if len(invoice_origin) > 43:
					invoice_origin = invoice_origin[:40] + '...'
				type_document = _('Bills of exchange') # TODO agregar tipo de documento
				columns = [
					format_date(self.env, aml.bill_date_issue, lang_code=lang_code),
					date_due,
					invoice_origin,
					type_document,
					move_line_name,
					(expected_pay_date and expected_pay_date + ' '),
					{'name': '', 'blocked': False},
					amount,
				]
				if self.env.context.get('print_mode'):
					columns = columns[:5] + columns[7:]
				lines.append({
					'id': aml.id,
					'account_move': aml.bill_form_id or aml.send_form_id,
					'name': aml.bill_form_id.name or aml.send_form_id.name,
					'caret_options': 'followup',
					'move_id': aml.account_move.id,
					'type': '', #is_payment and 'payment' or 'unreconciled_aml',
					'unfoldable': False,
					'columns': [type(v) == dict and v or {'name': v} for v in columns],
				})
			total_due = formatLang(self.env, total, currency_obj=currency)
			line_num += 1
			lines.append({
				'id': line_num,
				'name': '',
				'class': 'total',
				'style': 'border-top-style: double',
				'unfoldable': False,
				'level': 3,
				'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [total >= 0 and _('Total Due') or '', total_due]],
			})
			if total_issued > 0:
				total_issued = formatLang(self.env, total_issued, currency_obj=currency)
				line_num += 1
				lines.append({
					'id': line_num,
					'name': '',
					'class': 'total',
					'unfoldable': False,
					'level': 3,
					'columns': [{'name': v} for v in [''] * (4 if self.env.context.get('print_mode') else 6) + [_('Total Overdue'), total_issued]],
				})
			# Add an empty line after the total to make a space between two currencies
			line_num += 1
			lines.append({
				'id': line_num,
				'name': '',
				'class': '',
				'style': 'border-bottom-style: none',
				'unfoldable': False,
				'level': 0,
				'columns': [{} for col in columns],
			})
		# Remove the last empty line
		if lines:
			lines.pop()
		return lines