# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class res_country_state(models.Model):
	_inherit = 'res.country.state'

	analytic_group_id = fields.Many2one('account.analytic.group','Grupo de Cuenta Analitica por Defecto (Proyectos)')