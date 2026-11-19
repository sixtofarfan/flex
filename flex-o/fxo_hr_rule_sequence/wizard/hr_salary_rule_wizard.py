# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRuleWizard(models.TransientModel):
	_name = 'hr.salary.rule.wizard'

	name = fields.Char()
	sequence = fields.Integer(string='Aumentar en')

	def add_sequence(self):
		for record in self.env['hr.salary.rule'].browse(self._context.get('active_ids')):
			record.sequence += self.sequence