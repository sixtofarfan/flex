# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	partner_street_destination = fields.Many2one('res.partner', string='Direccion')

	def _prepare_account_move_line(self, move):
		res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
		if self.partner_street_destination:
			res['partner_street_destination'] = self.partner_street_destination.id
		return res