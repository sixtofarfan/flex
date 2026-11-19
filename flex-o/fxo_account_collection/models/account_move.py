# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	collection_number = fields.Char(string='Numero de Recaudacion')
	collection_date = fields.Date(string='Fecha de Recaudacion')