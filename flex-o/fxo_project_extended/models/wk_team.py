# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class WkTeam(models.Model):
	_inherit = 'wk.team'

	is_design_team = fields.Boolean(string='Equipo de Diseño', default=False)