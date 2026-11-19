# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProjectLog(models.Model):
	_name = 'project.log'
	_description = 'Project Log'

	name = fields.Char(string='Nombre')
	codigo = fields.Char(string='Codigo')
	partner_id = fields.Many2one('res.partner', string='Cliente del Pedido')