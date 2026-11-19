# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round

class AccountMoveDiferedWizard(models.TransientModel):
	_name = 'account.move.difered.wizard'
	_description = 'Account Move Difered Wizard'

	before_date = fields.Date(string='Fecha Anterior', default=lambda self: self._get_before_date())
	date = fields.Date(string='Fecha', default=fields.Date.today())
	journal_id = fields.Many2one('account.journal', string='Diario')
	after_date = fields.Date(string='Fecha Posterior', default=fields.Date.today() + relativedelta(months=1))

	@api.model
	def _get_before_date(self):
		new_date = fields.Date.today() - relativedelta(months=1)
		last_day = monthrange(new_date.year, new_date.month)[1]
		return date(new_date.year, new_date.month, last_day)

	def get_tmp_values(self, line):
		tmp_values = {
			'type_document_id': line.type_document_id.id,
			'name': line.name,
			'tc': line.tc,
			'partner_id': line.partner_id.id if line.partner_id else None,
			'nro_comp': line.nro_comp,
			'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None,
			'currency_id': line.currency_id.id if line.currency_id else None, #self.env.company.currency_id.id,
		}
		return tmp_values

	def get_tmp_move_values(self, move):
		tmp_move_values = {
			'partner_id': move.partner_id.id if move.partner_id else None,
			'type_document_id': move.type_document_id.id if move.type_document_id else None,
			'glosa': move.glosa,
			'currency_rate': move.currency_rate,
			'currency_id': move.currency_id.id,
			'invoice_date': move.invoice_date,
			'invoice_date_due': move.invoice_date_due,
			'ref': move.ref,
			'linked_to_detractions': move.linked_to_detractions,
			'type_operation': move.type_operation.id if move.type_operation else None,
			'type_good_service': move.type_good_service.id if move.type_good_service else None,
			'percent_detraction': move.percent_detraction,
			'date_detraccion': move.date_detraccion,
			'voucher_number': move.voucher_number,
			'detra_amount': move.detra_amount,
		}
		return tmp_move_values

	def set_difered_tax_account(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter.difered_tax_journal:
			raise UserError('No se ha definido un Diario para Impuesto Diferido en Parametros Principales de Contabilidad')
		Moves = self.env['account.move'].browse(self._context.get('active_ids'))
		for move in Moves:
			move.button_draft()
			move.action_change_name()
			move.journal_id = MainParameter.difered_tax_journal.id
			move.action_post()
			for line in move.invoice_line_ids:
				if line.storable_account_tax:
					raise UserError('El comprobante %s ya ha diferido sus impuestos en la linea con descripcion %s' % (line.move_id.name, line.name))
				else:
					for tax in line.tax_ids:
						move_line = move.line_ids.filtered(lambda l: l.name == tax.name)
						if not tax.difered_account_id:
							raise UserError('El Impuesto %s no tiene una Cuenta de Impuesto Diferido asociada' % tax.name)
						move_line.storable_account_tax = move_line.account_id.id
						move_line.account_id = tax.difered_account_id.id
		return self.env['popup.it'].get_message('Se completo el proceso exitosamente')

	def get_difered_moves_tax(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		Moves = self.env['account.move'].browse(self._context.get('active_ids'))
		if not MainParameter.difered_cost_journal:
			raise UserError('No se ha configurado Diario de Compras en Parametros Principales en la pestaña Gastos Diferidos')
		log = ''
		for move in Moves:
			if move.type in ['in_invoice', 'in_refund']:
				difered_account = MainParameter.difered_income_account
			else:
				difered_account = MainParameter.difered_cost_account
			lines, log_line = [], ''
			if move.difered_move_tax_id:
				log += 'El documento %s ya tiene un Asiento de Impuesto Diferido\n' % move.name
			else:
				tax_lines = move.line_ids.filtered(lambda l: l.tax_line_id)
				igv_line = move.line_ids.filtered(lambda l: l.account_id == difered_account)
				if not igv_line:
					raise UserError('No se ha encontrado una linea con la misma cuenta en igv para el \
comprobante %s con la cuenta configurada %s' % (move.ref, difered_account.code))
				igv_line = igv_line[0]
				for line in tax_lines:
					if not line.storable_account_tax:
						log_line += 'La linea %s del documento %s no tiene Cuenta de Impuesto Diferido asociada \n' % (line.name, move.name)
					else:
						tmp_values = self.get_tmp_values(line)
						base = self.env['account.account.tag'].search([('name', '=', 'BASE1')])
						if not base:
							raise UserError('No se ha encontrado etiqueta de impuesto con nombre "BASE1"')
						values = tmp_values.copy()
						values.update({
							'account_id': line.storable_account_tax.id,
							'debit': line.debit,
							'credit': line.credit,
							'currency_id': line.currency_id.id,
							'amount_currency': line.amount_currency * (-1 if line.credit > 0 else 1),
							'balance': line.credit if line.credit > 0 else line.debit,
							'tag_ids': [(6, 0, line.tag_ids.ids)] if line.tag_ids else None,
							'tax_amount_it': line.debit,
						})
						lines.append((0, 0, values))
						values = tmp_values.copy()
						if line.currency_id.name == 'USD':
							amount_untaxed = float_round(move.amount_untaxed * line.tc, 2)
						else:
							amount_untaxed = move.amount_untaxed
						values.update({
							'account_id': line.account_id.id,
							'debit': line.credit,
							'credit': line.debit,
							'currency_id': line.currency_id.id,
							'amount_currency': line.amount_currency * (-1 if line.debit > 0 else 1),
							'balance': line.credit if line.debit > 0 else line.debit,
							'tag_ids': [(6, 0, [base[0].id])],
							'tax_amount_it': amount_untaxed,
						})
						lines.append((0, 0, values))
				if log_line:
					log += log_line
				else:
					tmp_move_values = self.get_tmp_move_values(move)
					move_values = tmp_move_values.copy()
					move_values.update({
						'journal_id': MainParameter.difered_cost_journal.id,
						'date': self.date,
						'line_ids': lines,
					})
					new_move = self.env['account.move'].create(move_values)
					new_move.post()
					move.difered_move_tax_id = new_move.id
		if log:
			return self.env['popup.it'].get_message('Los siguientes documentos no pudieron ser procesados:\n' + log)
		else:
			return self.env['popup.it'].get_message('Generacion de Asientos de Impuestos Diferidos Exitosa')

	def update_amount_currency(self, values, line):
		if values.get('debit') > 0:
			values.update({'amount_currency': line.amount_currency})
		else:
			values.update({'amount_currency': -line.amount_currency if line.amount_currency else 0})
		return values

	def get_difered_moves_derive(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		Moves = self.env['account.move'].browse(self._context.get('active_ids'))
		log = ''
		for move in Moves:
			if move.return_move_id:
				log += 'El documento %s ya tiene un Asiento de Extorno\n' % move.name
			elif move.provision_move_id:
				log += 'El documento %s ya tiene un Asiento de Provision\n' % move.name
			else:
				lines_return, lines_provision = [], []
				if move.type in ['in_invoice', 'in_refund']:
					Lines = move.invoice_line_ids.filtered(lambda l: l.account_id.code.startswith('63') or l.account_id.code.startswith('65'))
					if not MainParameter.difered_cost_account:
						raise UserError('No se ha configurado una cuenta para Gastos Diferidos en Parametros Generales de Contabilidad en la pestaña de Diferidos')
					difered_account = MainParameter.difered_cost_account.id
				elif move.type in ['out_invoice', 'out_refund']:
					Lines = move.invoice_line_ids.filtered(lambda l: l.account_id.code.startswith('70'))
					if not MainParameter.difered_income_account:
						raise UserError('No se ha configurado una cuenta para Ingresos Diferidos en Parametros Generales de Contabilidad en la pestaña de Diferidos')
					difered_account = MainParameter.difered_income_account.id
				for line in Lines:
					tmp_values = self.get_tmp_values(line)
					values = tmp_values.copy()
					values.update({
						'account_id': difered_account,
						'debit': line.debit,
						'credit': line.credit,
					})
					values = self.update_amount_currency(values, line)
					lines_return.append((0, 0, values))
					values = tmp_values.copy()
					values.update({
						'account_id': line.account_id.id,
						'debit': line.credit,
						'credit': line.debit,
					})
					values = self.update_amount_currency(values, line)
					if values.get('debit') > 0:
						values.update({'amount_currency': line.amount_currency})
					else:
						values.update({'amount_currency': -line.amount_currency if line.amount_currency else 0})
					lines_return.append((0, 0, values))
					values = tmp_values.copy()
					values.update({
						'account_id': line.account_id.id,
						'debit': line.debit,
						'credit': line.credit,
					})
					values = self.update_amount_currency(values, line)
					lines_provision.append((0, 0, values))
					values = tmp_values.copy()
					values.update({
						'account_id': difered_account,
						'debit': line.credit,
						'credit': line.debit,
					})
					values = self.update_amount_currency(values, line)
					lines_provision.append((0, 0, values))
				tmp_move_values = self.get_tmp_move_values(move)
				move_values = tmp_move_values.copy()
				move_values.update({
					'journal_id': self.journal_id.id,
					'date': move.date,
					'line_ids': lines_return,
				})
				new_move = self.env['account.move'].create(move_values)
				new_move.post()
				move.return_move_id = new_move.id
				move_values = tmp_move_values.copy()
				move_values.update({
					'journal_id': self.journal_id.id,
					'date': self.after_date,
					'line_ids': lines_provision,
				})
				new_move = self.env['account.move'].create(move_values)
				new_move.post()
				move.provision_move_id = new_move.id
		if log:
			return self.env['popup.it'].get_message('Los siguientes documentos no pudieron ser procesados:\n' + log)
		else:
			return self.env['popup.it'].get_message('Generacion de Asientos Diferidos Exitosa')
		