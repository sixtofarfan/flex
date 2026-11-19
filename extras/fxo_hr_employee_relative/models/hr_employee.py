# -*- encoding: utf-8 -*-
from odoo import fields, models, api

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	custom_child_ids = fields.One2many('hr.employee.child', 'employee_id')
	men = fields.Integer(compute='get_child_number')
	women = fields.Integer(compute='get_child_number')
	child_count = fields.Integer(string='Numero de Hijos', compute='get_child_count')

	@api.depends('men', 'women')
	def get_child_count(self):
		for rec in self:
			rec.child_count = rec.men + rec.women

	def get_child_number(self):
		today = fields.Date.today()
		for rec in self:
			if rec.custom_child_ids:
				rec.men = len(rec.custom_child_ids.filtered(lambda l: l.gender == 'male' and l.age < 18 and not l.proof_studies))
				rec.women = len(rec.custom_child_ids.filtered(lambda l: l.gender == 'female' and l.age < 18 and not l.proof_studies))
			else:
				rec.men = 0
				rec.women = 0
	
	def get_child_view(self):
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.employee.child",
			"views": [
				(False, 'tree'),
				(False, 'form'),
			],
			"domain": [['id', 'in', self.custom_child_ids.ids]],
			"context": {'default_employee_id': self.id},
			"name": "Parientes",
		}