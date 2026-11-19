# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def generate_advance(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.verify_massive_advance_values()
		ReportBase = self.env['report.base']
		for record in self:
			AdvanceRule = record.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.massive_advance_rule)
			amount = ReportBase.custom_round(AdvanceRule.total * (MainParameter.massive_advance_percent/100), 2)
			self.env['hr.advance'].create({
				'employee_id': record.employee_id.id,
				'amount': amount,
				'initial_amount': amount,
				'date': fields.Datetime.now(),
				'discount_date': date(record.date_from.year, record.date_from.month, 15),
				'advance_type_id': MainParameter.massive_advance_type.id,
				'struct_id': record.struct_id.id,
			})._get_name()