# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	internal_type_id = fields.Many2one('einvoice.catalog.09.internal', string='Tipo Interno')