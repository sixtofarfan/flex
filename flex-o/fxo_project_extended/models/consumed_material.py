# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ConsumedMaterial(models.Model):
	_inherit = 'consumed.material'

	serie = fields.Char(string='Serie')
	date_consumed = fields.Date(string='Fecha Consumo')
	partner_id = fields.Many2one(string='Socio')