from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64

class AccountBill(models.Model):
	_inherit = 'account.bill'

	order_id = fields.Many2one('sale.order', string='Routing Order')
	internal_ref = fields.Char(related='order_id.internal_ref', string='Referencia Interna')
	interest = fields.Float(string='Interes', compute='get_interest')
	interest_time = fields.Integer(string='Tiempo')
	freight_interest = fields.Float(string='Portes')
	igv = fields.Float(string='IGV', compute='get_igv')
	capital = fields.Float(string='Capital')
	bill_amount_total = fields.Float(compute='get_advanced_amount')
	bill_amount_total_signed = fields.Float(compute='compute_total_signed')

	@api.depends('bill_amount_total','exchange_rate')
	def compute_total_signed(self):
		for rec in self:
			if rec.bill_currency_id != rec.env.company.currency_id.name:
				rec.bill_amount_total_signed = rec.bill_amount_total * rec.exchange_rate
			else:
				rec.bill_amount_total_signed = rec.bill_amount_total

	@api.depends('interest', 'freight_interest')
	def get_igv(self):
		for rec in self:
			rec.igv = (rec.interest + rec.freight_interest) * 0.18

	@api.depends('bill_amount_total', 'bill_form_id.interest_percent', 'bill_form_id.type_time', 'interest_time')
	def get_interest(self):
		ReportBase = self.env['report.base']
		for rec in self:
			if rec.bill_form_id.type_time == 'yearly':
				rec.interest = ReportBase.custom_round(((1 + rec.bill_form_id.interest_percent/100) ** (rec.interest_time/360) - 1) * rec.capital, 2)
			else:
				rec.interest = ReportBase.custom_round(((1 + rec.bill_form_id.interest_percent/100) ** (rec.interest_time/30) - 1) * rec.capital, 2)

	@api.depends('capital', 'interest', 'bill_form_id.type_freight', 'freight_interest', 'igv', 'bill_form_id.bills_qty')
	def get_advanced_amount(self):
		self.get_interest()
		for rec in self:
			rec.bill_amount_total = rec.capital + rec.igv + rec.interest + rec.freight_interest

	def get_general_bill_report(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'General.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet('Reporte General de Letras')
		worksheet.set_tab_color('blue')
		HEADERS = [
			'Cod. Cliente', 'Nombre Cliente', 'Año', 'Nro. Letra', 'Reno', 'Emision', 'Vencimiento',
			'Referencia', 'Moneda', 'Dolares', 'Soles', 'Aceptacion', 'Envio Bco.', 'Banco', 'Nombre Banco',
			'Abono', 'Cancelacion', 'Nro. Unico'
		]
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x = 1
		for rec in self:
			worksheet.write(x, 0, rec.acceptor_id.vat if rec.acceptor_id else '', formats['especial1'])
			worksheet.write(x, 1, rec.acceptor_id.name if rec.acceptor_id else '', formats['especial1'])
			worksheet.write(x, 2, rec.bill_date_issue.year if rec.bill_date_issue else '', formats['especial1'])
			worksheet.write(x, 3, rec.bill_number if rec.bill_number else '', formats['especial1'])
			worksheet.write(x, 4, rec.renew_date if rec.state_of_bill == 'renewed' and rec.renew_date else '', formats['reverse_dateformat'])
			worksheet.write(x, 5, rec.bill_date_issue if rec.bill_date_issue else '', formats['reverse_dateformat'])
			worksheet.write(x, 6, rec.bill_date_due if rec.bill_date_due else '', formats['reverse_dateformat'])
			worksheet.write(x, 7, rec.order_id.name if rec.order_id else '', formats['especial1'])
			worksheet.write(x, 8, rec.bill_currency_id.name if rec.bill_currency_id else '', formats['especial1'])
			worksheet.write(x, 9, rec.bill_amount_total_signed if rec.bill_currency_id.name == 'USD' else 0, formats['numberdos'])
			worksheet.write(x, 10, rec.bill_amount_total_signed if rec.bill_currency_id.name == 'PEN' else 0, formats['numberdos'])
			worksheet.write(x, 11, rec.bill_form_id.aceptation_date if rec.bill_form_id.aceptation_date else '', formats['reverse_dateformat'])
			worksheet.write(x, 12, rec.send_form_id.send_date if rec.send_form_id.send_date else '', formats['reverse_dateformat'])
			worksheet.write(x, 13, rec.send_form_id.journal_id.code if rec.send_form_id.journal_id else '', formats['especial1'])
			worksheet.write(x, 14, rec.send_form_id.journal_id.name if rec.send_form_id.journal_id else '', formats['especial1'])
			worksheet.write(x, 15, rec.bank_disbursement_id.disbursement_date if rec.bank_disbursement_id else '', formats['reverse_dateformat'])
			worksheet.write(x, 16, rec.payment_date if rec.state_of_bill == 'paid' and rec.payment_date else '', formats['reverse_dateformat'])
			worksheet.write(x, 17, rec.bank_number if rec.bank_number else '', formats['especial1'])

			x += 1

		widths = [14] * 18
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(route + 'General.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte de Letras General.xlsx', base64.encodestring(b''.join(f.readlines())))