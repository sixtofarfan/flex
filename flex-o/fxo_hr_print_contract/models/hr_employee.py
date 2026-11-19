# -*- encoding: utf-8 -*-
from odoo import fields, models, api

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	emp_date_start = fields.Date(string='Fecha de Ingreso')