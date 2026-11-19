# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def get_batch_detraction_wizard(self):
		return {
			'name': 'Confirmacion',
			'type': 'ir.actions.act_window',
			'res_model': 'detraction.batch.wizard',
			'views': [(self.env.ref('fxo_account_detraction_batch.view_detraction_batch_wizard').id, 'form')],
			'context': self._context,
			'target': 'new',
		}