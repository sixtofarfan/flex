# -*- coding:utf-8 -*-
from odoo import api, fields, models

class MainParameterWizard(models.TransientModel):
	_name = 'main.parameter.wizard'

	company_ids = fields.Many2many('res.company', string='Compañias')

	def generate_parameters(self):
		MainParameter = self.env['main.parameter'].browse(self._context.get('active_id'))
		for company in self.company_ids:
			MainParameter.copy(default={'company_id': company.id})