# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = 'account.move'

	status_partner_id = fields.Many2one('catalog.100', related='partner_id.status_id', string="Est.Cliente")
