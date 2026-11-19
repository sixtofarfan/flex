# -*- coding:utf-8 -*-

from odoo import api, fields, models

class HrAdvanceInput(models.Model):
	_name = 'hr.advance.input'
	_description = 'Hr Advance Input'

	advance_id = fields.Many2one('hr.advance', ondelete='cascade')
	input_type_id = fields.Many2one('hr.payslip.input.type', string='Input')
	amount_type = fields.Selection([
		('income', 'Ingreso'),
		('discount', 'Descuento'),
	], default='income', string='Tipo de Concepto')
	amount = fields.Float(string='Monto')

	@api.onchange('struct_id')
	def _onchange_struct_id(self):
		return {'domain': {'input_type_id': ['|', ('id', 'in', self.advance_id.struct_id.input_line_type_ids.ids), ('struct_ids', '=', False)]}}