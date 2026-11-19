# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	def get_rule_wizard(self):
		return {
			'name': 'Aumentar Secuencia',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.salary.rule.wizard',
			'views': [(self.env.ref('fxo_hr_rule_sequence.view_hr_salary_rule_wizard_form').id, 'form')],
			'context': self._context,
			'target': 'new'
		}