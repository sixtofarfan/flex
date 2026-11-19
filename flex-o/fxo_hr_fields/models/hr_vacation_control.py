# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class HrVacationControlLine(models.Model):
	_inherit = 'hr.vacation.control.line'
	_description = 'Vacation Control Line'

	stored_days = fields.Integer(string='Dias Acumulados')
	total = fields.Integer(string='Total', compute='get_total_control_line')

	def get_total_control_line(self):
		for rec in self:
			rec.total = rec.vacation_balance + rec.stored_days - rec.expended_days