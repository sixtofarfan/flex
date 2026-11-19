# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	including_lots = fields.Boolean(string='Incluir lotes, series Fecha de Vencimiento en Guias', default=False)
	including_lots_make = fields.Boolean(string='Incluir lotes, series Fecha de fabricacion, Reg. Sanitario en Guias', default=False)
	including_lots_in_invoice = fields.Boolean(string='Incluir lotes y series en Facturas', default=False)
	including_address_in_invoice = fields.Boolean(string='Incluir direcciones en Facturas', default=False)
	including_custom_lots = fields.Boolean(string='Incluir lotes y series en Facturas por cantidades', default=False)
