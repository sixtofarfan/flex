# -*- coding: utf-8 -*-

from odoo import api, fields, models

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	def get_wizard(self):
		return {
			'type':'ir.actions.act_window',
			'res_model':'main.parameter.wizard',
			'views':[(False, 'form')],
			'target':'new'
		}