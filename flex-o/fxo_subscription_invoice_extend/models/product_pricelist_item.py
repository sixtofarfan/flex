# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductPricelistItem(models.Model):
	_inherit = 'product.pricelist.item'

	discount_extra = fields.Float(string='Descuento Extra')
	default_months = fields.Integer(string='Meses por defecto', help='Meses por defecto que se utilizaran para el calculo de descuentos en suscripciones')

	@api.constrains('discount_extra', 'default_months')
	def verify_default_months(self):
		for rec in self:
			if rec.discount_extra and rec.default_months <= 0:
				raise UserError('Es necesario colocar un valor positivo en el campo de "Meses por defecto" si se esta configurando un descuento extra')