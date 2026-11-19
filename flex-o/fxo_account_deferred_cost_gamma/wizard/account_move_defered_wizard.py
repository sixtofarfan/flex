# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMoveDiferedWizard(models.TransientModel):
	_inherit = 'account.move.difered.wizard'

	def get_tmp_values(self, line):
		res = super(AccountMoveDiferedWizard, self).get_tmp_values(line)
		res.update({
			'request_id': line.request_id.id if line.request_id else None,
			'order_id': line.order_id.id if line.order_id else None,
		})
		return res

	def get_tmp_move_values(self, move):
		res = super(AccountMoveDiferedWizard, self).get_tmp_move_values(move)
		res.update({
			'bill_to_numberdocument': move.bill_to_numberdocument.id if move.bill_to_numberdocument else None,
		})
		return res