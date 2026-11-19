# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockQuant(models.Model):
	_inherit = 'stock.quant'

	life_date = fields.Datetime(related='lot_id.life_date')