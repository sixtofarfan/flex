# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDaysType(models.Model):
	_inherit = 'hr.payslip.worked_days.type'

	is_discount = fields.Boolean(string='Es un Descuento', default=False)