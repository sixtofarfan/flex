# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def import_fixed_inputs(self):
		log = []
		for rec in self:
			FixedInput = self.env['hr.fixed.inputs'].search([('employee_id', '=', rec.employee_id.id)])
			if FixedInput:
				for line in FixedInput.fixed_line_ids:
					input_line = rec.input_line_ids.filtered(lambda l: l.input_type_id == line.input_id)
					input_line.amount = line.amount
				log.append(rec.employee_id.name)
		if log:
			return self.env['popup.it'].get_message('Se importo conceptos fijos de los siguientes Empleados:\n' + '\n'.join(log))
		else:
			return self.env['popup.it'].get_message('No se importo ningun concepto fijo')