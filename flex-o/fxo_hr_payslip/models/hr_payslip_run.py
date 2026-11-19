# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
import base64

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def tab_payroll(self):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Planilla_Tabular.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Planilla Tabular")
		worksheet.set_tab_color('blue')
		self._cr.execute(self._get_tab_payroll_sql())
		data = self._cr.dictfetchall()
		x, y = 0, 5
		limit = len(data[0] if data else 0)
		struct_id = self.slip_ids[0].struct_id.id
		SalaryRules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		names = SalaryRules.mapped('name')
		codes = SalaryRules.mapped('code')
		size = len(codes)
		
		worksheet.write(x, 0, 'NRO IDENTIFICACION', formats['boldbord'])
		worksheet.write(x, 1, 'NOMBRE', formats['boldbord'])
		worksheet.write(x, 2, 'TITULO DE TRABAJO', formats['boldbord'])
		worksheet.write(x, 3, 'INICIO DE LABORES', formats['boldbord'])
		worksheet.write(x, 4, 'AFILIACION', formats['boldbord'])
		
		for name in names:
			worksheet.write(x, y, name, formats['boldbord'])
			y += 1
		x += 1
		table = []
		row = []
		aux_id, limit = '', len(data)
		for c, line in enumerate(data, 1):
			if aux_id != line['employee_id']:
				if len(row) > 0:
					table.append(row)
					x += 1
				row = []
				employee = self.env['hr.employee'].browse(line['employee_id'])
				worksheet.write(x, 0, line['identification_id'] if line['identification_id'] else '', formats['especial1'])
				worksheet.write(x, 1, employee.name if employee.name else '', formats['especial1'])
				worksheet.write(x, 2, employee.job_title if employee.job_title else '', formats['especial1'])
				worksheet.write(x, 3, employee.emp_date_start if employee.emp_date_start else '', formats['dateformat'])
				worksheet.write(x, 4, line['membership'] if line['membership'] else '', formats['especial1'])
				worksheet.write(x, 5, line['sum'] if line['sum'] else 0.0, formats['numberdos'])
				row.append(line['sum'])
				y = 5
				aux_id = line['employee_id']
			else:
				y += 1
				worksheet.write(x, y, line['sum'] if line['sum'] else 0.0, formats['numberdos'])
				aux_id = line['employee_id']
				row.append(line['sum'])
				if c == limit:
					table.append(row)
					x += 1

		zipped_table = zip(*table)
		y = 5
		for row in zipped_table:
			worksheet.write(x, y, sum(list(row)), formats['numbertotal'])
			y += 1
		widths = [18, 40, 22, 12, 16] + size * [19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Planilla_Tabular.xlsx', 'rb')
		return self.env['popup.it'].get_file('Planilla %s.xlsx' % self.name, base64.encodestring(b''.join(f.readlines())))