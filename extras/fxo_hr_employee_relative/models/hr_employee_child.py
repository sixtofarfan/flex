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
	age = fields.Integer(string='Edad', compute='get_age')
	limit_date = fields.Date(string='Fecha Limite', compute=None)
	gender = fields.Selection([
		('male', 'Hombre'),
		('female', 'Mujer'),
	], string='Genero', default='male', required=True)
	proof_studies = fields.Binary(string='Constancia de Estudios')
	family_bond_id = fields.Many2one('hr.family.bond', string='Parentesco')
	company_id = fields.Many2one('res.company', string='Company', index=True,
								 default=lambda self: self.env.user.company_id.id)

	@api.depends('birth_date')
	def get_age(self):
		for rec in self:
			if rec.birth_date:
				today = fields.Date.today()
				born = rec.birth_date
				rec.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
			else:
				rec.age = 0

	@api.onchange('birth_date')
	def get_limit_date(self):
		for rec in self:
			if rec.birth_date:
				rec.limit_date = date(rec.birth_date.year + 18, rec.birth_date.month, rec.birth_date.day)
			else:
				rec.limit_date = None
	
	@api.model
	def create(self, vals):
		res = super(HrEmployeeChild, self).create(vals)
		res.get_limit_date()
		return res

	@api.onchange('names', 'last_name', 'm_last_name')
	def verify_name(self):
		self.name = '%s %s %s' % ((self.names or '').strip(), (self.last_name or '').strip(), (self.m_last_name or '').strip())

	def name_get(self):
		result = []
		for rec in self:
			name = '%s %s %s' % ((rec.names or '').strip(), (rec.last_name or '').strip(), (rec.m_last_name or '').strip())
			result.append([rec.id, name])
		return result