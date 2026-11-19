# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class EinvoiceCatalog09Internal(models.Model):
	_name = 'einvoice.catalog.09.internal'
	_description = 'Einvoice Catalog 09 Internal'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Nombre')