# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def compute_wds(self):
		for record in self:
			MainParameter = self.env['hr.main.parameter'].get_main_parameter()
			Holidays = self.env['hr.holidays'].search([('date', '>=', record.date_from),
													   ('date', '<=', record.date_to),
													   ('workday_id', '=', record.contract_id.workday_id.id)])
			record.holidays = len(Holidays)
			if not MainParameter.payslip_working_wd:
				raise UserError('Falta configurar un Worked Day para Dias Laborados en Parametros Principales de Nomina')
			WDLine = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
			Contract = self.env['hr.contract'].get_first_contract(record.employee_id, record.contract_id)
			if Contract.date_start > record.date_from and Contract.date_start <= record.date_to:
				result = record.date_to.day - Contract.date_start.day + 1
				WDLine.number_of_days = result
			else:
				WDLine.number_of_days = MainParameter.payslip_working_wd.days
			WDDiscountLines = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id != MainParameter.payslip_working_wd and 
																				line.wd_type_id.is_discount)
			if WDDiscountLines:
				WDLine.number_of_days -= sum(WDDiscountLines.mapped('number_of_days'))
		return self.env['popup.it'].get_message('Se calculo correctamente')