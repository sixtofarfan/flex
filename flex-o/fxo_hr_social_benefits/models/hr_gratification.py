# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrGratification(models.Model):
	_inherit = 'hr.gratification'

	def get_gratification_sheet(self, workbook, lines, liquidation=False):
		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)
		labor_regime = dict(self.env['hr.contract']._fields['labor_regime'].selection)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('GRATIFICACION')
		worksheet.set_tab_color('blue')

		#### I'm separating this array of headers 'cause i need a dynamic limiter to set the totals at the end of the printing, i will use the HEADER variable to get the lenght and this will be my limiter'
		HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO', 'REGIMEN LABORAL', 'SEGURO', 'MES', 'DIAS']
		if liquidation:
			HEADERS = HEADERS[:5] + ['FECHA DE COMPUTO', 'FECHA DE CESE'] + HEADERS[5:]
		HEADERS_WITH_TOTAL = ['FALTAS', 'SUELDO', 'ASIGNACION FAMILIAR', 'COMISION', 'BONIFICACION', 'PROMEDIO HRS EXTRAS', 'REMUNERACION COMPUTABLE',
			'MONTO POR MES', 'MONTO POR DIA', 'TOTAL FALTAS S/.', 'GRAT. POR MESES', 'GRAT. POR DIAS', 'TOTAL GRAT.', 'BONIFICACION 9%', 'TOTAL A PAGAR', 'TOTAL ADELANTOS']
		worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
		x, y = 1, 0
		totals = [0] * len(HEADERS_WITH_TOTAL)
		limiter = len(HEADERS)
		
		for line in lines:
			worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
			worksheet.write(x, 1, line.last_name or '', formats['especial1'])
			worksheet.write(x, 2, line.m_last_name or '', formats['especial1'])
			worksheet.write(x, 3, line.names or '', formats['especial1'])
			worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
			if liquidation:
				worksheet.write(x, 5, line.compute_date or '', formats['reverse_dateformat'])
				worksheet.write(x, 6, line.cessation_date or '', formats['reverse_dateformat'])
				y = 2
			worksheet.write(x, 5 + y, labor_regime.get(line.labor_regime) or '', formats['especial1'])
			worksheet.write(x, 6 + y, line.social_insurance_id.name or '', formats['especial1'])
			worksheet.write(x, 7 + y, line.months or 0, formats['number'])
			worksheet.write(x, 8 + y, line.days or 0, formats['number'])
			worksheet.write(x, 9 + y, line.lacks or 0, formats['number'])
			worksheet.write(x, 10 + y, line.wage or 0, formats['numberdos'])
			worksheet.write(x, 11 + y, line.household_allowance or 0, formats['numberdos'])
			worksheet.write(x, 12 + y, line.commission or 0, formats['numberdos'])
			worksheet.write(x, 13 + y, line.bonus or 0, formats['numberdos'])
			worksheet.write(x, 14 + y, line.extra_hours or 0, formats['numberdos'])
			worksheet.write(x, 15 + y, line.computable_remuneration or 0, formats['numberdos'])
			worksheet.write(x, 16 + y, line.amount_per_month or 0, formats['numberdos'])
			worksheet.write(x, 17 + y, line.amount_per_day or 0, formats['numberdos'])
			worksheet.write(x, 18 + y, line.amount_per_lack or 0, formats['numberdos'])
			worksheet.write(x, 19 + y, line.grat_per_month or 0, formats['numberdos'])
			worksheet.write(x, 20 + y, line.grat_per_day or 0, formats['numberdos'])
			worksheet.write(x, 21 + y, line.total_grat or 0, formats['numberdos'])
			worksheet.write(x, 22 + y, line.bonus_essalud or 0, formats['numberdos'])
			worksheet.write(x, 23 + y, line.total or 0, formats['numberdos'])
			worksheet.write(x, 24 + y, line.advance_amount or 0, formats['numberdos'])

			totals[0] += line.lacks
			totals[1] += line.wage
			totals[2] += line.household_allowance
			totals[3] += line.commission
			totals[4] += line.bonus
			totals[5] += line.extra_hours
			totals[6] += line.computable_remuneration
			totals[7] += line.amount_per_month
			totals[8] += line.amount_per_day
			totals[9] += line.amount_per_lack
			totals[10] += line.grat_per_month
			totals[11] += line.grat_per_day
			totals[12] += line.total_grat
			totals[13] += line.bonus_essalud
			totals[14] += line.total
			totals[15] += line.advance_amount

			x += 1
		x += 1
		for total in totals:
			worksheet.write(x, limiter, total, formats['numbertotal'])
			limiter += 1

		widths = [14, 12, 12, 10, 10, 10, 8, 5, 5, 8, 8, 13, 11, 16, 13, 16, 9, 9, 12, 11, 11, 8, 19, 10, 13]
		if liquidation:
			widths = widths[:5] + [10, 10] + widths[5:]
		worksheet = ReportBase.resize_cells(worksheet, widths)