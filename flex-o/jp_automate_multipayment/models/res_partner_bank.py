# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	@api.onchange('type_of_account')
	def get_is_detraction(self):
		for rec in self:
			if rec.type_of_account == '2':
				rec.is_detraction_account = True
			else:
				rec.is_detraction_account = False