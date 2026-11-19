# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def custom_concilation(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		MoveLines_fil = self.env['account.move.line']
		bank_line_ids = self.line_ids.filtered(lambda l: not l.journal_entry_ids)
		conciled_ids = [0]
		# for line in self.line_ids:
		# 	print(line.journal_entry_ids)
		# 	print(line.state)
		# 	print(line.move_name)
		counter = 0
		for line in bank_line_ids:
			ConcilationLine = MainParameter.concilation_line_ids.filtered(lambda l: any(c.name in line.name for c in l.concept_ids))
			# if line.type != MainParameter.advance_concile_code:
			# 	continue
			if ConcilationLine and len(ConcilationLine) > 1:
				raise UserError('Los filtros %s han sido encontrados en una sola linea' % ','.join(ConcilationLine.mapped('name')))
			move_lines = []
			ref = (line.name or '') + '-' + (line.ref or '')
			journal_acc = self.journal_id.default_debit_account_id.id if line.amount > 0 else self.journal_id.default_credit_account_id.id
			move_vals = {
				'date': line.date,
				'journal_id': self.journal_id.id,
				'type': 'entry',
				'ref': (self.name or '') + '-' + (line.ref or ''),
				'glosa': ref,
				'currency_id': self.currency_id.id,
			}
			Catalog = self.env['einvoice.catalog.01'].search([('code', '=', '00')])
			nro_comp = '%s-%s' % (str(line.date).replace('-', ''), line.ref if line.ref else '')
			vals = {
				'partner_id': line.partner_id.id if line.partner_id else None,
				'name': ref,
				'statement_id': line.statement_id.id,
				'statement_line_id': line.id,
				'currency_id': self.currency_id.id if self.currency_id.name == 'USD' else None,
				'type_document_id': Catalog.id if Catalog else None,
				'nro_comp': nro_comp,
				'order_id': line.order_id.id if line.order_id else None,
			}
			if ConcilationLine:
				if ConcilationLine.partner_bank:
					PartnerBank = line.statement_id.journal_id.bank_partner_id
					vals['partner_id'] = PartnerBank.id if PartnerBank else vals['partner_id']
				vals['account_id'] = journal_acc
				vals['debit'] = abs(line.amount) if line.amount > 0 else 0
				vals['credit'] = abs(line.amount) if line.amount < 0 else 0
				if self.currency_id.name == 'USD':
					vals['amount_currency'] = line.amount
				move_lines.append((0, 0, vals))
				vals2 = vals.copy()
				vals2['account_id'] = ConcilationLine.account_id.id
				vals2['debit'] = abs(line.amount) if (-1 * line.amount) > 0 else 0
				vals2['credit'] = abs(line.amount) if (-1 * line.amount) < 0 else 0
				if self.currency_id.name == 'USD':
					vals2['amount_currency'] = (-1 * line.amount)
				move_lines.append((0, 0, vals2))
				move_vals['line_ids'] = move_lines
				Move = self.env['account.move'].create(move_vals)
				Move.action_post()
				for line in Move.line_ids:
					if self.currency_id.name == 'USD':
						currency_rate = self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, Move.date)
						line.with_context(check_move_validity=False).write({
							'credit': self.env['report.base'].custom_round(line.credit * currency_rate, 2),
							'debit': self.env['report.base'].custom_round(line.debit * currency_rate, 2),
							'tc': currency_rate,
						})
						Move.currency_rate = currency_rate
					conciled_ids.append(line.id)
				counter += 1
			elif line.type and (line.order_id or line.partner_id) and line.amount > 0:
				AdvanceLine = MainParameter.concilation_line_ids.filtered(lambda l: l.code == line.type and l.currency_id == self.currency_id)
				if AdvanceLine:
					domain = [
						('destination_account_id', '=', AdvanceLine.account_id.id), 
						('payment_date', '=', line.date),
						('amount', '=', abs(line.amount)),
						('state', '=', 'posted'),
						('currency_id', '=', line.statement_id.currency_id.id),
						('company_id', '=', self.company_id.id),
					]
					if line.order_id:
						domain.append(('order_id', '=', line.order_id.id))
					else:
						domain.append(('partner_id', '=', line.partner_id.id))
					Payment = self.env['account.payment'].search(domain)
					if not Payment:
						payment_vals  = {
							'name': self.name,
							'partner_type': 'customer',
							'partner_id': line.order_id.partner_id.id if line.order_id else line.partner_id.id,
							'destination_account_id': AdvanceLine.account_id.id,
							'order_id': line.order_id.id if line.order_id else None,
							'journal_id': self.journal_id.id,
							'type_document_id': Catalog.id if Catalog else None,
							'nro_comp': nro_comp,
							'amount': abs(line.amount),
							'currency_id': self.currency_id.id,
							'payment_date': line.date,
							'payment_type': 'inbound',
							'cash_nro_comp': line.ref or '',
							'catalog_payment_id': line.catalog_payment_id.id if line.catalog_payment_id else None,
							'is_advance': True if AdvanceLine.is_advance else False,
							'payment_method_id': self.env['account.payment.method'].search([
								('code', '=', 'manual'),
								('payment_type', '=', 'inbound'),
							], limit=1).id,
						}
						Payment = self.env['account.payment'].create(payment_vals)
						if Payment.order_id.id:
							Payment.communication =  Payment.partner_id.name + " " + str(Payment.order_id.name) 
						else :
							Payment.communication =  Payment.partner_id.name
							
						Payment.post()
					if not line.partner_id:
						line.partner_id = Payment.partner_id.id
					# payment_line_ids = Payment.move_line_ids.filtered(lambda l: l.account_id.reconcile)
					for l in Payment.move_line_ids:
						l.statement_line_id = line.id
						l.statement_id = line.statement_id.id
						l.move_id.currency_rate = l.tc if l.tc > 1 else 1
						conciled_ids.append(l.id)
					Payment.state = 'reconciled'
					counter += 1

			elif line.type == MainParameter.advance_concile_code and line.amount < 0:
				request_domain = [
						('amount_total', '=', abs(line.amount)),
						('payment_date', '=', line.date),
						('state', '=', 'payed'),
						('company_id', '=', line.statement_id.company_id.id),
					]
				Requests = self.env['fxo.payment.request'].search(request_domain)
				if Requests and len(Requests) == 1:
					Currency = Requests.currency_id
					if Currency == line.statement_id.currency_id:
						Line = Requests.indepent_move_id.line_ids.filtered(lambda l: l.credit > 0)
						Line = Line[0]
						Line.statement_id = line.statement_id.id
						Line.statement_line_id = line.id
						Line.move_id.ref = line.statement_id.name + '-' + (line.ref or '')
						currency_rate = Currency._get_conversion_rate(Currency, self.env.company.currency_id, self.env.company, line.date)
						Line.move_id.currency_rate = currency_rate
						conciled_ids.append(Line.id)
						counter += 1
			else:
				payment_domain = [
					('payment_date', '=', line.date),
					('amount', '=', abs(line.amount)),
					('state', '=', 'posted'),
					('currency_id', '=', line.statement_id.currency_id.id),
					('company_id', '=', line.statement_id.company_id.id),
				]
				if line.amount > 0:
					payment_domain.append(('payment_type', '=', 'inbound')) 
				else:
					payment_domain.append(('payment_type', '=', 'outbound')) 
				Payment = self.env['account.payment'].search(payment_domain)
				if Payment and len(Payment) == 1:
					payment_line = Payment.move_line_ids.filtered(lambda l: not l.full_reconcile_id and (l.debit if line.amount > 0 else l.credit) > 0)
					payment_line.statement_id = line.statement_id
					payment_line.statement_line_id = line.id
					payment_line.move_id.ref = line.statement_id.name + '-' + (line.ref or '')
					Payment.state = 'reconciled'
					conciled_ids.append(payment_line.id)
					counter += 1
		bank_line_ids = self.line_ids.filtered(lambda l: not l.journal_entry_ids)
		for line in bank_line_ids:
			if self.journal_id.currency_id and self.journal_id.currency_id != self.env.company.currency_id:
				condition = " AND aml.amount_currency = {0}".format(line.amount)
			else:
				condition = " AND aml." + ("debit" if line.amount > 0 else "credit") + " = {0}".format(abs(line.amount))
			sql = """
			SELECT aml.id
			FROM account_move_line aml
			INNER JOIN account_account aa on aa.id = aml.account_id
			WHERE
			aml.date = '%s'
			AND aa.code = '%s'
			AND aml.statement_id is null
			AND aml.statement_line_id is null
			AND aml.id not in (%s)
			AND aml.company_id = %d
			%s
			LIMIT 1
			""" % (line.date, self.journal_id.default_debit_account_id.code, (','.join([str(aml_id) for aml_id in conciled_ids])), self.company_id.id, condition)
			self._cr.execute(sql)
			# print(sql)
			data = self._cr.fetchone()
			if not data:
				continue
			conciled_ids.append(data[0])
			# print(conciled_ids)
			aml_line_ids = self.env['account.move.line'].browse(data)
			if aml_line_ids:
				aml_line = aml_line_ids[0]
				aml_line.statement_id = line.statement_id
				aml_line.statement_line_id = line.id
				aml_line.move_id.ref = line.statement_id.name + '-' + (line.ref if line.ref else '')
				counter += 1
		return self.env['popup.it'].get_message('Se concilio %d registros correctamente' % counter)

	def get_conciliation_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Conciliacion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		for rec in self:
			worksheet = workbook.add_worksheet(rec.name)
			worksheet.set_tab_color('blue')

			worksheet.write(0, 0, 'DIARIO', formats['especial1'])
			worksheet.write(0, 1, rec.journal_id.name, formats['especial1'])
			worksheet.write(1, 0, 'FECHA', formats['especial1'])
			worksheet.write(1, 1, rec.date, formats['reverse_dateformat'])
			worksheet.write(2, 0, 'FECHA CONTABLE', formats['especial1'])
			worksheet.write(2, 1, rec.accounting_date if rec.accounting_date else '', formats['reverse_dateformat'])
			worksheet.write(3, 0, 'COMPAÑIA', formats['especial1'])
			worksheet.write(3, 1, rec.company_id.name, formats['especial1'])
			worksheet.write(0, 3, 'SALDO INICIAL', formats['especial1'])
			worksheet.write(0, 4, rec.balance_start, formats['numberdos'])
			worksheet.write(1, 3, 'SALDO FINAL', formats['especial1'])
			worksheet.write(1, 4, rec.balance_end_real, formats['numberdos'])

			HEADERS = ['FECHA', 'DESCRIPCION', 'SOCIO', 'REFERENCIA', 'MEDIO DE PAGO', 'MONEDA', 'IMPORTE', 'NRO OPERACION', 'TIPO', 'ESTADO']
			worksheet = ReportBase.get_headers(worksheet, HEADERS, 5, 0, formats['boldbord'])
			x = 6
			for line in rec.line_ids:
				worksheet.write(x, 0, line.date, formats['reverse_dateformat'])
				worksheet.write(x, 1, line.name, formats['especial1'])
				worksheet.write(x, 2, line.partner_id.name if line.partner_id else '', formats['especial1'])
				worksheet.write(x, 3, line.ref if line.ref else '', formats['especial1'])
				worksheet.write(x, 4, line.catalog_payment_id.name if line.catalog_payment_id else '', formats['especial1'])
				worksheet.write(x, 5, line.statement_id.currency_id.name if line.statement_id.currency_id else '', formats['especial1'])
				worksheet.write(x, 6, line.amount, formats['especial1'])
				worksheet.write(x, 7, line.order_id.name if line.order_id else '', formats['especial1'])
				worksheet.write(x, 8, line.type if line.type else '', formats['especial1'])
				worksheet.write(x, 9, 'CONCILIADO' if line.journal_entry_ids else 'NO CONCILIADO', formats['especial1'])
				x += 1

			widths = [14] * 10
			worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'Conciliacion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Conciliacion Bancaria.xlsx', base64.encodestring(b''.join(f.readlines())))