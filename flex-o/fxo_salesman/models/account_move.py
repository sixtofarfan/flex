# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	salesman_id = fields.Many2one('res.partner', string='Codigo Vendedor')

	@api.onchange('partner_id')
	def get_salesman_by_partner(self):
		for rec in self:
			if rec.partner_id and rec.partner_id.salesman_id:
				rec.salesman_id = rec.partner_id.salesman_id.id

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	salesman_id = fields.Many2one('res.partner', related='move_id.salesman_id', string='Codigo Vendedor')