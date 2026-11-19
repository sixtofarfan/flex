# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_get_moves(self):
		if self.env.user.partner_id:
			Moves = self.env['account.move'].search([('partner_id', '=', 184)])
		return {
			'name': 'Mis Documentos',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
			'views': [
				(False, 'tree'),
				(False, 'form'),
			],
			'context': self._context,
			'domain': [('id', 'in', Moves.ids)],
		}