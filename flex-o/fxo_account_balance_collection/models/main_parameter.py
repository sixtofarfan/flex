# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	use_invoice_period = fields.Boolean(string='Usar periodos en Facturas', default=False)