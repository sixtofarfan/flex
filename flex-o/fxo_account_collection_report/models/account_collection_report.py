# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountCollectionReport(models.Model):
	_name = 'account.collection.report'
	_description = 'Account Collection Report'

	status_id = fields.Many2one('catalog.100', string='Estado Cliente')
	currency_id = fields.Many2one('res.currency', string='Moneda')
	wizard_record = fields.Boolean(default=True)

	def generate_collection_report(self):
		import io, base64
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Informe_Cobranzas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		domain = [
			('type', '=', 'out_invoice'),
			('state', '=', 'posted'),
			('collection_id', '!=', None),
		]
		if self.status_id:
			domain.append(('partner_id.status_id', '=', self.status_id.id))
		if self.currency_id:
			domain.append(('currency_id', '=', self.currency_id.id))
		symbol = self.currency_id.symbol if self.currency_id else ''
		Moves = self.env['account.move'].search(domain)
		Periods = self.env['account.period'].search([
			('is_opening_close', '=', False),
		])
		Collectors = self.env['account.move'].read_group(domain, ['collection_id'], ['collection_id'])
		Collector_names = list(map(lambda col: self.env['res.users'].browse(col['collection_id'][0]).name, Collectors))
		HEADERS = ['Periodo', 'Facturado', 'CxC'] + Collector_names
		Catalog100 = self.env['catalog.100'].search([]) if not self.status_id else list(self.status_id)
		for status in Catalog100:
			worksheet = workbook.add_worksheet(status.name)
			worksheet.set_tab_color('blue')
			worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])

			x = 1
			totals = []
			for period in Periods:
				row = []
				worksheet.write(x, 0, period.name, formats['especial1'])
				filtered_moves = Moves.filtered(lambda m: m.invoice_period_id == period and m.partner_id.status_id == status)
				amount_total_signed = sum(filtered_moves.mapped('amount_total_signed'))
				amount_collected_signed = amount_total_signed - sum(filtered_moves.mapped('amount_residual_signed'))
				worksheet.write(x, 1, '%s %d' % (symbol, amount_total_signed), formats['numberdos'])
				row.append(amount_total_signed)
				worksheet.write(x, 2, '%s %d' % (symbol, amount_collected_signed), formats['numberdos'])
				row.append(amount_collected_signed)
				y = 3
				for col in Collectors:
					collection_moves = filtered_moves.filtered(lambda line: line.collection_id.id == col['collection_id'][0])
					collection_total_signed = sum(collection_moves.mapped('amount_total_signed'))
					collection_collected_signed = collection_total_signed - sum(collection_moves.mapped('amount_residual_signed'))
					worksheet.write(x, y, '%s %d' % (symbol, collection_collected_signed), formats['numberdos'])
					row.append(collection_collected_signed)
					y += 1
				x += 1
				totals.append(row)
			zipped = zip(*totals)
			y = 1
			for row in zipped:
				worksheet.write(x, y, '%s %d' % (symbol, sum(list(row))), formats['numbertotal'])
				y += 1

			widths = [20, 14, 14] + [30] * len(Collector_names)
			worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(route + 'Informe_Cobranzas.xlsx', 'rb')
		return self.env['popup.it'].get_file(
			'Informe Cobranzas %s.xlsx' % ('por estado ' + self.status_id.name if self.status_id else ''), 
			base64.encodestring(b''.join(f.readlines()))
		)