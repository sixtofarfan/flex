# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def import_fixed_inputs_by_lot(self):
		return self.slip_ids.import_fixed_inputs()

	def update_wage(self):
		for slip in self.slip_ids:
			slip.employee_wage = slip.contract_id.wage