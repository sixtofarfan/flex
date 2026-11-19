# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def generate_massive_advance(self):
		if not self.env.user.has_group('fxo_hr_massive_advances.group_hr_massive_advance'):
			raise UserError('Necesita tener acceso al grupo Adelantos Quincenales para realizar esta accion')
		for record in self:
			record.slip_ids.generate_advance()
		return self.env['popup.it'].get_message('Se generaron todos los adelantos exitosamente')