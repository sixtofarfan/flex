# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	massive_advance_rule = fields.Many2one('hr.salary.rule', string='R. S. para Adelantos Quincenales')
	massive_advance_type = fields.Many2one('hr.advance.type', string='Tipo de Adelanto para Adelantos Quincenales')
	massive_advance_percent = fields.Float(string='Porcentaje Aplicable')

	def verify_massive_advance_values(self):
		if not self.massive_advance_rule or\
		   not self.massive_advance_type or\
		   not self.massive_advance_percent:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Adelantos del Menu de Parametros Principales')