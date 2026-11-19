# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMove(models.Model):
	_inherit = 'stock.move'

	def get_stock_move_wizard(self):
		return {
			'name': 'Importar Lineas',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.move.wizard',
			'views': [(False, 'form')],
			'context': self._context,
			'target': 'new',
		}