# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDays(models.Model):
	_inherit = 'hr.payslip.worked_days'

	name = fields.Char(store=True)