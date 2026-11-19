# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrFixedInputs(models.Model):
	_name = 'hr.fixed.inputs'
	_description = 'Hr Fixed Inputs'

	name = fields.Char(compute='get_name')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	fixed_line_ids = fields.One2many('hr.fixed.inputs.line', 'fixed_input_id')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

	def get_name(self):
		for rec in self:
			rec.name = 'Conceptos Fijos ' + rec.employee_id.name

	@api.constrains('employee_id')
	def verify_duplicated_employee(self):
		for rec in self:
			Fixed_Inputs = self.env['hr.fixed.inputs'].search([('id', '!=', rec.id)])
			if rec.employee_id in Fixed_Inputs.mapped('employee_id'):
				raise UserError('No puede existir dos registros de Conceptos Fijos para un mismo Empleado')

class HrFixedInputsLine(models.Model):
	_name = 'hr.fixed.inputs.line'
	_description = 'Hr Fixed Inputs Line'

	fixed_input_id = fields.Many2one('hr.fixed.inputs', ondelete='cascade')
	input_id = fields.Many2one('hr.payslip.input.type', string='Input')
	amount = fields.Float(string='Monto')