# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'
	
	type_operation = fields.Many2one('type.operation', string='Type of Operation')
	type_good_service = fields.Many2one('einvoice.catalog.54', string='Goods and Services')
	detraction_bool = fields.Boolean(default=False)

	@api.onchange('type_operation', 'type_good_service')
	def check_detraction_bool(self):
		for record in self:
			record.detraction_bool = False if not record.type_operation and not record.type_good_service else True

	@api.onchange('bank_ids')
	def get_is_detraction_in_banks(self):
		self.bank_ids.get_is_detraction()