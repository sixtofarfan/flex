# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = 'account.move'

	status_partner_id = fields.Many2one('base.element', string="Estado Cliente", domain=[('table_id.code', '=', 'STATUS.PARTNER')])

