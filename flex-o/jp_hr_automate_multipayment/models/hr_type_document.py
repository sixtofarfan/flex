# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrTypeDocument(models.Model):
	_inherit = 'hr.type.document'

	bbva_code = fields.Char()
	bcp_code = fields.Char()
	interbank_code = fields.Char()