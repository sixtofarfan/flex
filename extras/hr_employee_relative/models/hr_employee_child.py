# -*- encoding: utf-8 -*-
from odoo import fields, models, api
from datetime import *

class HrEmployeeChild(models.Model):
	_name = 'hr.employee.child'
	_description = 'Hr Employee Child'

	name = fields.Char(string='Nombre')
	names = fields.Char(string='Nombres')
	last_name = fields.Char(string='Apellido Paterno')
	m_last_name = fields.Char(string='Apellido Materno')
	employee_id = fields.Many2one('hr.employee', string='Empleado', ondelete='cascade', required=True)
	birth_date = fields.Date(string='Fecha de Nacimiento', required=True)
	limit_date = fields.Date(string='Fecha Limite', compute='get_limit_date')
	gender = fields.Selection([
		('male', 'Hombre'),
		('female', 'Mujer'),
	], string='Genero', default='male', required=True)
	proof_studies = fields.Binay(string='Constancia de Estudios')

	@api.depends('birth_date')
	def get_limit_date(self):
		for rec in self:
			rec.limit_date = date(rec.birth_date.year + 18, rec.birth_date.month, rec.birth_date.day)

	@api.onchange('names', 'last_name', 'm_last_name')
	def verify_name(self):
		self.name = '%s %s %s' % ((self.names or '').strip(), (self.last_name or '').strip(), (self.m_last_name or '').strip())

	def name_get(self):
		result = []
		for rec in self:
			name = '%s %s %s' % ((rec.names or '').strip(), (rec.last_name or '').strip(), (rec.m_last_name or '').strip())
			result.append([rec.id, name])
		return result