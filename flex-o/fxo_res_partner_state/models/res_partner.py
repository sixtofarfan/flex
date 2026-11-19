# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResPartner(models.Model):
	_inherit = 'res.partner'

	status_id = fields.Many2one(comodel_name='catalog.100', string='Estado Cliente', readonly=False)
