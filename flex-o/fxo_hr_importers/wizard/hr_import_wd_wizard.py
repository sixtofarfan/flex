# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWdWizard(models.TransientModel):
	_inherit = 'hr.import.wd.wizard'

	option = fields.Selection(selection_add=[('wd_row', 'Worked Days en Columnas')])

	def get_template(self):
		if self.option == 'wd':
			return self.get_wd_template()
		elif self.option == 'wd_row':
			return self.get_wd_row_template()
		else:
			return self.get_input_template()

	def import_template(self):
		if self.option == 'wd':
			return self.import_wd_template()
		elif self.option == 'wd_row':
			return self.import_wd_row_template()
		else:
			return self.import_input_template()

	def get_wd_row_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Worked Days.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('WD')
		worksheet.set_tab_color('blue')
		Codes = self.env['hr.payslip.worked_days.type'].search([]).mapped('code')
		worksheet.merge_range(0, 0, 1, 0, 'EMPLEADO', formats['boldbord'])
		y = 1
		for code in Codes:
			worksheet.merge_range(0, y, 0, y + 1, code, formats['boldbord'])
			worksheet.write(1, y, 'NRO DIAS', formats['boldbord'])
			worksheet.write(1, y + 1, 'NRO HORAS', formats['boldbord'])
			y += 2
		worksheet.write(2, 0, '45653672', formats['especial1'])
		for i in range(1, y):
			if i % 2 == 0:
				worksheet.write(2, i, '0:00', formats['hourformat'])
			else:
				worksheet.write(2, i, 0, formats['especial1'])
		widths = (1 + len(Codes) * 2) * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Plantilla Worked Days.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Worked Days.xlsx', base64.encodestring(b''.join(f.readlines())))

	def import_wd_row_template(self):
		if not self.file:
			raise UserError('Es necesario adjuntar un archivo para la importacion')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_WD.xlsx'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		sheet = wb.sheet_by_index(0)
		Codes = self.env['hr.payslip.worked_days.type'].search([]).mapped('code')
		ncols = (1 + len(Codes) * 2)
		if sheet.ncols != ncols:
			raise UserError('El archivo de importacion debe tener %d columnas' % ncols)
		Payslips = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
		for i in range(1, sheet.nrows):
			Payslip = Payslips.filtered(lambda p: p.employee_id.identification_id == self.parse_xls_float(sheet.cell_value(i, 0)))
			if Payslip:
				for j in range(1, len(Codes) * 2):
					if j % 2 == 0:
						WD = Payslip.worked_days_line_ids.filtered(lambda wd: wd.code == sheet.cell_value(0, j - 1))
						if WD:
							hour = sheet.cell_value(i, j)
							if type(hour) == float:
								hour = int(hour * 24 * 3600)
								hour = time(hour//3600, (hour % 3600)//60, hour % 60)
								WD.number_of_hours = hour.hour + hour.minute/60
					else:
						WD = Payslip.worked_days_line_ids.filtered(lambda wd: wd.code == sheet.cell_value(0, j))
						if WD:
							WD.number_of_days = sheet.cell_value(i, j)

		return self.env['popup.it'].get_message('Se importaron todos los worked days satisfactoriamente')