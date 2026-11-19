# -*- coding:utf-8 -*-
from odoo import api, fields, models

class ResPartner(models.Model):
	_inherit = 'res.partner'

	client_representative_id = fields.Many2one('res.partner', string='Representante del Cliente')