# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	employee_wage = fields.Float(string='Salario Contrato')

class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'

	def compute_sheet(self):
		res = super(HrPayslipEmployees, self).compute_sheet()
		PayslipRun = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
		for slip in PayslipRun.slip_ids:
			slip.employee_wage = slip.contract_id.wage
		return res