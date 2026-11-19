# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def update_amount_residual_signed(self):
		if not self.env.user.has_group('fxo_account_amount_residual_error.group_update_amount_residual_signed'):
			raise UserError('Usted no tiene autorizacion para Actualizar Consistencia de Saldo de Facturas')
		return {
			'name': 'Actualizar Importe Adeudado',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.wizard',
			'views': [(False, 'form')],
			'context': self._context,
			'target': 'new'
		}