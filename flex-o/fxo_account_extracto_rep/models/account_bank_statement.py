# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def generate_excel(self):
		import io, base64
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		dir = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

		if not dir:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(dir +'Extractos_Bancarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('EXTRACTOS BANCARIOS')
		worksheet.set_tab_color('blue')
		worksheet.write(0, 0, self.env.company.name ,formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, 'CONCILIACION BANCARIA AL: {0}'.format(self.date), formats['especial2'])

		worksheet.write(3, 0, 'BANCO:', formats['especial2'])
		worksheet.write(3, 1, self.journal_id.name, formats['especial4'])
		worksheet.write(3, 2, 'CTA:', formats['especial2'])
		worksheet.write(3, 3, self.journal_id.bank_account_id.acc_number, formats['especial4'])
		worksheet.write(3, 4, 'MONEDA:', formats['especial2'])
		worksheet.write(3, 5, 'DOLARES' if self.journal_id.currency_id else 'SOLES', formats['especial4'])

		worksheet.write(5, 0, 'TOTAL ABONO:', formats['especial2'])
		worksheet.write(5, 1, self.balance_start, formats['numberdosespecial'])

		worksheet.write(6, 0, 'TOTAL CARGO:', formats['especial2'])
		worksheet.write(6, 1, self.balance_end, formats['numberdosespecial'])
		worksheet.write(7, 1, self.balance_start - self.balance_end, formats['numberdosespecial'])

		HEADERS = ['FECHA', 'DESCRIPCION', 'DOCUMENTO', 'IMPORTE']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 9, 0, formats['boldbord'])

		x = 10
		for line in self.line_ids:
			worksheet.write(x, 0, line.date if line.date else '', formats['dateformat'])
			worksheet.write(x, 1, line.name if line.name else '', formats['especial1'])
			worksheet.write(x, 2, line.ref if line.ref else '', formats['especial1'])
			worksheet.write(x, 3, line.amount if line.amount else '', formats['numberdos'])
			x += 1

		widths = [25, 50, 25, 20]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()

		f = open(dir +'Extractos_Bancarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('Extractos Bancarios {0}.xlsx'.format(self.date), base64.encodestring(b''.join(f.readlines())))