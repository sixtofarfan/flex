# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
import base64

class HrAdvance(models.Model):
	_inherit = 'hr.advance'

	input_ids = fields.One2many('hr.advance.input', 'advance_id')
	initial_amount = fields.Float()
	struct_id = fields.Many2one('hr.payroll.structure')

	@api.onchange('input_ids', 'amount')
	def amount_by_lines(self):
		for rec in self:
			if rec.initial_amount > 0:
				total_input = 0
				for inp in rec.input_ids:
					if inp.amount_type == 'income':
						total_input += inp.amount
					elif inp.amount_type == 'discount':
						total_input -= inp.amount
				rec.amount = rec.initial_amount + total_input

	def get_advance_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		if any(rec.advance_type_id != MainParameter.massive_advance_type for rec in self):
			raise UserError('Todos los adelantos deben ser del tipo %s' % MainParameter.massive_advance_type.name)
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Adelantos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Adelantos Quincenales")
		worksheet.set_tab_color('blue')

		Incomes = self.env['hr.advance.input'].read_group([('advance_id', 'in', self.ids), ('amount_type', '=', 'income')], ['input_type_id', 'amount'], ['input_type_id'])
		Discounts = self.env['hr.advance.input'].read_group([('advance_id', '=', self.ids), ('amount_type', '=', 'discount')], ['input_type_id', 'amount'], ['input_type_id'])
		Income_names = list(map(lambda inc: self.env['hr.payslip.input.type'].browse(inc['input_type_id'][0]).name, Incomes))
		Discount_names = list(map(lambda inc: self.env['hr.payslip.input.type'].browse(inc['input_type_id'][0]).name, Discounts))
		HEADERS = ['Empleado', 'Fecha Adelanto', 'Fecha Descuento', 'Monto Bruto'] + Income_names + Discount_names + ['Neto a Pagar']
		if len(Income_names) > 0:
			worksheet.merge_range(0, 4, 0, len(Income_names) + 3, 'Ingresos', formats['boldbord'])
		if len(Discount_names) > 0:
			worksheet.merge_range(0, len(Income_names) + 4, 0, len(Income_names) + 3 + len(Discount_names), 'Descuentos', formats['boldbord'])
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 1, 0, formats['boldbord'])

		x = 2
		totals = []
		for adv in self:
			row = []
			worksheet.write(x, 0, adv.employee_id.name if adv.employee_id else '', formats['especial1'])
			worksheet.write(x, 1, adv.date if adv.date else '', formats['dateformat'])
			worksheet.write(x, 2, adv.discount_date if adv.discount_date else '', formats['dateformat'])
			worksheet.write(x, 3, adv.initial_amount or 0, formats['numberdos'])
			row.append(adv.initial_amount)
			y = 4
			for inc in Income_names:
				inp = adv.input_ids.filtered(lambda i: i.input_type_id.name == inc and i.amount_type == 'income')
				worksheet.write(x, y, inp[0].amount if inp else 0, formats['numberdos'])
				row.append(inp[0].amount if inp else 0)
				y += 1
			for dis in Discount_names:
				inp = adv.input_ids.filtered(lambda i: i.input_type_id.name == dis and i.amount_type == 'discount')
				worksheet.write(x, y, inp[0].amount if inp else 0, formats['numberdos'])
				row.append(inp[0].amount if inp else 0)
				y += 1
			worksheet.write(x, y, adv.amount or 0, formats['numberdos'])
			row.append(adv.amount)
			x += 1
			totals.append(row)
		zipped = zip(*totals)
		y = 3
		for row in zipped:
			worksheet.write(x, y, sum(list(row)), formats['numbertotal'])
			y += 1

		widths = [40, 14, 14, 12] + [12] * len(Income_names) + [12] * len(Discount_names) + [12]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'Adelantos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Adelantos Quincenales.xlsx', base64.encodestring(b''.join(f.readlines())))
