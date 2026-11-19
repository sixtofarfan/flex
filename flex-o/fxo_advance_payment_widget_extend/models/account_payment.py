# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	import_number = fields.Char(string='Numero de Importacion')

	def post(self):
		res = super(AccountPayment, self).post()
		for rec in self:
			if rec.move_line_ids:
				for line in rec.move_line_ids:
					line.import_number = rec.import_number

		return res