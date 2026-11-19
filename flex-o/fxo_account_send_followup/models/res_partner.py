# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	special_client = fields.Boolean(string='Cliente Especial', help="A Clientes especiales no enviará en automático la carta de seguimiento de cobranza", default=False)
