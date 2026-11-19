# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class res_partner(models.Model):
	_inherit = 'res.partner'

	analytic_group_id = fields.Many2one('account.analytic.group','Grupo de Cuenta Analitica por Defecto (Proyectos)',related="state_id.analytic_group_id")