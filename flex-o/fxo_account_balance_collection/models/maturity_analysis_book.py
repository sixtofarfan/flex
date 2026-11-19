# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MaturityAnalysisBook(models.Model):
	_inherit = 'maturity.analysis.book'

	collection = fields.Char(string='Cobrador')
	invoice_user_id = fields.Char(string='Invoice User')
	invoice_expo_user_id = fields.Char(string='Expo User')
	invoice_period = fields.Char(string='Periodo de Facturacion')