# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	custom_client_journal = fields.Many2one('account.journal', string='Diario Aplicacion Facturas de Clientes')