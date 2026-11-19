# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	is_life_essalud = fields.Boolean(string='Tiene Essalud Vida', default=False)